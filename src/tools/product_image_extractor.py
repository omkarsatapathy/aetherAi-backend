"""Product Image Extractor Tool - Extracts product images from e-commerce URLs.

This tool uses a multi-strategy fallback chain to extract product images:
1. Open Graph (og:image) - 90% success rate
2. Twitter Card (twitter:image) - Backup for social-ready sites
3. JSON-LD Structured Data - Best for e-commerce (multiple images, product info)
4. HTML <img> parsing with product patterns - Fallback
5. Schema.org microdata - Additional structured data
6. Amazon ASIN-based image URL construction - Special handling for Amazon

Supports parallel processing for multiple URLs to minimize latency.
"""
import json
import re
import requests
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..logging_config import get_logger

logger = get_logger("chatbot.tools.product_image_extractor")

# User agents for rotation - More browser-like headers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]


def _get_headers(user_agent_index: int = 0, referer: str = None) -> Dict[str, str]:
    """Get request headers with rotating user agent."""
    headers = {
        'User-Agent': USER_AGENTS[user_agent_index % len(USER_AGENTS)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    if referer:
        headers['Referer'] = referer
    return headers


def _extract_amazon_asin(url: str) -> Optional[str]:
    """
    Extract Amazon ASIN (product ID) from URL.
    ASIN is a 10-character alphanumeric code.
    
    Examples:
    - /dp/B01LYRN9XV/
    - /gp/product/B01LYRN9XV
    - /ASIN/B01LYRN9XV
    """
    # Pattern for /dp/ASIN or /gp/product/ASIN or /ASIN/
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/ASIN/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    return None


def _construct_amazon_image_url(asin: str) -> List[str]:
    """
    Construct multiple possible Amazon product image URLs from ASIN.
    
    Amazon uses various image URL patterns. We return multiple possibilities
    to try in order.
    
    Args:
        asin: Amazon product ASIN
        
    Returns:
        List of possible image URLs to try
    """
    # Amazon image URLs use a different ID (not ASIN), but we can try these patterns
    # that sometimes work or redirect to the correct image
    return [
        # Direct product image API (most reliable)
        f"https://images-na.ssl-images-amazon.com/images/P/{asin}.jpg",
        f"https://images-na.ssl-images-amazon.com/images/P/{asin}._AC_SX679_.jpg",
        f"https://images-na.ssl-images-amazon.com/images/P/{asin}._AC_SL1500_.jpg",
        # EU servers
        f"https://images-eu.ssl-images-amazon.com/images/P/{asin}.jpg",
        f"https://images-eu.ssl-images-amazon.com/images/P/{asin}._AC_SX679_.jpg",
    ]


def _get_amazon_product_info(url: str, validate: bool = False) -> Dict[str, Any]:
    """
    Special handling for Amazon URLs - extract product info from ASIN.
    
    Amazon aggressively blocks scraping, so we try to construct the image URL
    directly from the ASIN when possible.
    """
    result = {
        'image': None,
        'name': None,
        'asin': None
    }
    
    asin = _extract_amazon_asin(url)
    if not asin:
        return result
    
    result['asin'] = asin
    
    # Try to extract product name from URL
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    for i, part in enumerate(path_parts):
        if part and part not in ['dp', 'gp', 'product', asin, ''] and not part.startswith('ref'):
            # This is likely the product name slug
            name = unquote(part).replace('-', ' ').title()
            if len(name) > 5:  # Reasonable name length
                result['name'] = name
                break
    
    # Try each possible image URL pattern
    image_urls = _construct_amazon_image_url(asin)
    
    for img_url in image_urls:
        if not validate:
            # Return the first URL without validation
            result['image'] = img_url
            logger.debug(f"Amazon ASIN extracted: {asin}, Image URL: {result['image']}")
            return result
        
        # Validate the image URL
        if _is_valid_image_url(img_url, timeout=3):
            result['image'] = img_url
            logger.debug(f"Amazon validated image URL: {result['image']}")
            return result
    
    # If no valid URL found, return the first pattern anyway
    if image_urls:
        result['image'] = image_urls[0]
    
    return result


def _is_amazon_url(url: str) -> bool:
    """Check if URL is from Amazon (any region)."""
    amazon_domains = [
        'amazon.com', 'amazon.in', 'amazon.co.uk', 'amazon.de', 
        'amazon.fr', 'amazon.it', 'amazon.es', 'amazon.ca',
        'amazon.com.au', 'amazon.co.jp', 'amazon.com.br', 'amazon.com.mx'
    ]
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in amazon_domains)


def _is_valid_image_url(url: str, timeout: int = 5) -> bool:
    """
    Quick validation of image URL - checks if it's accessible and is an image.
    
    Args:
        url: Image URL to validate
        timeout: Request timeout in seconds
        
    Returns:
        bool: True if valid image, False otherwise
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
        
    try:
        # Use HEAD request first for speed
        headers = {'User-Agent': USER_AGENTS[0]}
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            if any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                return True
        
        # Some servers don't support HEAD, try GET with stream
        if response.status_code in [405, 403, 404]:
            response = requests.get(url, headers=headers, timeout=timeout, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'image/' in content_type:
                    response.close()
                    return True
                # Check magic bytes
                chunk = next(response.iter_content(16), None)
                response.close()
                if chunk:
                    # JPEG, PNG, WebP, GIF signatures
                    if (chunk.startswith(b'\xff\xd8') or  # JPEG
                        chunk.startswith(b'\x89PNG') or   # PNG
                        chunk.startswith(b'RIFF') or      # WebP
                        chunk.startswith(b'GIF')):        # GIF
                        return True
        
        return False
    except Exception as e:
        logger.debug(f"Image validation failed for {url}: {str(e)}")
        return False


def _clean_image_url(url: str, base_url: str) -> Optional[str]:
    """
    Clean and normalize image URL, converting relative to absolute.
    
    Args:
        url: Image URL (may be relative)
        base_url: Base URL of the page
        
    Returns:
        Cleaned absolute URL or None if invalid
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Skip data URIs and invalid protocols
    if url.startswith(('data:', 'javascript:', 'blob:')):
        return None
    
    # Convert relative to absolute
    if not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Skip very small images (likely icons/thumbnails)
    # Common patterns for tracking pixels
    if any(x in url.lower() for x in ['1x1', 'pixel', 'tracking', 'beacon', 'spacer']):
        return None
    
    return url


def _extract_og_image(soup: BeautifulSoup) -> Optional[str]:
    """Extract image from Open Graph meta tags."""
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        return og_image['content']
    
    # Try alternate attribute name
    og_image = soup.find('meta', attrs={'name': 'og:image'})
    if og_image and og_image.get('content'):
        return og_image['content']
    
    return None


def _extract_twitter_image(soup: BeautifulSoup) -> Optional[str]:
    """Extract image from Twitter Card meta tags."""
    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
    if twitter_image and twitter_image.get('content'):
        return twitter_image['content']
    
    twitter_image = soup.find('meta', property='twitter:image')
    if twitter_image and twitter_image.get('content'):
        return twitter_image['content']
    
    return None


def _extract_json_ld_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract product data from JSON-LD structured data.
    
    Returns:
        Dict with 'image', 'images', 'name', 'price', 'description' if found
    """
    result = {
        'image': None,
        'images': [],
        'name': None,
        'price': None,
        'description': None
    }
    
    # Find all JSON-LD scripts
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            
            # Handle @graph structure (common in many sites)
            if isinstance(data, dict) and '@graph' in data:
                data = data['@graph']
            
            # Convert to list for uniform processing
            if isinstance(data, dict):
                data = [data]
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                item_type = item.get('@type', '')
                
                # Check if it's a product-related type
                if isinstance(item_type, list):
                    is_product = any(t in ['Product', 'IndividualProduct', 'ProductModel', 'Offer'] 
                                    for t in item_type)
                else:
                    is_product = item_type in ['Product', 'IndividualProduct', 'ProductModel', 'Offer']
                
                if is_product or 'image' in item:
                    # Extract images
                    if 'image' in item:
                        img = item['image']
                        if isinstance(img, str):
                            result['image'] = img
                            result['images'].append(img)
                        elif isinstance(img, list):
                            result['images'].extend([i if isinstance(i, str) else i.get('url', i.get('@id', '')) 
                                                    for i in img if i])
                            if result['images']:
                                result['image'] = result['images'][0]
                        elif isinstance(img, dict):
                            img_url = img.get('url') or img.get('@id') or img.get('contentUrl')
                            if img_url:
                                result['image'] = img_url
                                result['images'].append(img_url)
                    
                    # Extract product info
                    if 'name' in item and not result['name']:
                        result['name'] = item['name']
                    
                    if 'description' in item and not result['description']:
                        result['description'] = item['description'][:500] if item['description'] else None
                    
                    # Extract price from offers
                    if 'offers' in item:
                        offers = item['offers']
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        if isinstance(offers, dict):
                            price = offers.get('price') or offers.get('lowPrice')
                            currency = offers.get('priceCurrency', 'USD')
                            if price:
                                result['price'] = f"{currency} {price}"
                    
                    # Direct price field
                    if 'price' in item and not result['price']:
                        result['price'] = str(item['price'])
        
        except json.JSONDecodeError:
            logger.debug("Failed to parse JSON-LD script")
            continue
        except Exception as e:
            logger.debug(f"Error processing JSON-LD: {str(e)}")
            continue
    
    # Remove duplicates from images
    result['images'] = list(dict.fromkeys(result['images']))
    
    return result


def _extract_schema_microdata(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """
    Extract product data from Schema.org microdata (itemscope/itemprop).
    
    Returns:
        Dict with 'image', 'images', 'name', 'price' if found
    """
    result = {
        'image': None,
        'images': [],
        'name': None,
        'price': None
    }
    
    # Find product itemscope
    product_scope = soup.find(itemscope=True, itemtype=re.compile(r'schema\.org.*Product', re.I))
    
    if not product_scope:
        # Try finding any element with product-related itemtype
        product_scope = soup.find(attrs={'itemtype': re.compile(r'Product', re.I)})
    
    if product_scope:
        # Find images within product scope
        img_props = product_scope.find_all(itemprop='image')
        for img_prop in img_props:
            if img_prop.name == 'img':
                src = img_prop.get('src') or img_prop.get('data-src')
            elif img_prop.name == 'meta':
                src = img_prop.get('content')
            else:
                src = img_prop.get('href') or img_prop.get('src')
            
            if src:
                cleaned = _clean_image_url(src, base_url)
                if cleaned:
                    result['images'].append(cleaned)
        
        if result['images']:
            result['image'] = result['images'][0]
        
        # Get name
        name_prop = product_scope.find(itemprop='name')
        if name_prop:
            result['name'] = name_prop.get_text(strip=True) or name_prop.get('content')
        
        # Get price
        price_prop = product_scope.find(itemprop='price')
        if price_prop:
            result['price'] = price_prop.get_text(strip=True) or price_prop.get('content')
    
    return result


def _extract_html_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract product images from HTML <img> tags using pattern matching.
    
    Prioritizes images that are likely to be product images based on:
    - Class/ID names containing product-related keywords
    - Image dimensions (larger = more likely main product)
    - Position in DOM (earlier = more likely primary)
    
    Returns:
        List of image URLs, sorted by likelihood of being product images
    """
    images = []
    
    # High-priority selectors for product images
    product_selectors = [
        # Common product image patterns
        {'class': re.compile(r'(product|gallery|hero|main|primary|featured).*image', re.I)},
        {'class': re.compile(r'image.*(product|gallery|hero|main|primary)', re.I)},
        {'id': re.compile(r'(product|gallery|hero|main|primary)', re.I)},
        {'data-testid': re.compile(r'product.*image', re.I)},
        {'alt': re.compile(r'product', re.I)},
    ]
    
    # First, try high-priority selectors
    for selector in product_selectors:
        for img in soup.find_all('img', selector):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                cleaned = _clean_image_url(src, base_url)
                if cleaned and cleaned not in images:
                    images.append(cleaned)
    
    # Then look for images with specific size attributes (large images)
    for img in soup.find_all('img'):
        width = img.get('width', '0')
        height = img.get('height', '0')
        
        try:
            w = int(str(width).replace('px', ''))
            h = int(str(height).replace('px', ''))
            
            # Large images are more likely to be product images
            if w >= 300 or h >= 300:
                src = img.get('src') or img.get('data-src')
                if src:
                    cleaned = _clean_image_url(src, base_url)
                    if cleaned and cleaned not in images:
                        images.append(cleaned)
        except (ValueError, TypeError):
            continue
    
    # Look in common gallery/product containers
    gallery_containers = soup.find_all(['div', 'section', 'figure'], 
                                       class_=re.compile(r'(gallery|product|carousel|slider)', re.I))
    
    for container in gallery_containers:
        for img in container.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                cleaned = _clean_image_url(src, base_url)
                if cleaned and cleaned not in images:
                    images.append(cleaned)
    
    return images[:10]  # Return top 10 most likely product images


def _extract_page_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract page/product title from various sources."""
    # Try Open Graph title first (usually cleaner)
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content']
    
    # Try standard title
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        # Clean up common suffixes
        title = re.split(r'\s*[\|\-–—]\s*(Amazon|eBay|Walmart|Best Buy|Target)', title)[0]
        return title.strip()
    
    # Try h1
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    
    return None


def _fetch_and_extract_single(url: str, validate_image: bool = True) -> Dict[str, Any]:
    """
    Fetch a single URL and extract product image and info.
    
    Uses fallback chain:
    0. Amazon ASIN-based extraction (for Amazon URLs - no scraping needed)
    1. JSON-LD (best for product data)
    2. og:image
    3. twitter:image
    4. Schema.org microdata
    5. HTML img parsing
    
    Args:
        url: Product page URL
        validate_image: Whether to validate image URLs (slower but more reliable)
        
    Returns:
        Dict with product_link, image_link, text (product name/title), and metadata
    """
    result = {
        'product_link': url,
        'image_link': None,
        'text': None,  # Product name/title
        'price': None,
        'description': None,
        'additional_images': [],
        'extraction_source': None,
        'status': 'error',
        'error': None
    }
    
    logger.info(f"Extracting product image from: {url}")
    
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
        if parsed.scheme not in ('http', 'https'):
            result['error'] = f"Invalid URL scheme: {parsed.scheme}"
            return result
    except Exception as e:
        result['error'] = f"Invalid URL: {str(e)}"
        return result
    
    # Strategy 0: Amazon ASIN-based extraction (no scraping needed!)
    # Amazon blocks scraping, so we construct image URL directly from ASIN
    if _is_amazon_url(url):
        amazon_info = _get_amazon_product_info(url, validate=validate_image)
        if amazon_info['image']:
            result['image_link'] = amazon_info['image']
            result['text'] = amazon_info['name'] or f"Amazon Product {amazon_info['asin']}"
            result['extraction_source'] = 'amazon-asin'
            result['status'] = 'success'
            logger.info(f"✓ Successfully extracted Amazon image via ASIN: {amazon_info['asin']}")
            return result
        else:
            logger.warning(f"Amazon ASIN image URL not found, trying web scraping...")
    
    # Fetch page with retries (for non-Amazon or if ASIN method failed)
    response = None
    for attempt in range(3):
        try:
            headers = _get_headers(attempt)
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 200:
                break
            elif response.status_code in (403, 429):
                continue
            else:
                response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            continue
        except Exception as e:
            logger.warning(f"Request error on attempt {attempt + 1}: {str(e)}")
            continue
    
    if not response or response.status_code != 200:
        # If we're on Amazon and scraping failed, return the ASIN-based image anyway
        if _is_amazon_url(url):
            amazon_info = _get_amazon_product_info(url, validate=False)
            if amazon_info['image']:
                result['image_link'] = amazon_info['image']
                result['text'] = amazon_info['name'] or f"Amazon Product {amazon_info['asin']}"
                result['extraction_source'] = 'amazon-asin-fallback'
                result['status'] = 'success'
                logger.info(f"✓ Using Amazon ASIN fallback after scrape failure: {amazon_info['asin']}")
                return result
        
        result['error'] = f"Failed to fetch URL after 3 attempts"
        return result
    
    # Parse HTML
    try:
        encoding = response.encoding or response.apparent_encoding or 'utf-8'
        content = response.content.decode(encoding, errors='replace')
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        result['error'] = f"Failed to parse HTML: {str(e)}"
        return result
    
    # Strategy 1: JSON-LD (best for e-commerce - has product info + images)
    json_ld_data = _extract_json_ld_data(soup)
    if json_ld_data['image']:
        image_url = _clean_image_url(json_ld_data['image'], url)
        if image_url and (not validate_image or _is_valid_image_url(image_url)):
            result['image_link'] = image_url
            result['extraction_source'] = 'json-ld'
            result['text'] = json_ld_data['name']
            result['price'] = json_ld_data['price']
            result['description'] = json_ld_data['description']
            result['additional_images'] = [_clean_image_url(img, url) for img in json_ld_data['images'][1:5] if img]
            logger.debug(f"✓ Found image via JSON-LD: {image_url}")
    
    # Strategy 2: Open Graph
    if not result['image_link']:
        og_image = _extract_og_image(soup)
        if og_image:
            image_url = _clean_image_url(og_image, url)
            if image_url and (not validate_image or _is_valid_image_url(image_url)):
                result['image_link'] = image_url
                result['extraction_source'] = 'og:image'
                logger.debug(f"✓ Found image via og:image: {image_url}")
    
    # Strategy 3: Twitter Card
    if not result['image_link']:
        twitter_image = _extract_twitter_image(soup)
        if twitter_image:
            image_url = _clean_image_url(twitter_image, url)
            if image_url and (not validate_image or _is_valid_image_url(image_url)):
                result['image_link'] = image_url
                result['extraction_source'] = 'twitter:image'
                logger.debug(f"✓ Found image via twitter:image: {image_url}")
    
    # Strategy 4: Schema.org microdata
    if not result['image_link']:
        microdata = _extract_schema_microdata(soup, url)
        if microdata['image']:
            if not validate_image or _is_valid_image_url(microdata['image']):
                result['image_link'] = microdata['image']
                result['extraction_source'] = 'microdata'
                result['text'] = result['text'] or microdata['name']
                result['price'] = result['price'] or microdata['price']
                result['additional_images'] = microdata['images'][1:5]
                logger.debug(f"✓ Found image via microdata: {microdata['image']}")
    
    # Strategy 5: HTML img parsing (fallback)
    if not result['image_link']:
        html_images = _extract_html_images(soup, url)
        for img_url in html_images:
            if not validate_image or _is_valid_image_url(img_url):
                result['image_link'] = img_url
                result['extraction_source'] = 'html-parsing'
                result['additional_images'] = html_images[1:5]
                logger.debug(f"✓ Found image via HTML parsing: {img_url}")
                break
    
    # Get product title/text if not already found
    if not result['text']:
        result['text'] = _extract_page_title(soup)
    
    # Set status
    if result['image_link']:
        result['status'] = 'success'
        logger.info(f"✓ Successfully extracted image from {url} via {result['extraction_source']}")
    else:
        result['status'] = 'no_image_found'
        result['error'] = 'Could not find product image using any extraction method'
        logger.warning(f"✗ No image found for {url}")
    
    return result


def extract_product_image(url: str, validate_image: bool = True) -> str:
    """
    Extract product image and info from a single product page URL.
    
    Uses a multi-strategy fallback chain:
    1. JSON-LD structured data (best for e-commerce)
    2. Open Graph (og:image)
    3. Twitter Card (twitter:image)
    4. Schema.org microdata
    5. HTML <img> parsing with product patterns
    
    Args:
        url: The product page URL to extract image from
        validate_image: Whether to validate that image URLs are accessible (default: True)
        
    Returns:
        JSON string with:
        - product_link: The original URL
        - image_link: Extracted product image URL (or None)
        - text: Product name/title
        - price: Product price if found
        - status: 'success', 'no_image_found', or 'error'
        - extraction_source: Which method found the image
    """
    result = _fetch_and_extract_single(url, validate_image)
    return json.dumps(result, ensure_ascii=False)


def extract_product_images_batch(urls: list[str], validate_images: bool = True, max_workers: int = 10) -> str:
    """
    Extract product images from multiple URLs in parallel for faster processing.
    
    This tool processes multiple product page URLs concurrently to minimize latency.
    Essential for shopping workflows where multiple products need image extraction.
    
    Uses multi-strategy fallback chain for each URL:
    1. JSON-LD structured data
    2. Open Graph (og:image)
    3. Twitter Card (twitter:image)
    4. Schema.org microdata
    5. HTML <img> parsing
    
    Args:
        urls: List of product page URLs to extract images from (max 15)
        validate_images: Whether to validate image URLs are accessible (default: True)
        max_workers: Maximum parallel threads (default: 10)
        
    Returns:
        JSON string with:
        - products: List of extracted product data, each containing:
            - product_link: Original URL
            - image_link: Product image URL
            - text: Product name/title
            - price: Product price if found
            - status: 'success', 'no_image_found', or 'error'
        - success_count: Number of successfully extracted images
        - failed_count: Number of failed extractions
        - total: Total URLs processed
    """
    logger.info(f"Batch extracting product images from {len(urls)} URLs")
    
    # Limit URLs to prevent abuse
    urls = urls[:15]
    
    products = []
    success_count = 0
    failed_count = 0
    
    # Process URLs in parallel
    with ThreadPoolExecutor(max_workers=min(max_workers, len(urls))) as executor:
        # Submit all tasks
        future_to_url = {
            executor.submit(_fetch_and_extract_single, url, validate_images): url 
            for url in urls
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                products.append(result)
                
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Exception extracting from {url}: {str(e)}")
                products.append({
                    'product_link': url,
                    'image_link': None,
                    'text': None,
                    'price': None,
                    'status': 'error',
                    'error': str(e)
                })
                failed_count += 1
    
    # Sort products to maintain original URL order
    url_to_index = {url: i for i, url in enumerate(urls)}
    products.sort(key=lambda p: url_to_index.get(p['product_link'], 999))
    
    logger.info(f"Batch extraction complete: {success_count}/{len(urls)} successful")
    
    return json.dumps({
        'products': products,
        'success_count': success_count,
        'failed_count': failed_count,
        'total': len(urls)
    }, ensure_ascii=False)


# For testing
if __name__ == "__main__":
    # Test with Apple product URL
    test_urls = [
        "https://www.apple.com/shop/product/ftqv3ll/a/Refurbished-iPhone-15-Pro-256GB-Blue-Titanium-Unlocked",
        "https://www.amazon.com/dp/B0CHX1W1XY",
    ]
    
    print("Testing single URL extraction:")
    result = extract_product_image(test_urls[0])
    print(json.dumps(json.loads(result), indent=2))
    
    print("\nTesting batch extraction:")
    result = extract_product_images_batch(test_urls)
    print(json.dumps(json.loads(result), indent=2))

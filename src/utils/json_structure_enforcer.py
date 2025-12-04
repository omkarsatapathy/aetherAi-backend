"""JSON Structure Enforcer - Ensures agents produce valid structured JSON output.

This module provides a post-processing layer that uses an LLM to extract and validate
structured JSON from agent responses that may contain additional text or malformed JSON.
"""
import json
import re
from typing import Dict, Any, Optional
from ..config import Config
from ..logging_config import get_logger

logger = get_logger("chatbot.json_enforcer")


class JSONStructureEnforcer:
    """Enforces structured JSON output from agent responses using LLM post-processing."""

    def __init__(self):
        """Initialize the JSON structure enforcer with Gemini client."""
        try:
            from google import genai
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.model_id = Config.GEMINI_MODEL_ID
            logger.info(f"Initialized JSONStructureEnforcer with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def extract_shopping_preference_json(self, agent_response: str) -> Optional[Dict[str, Any]]:
        """Extract and validate shopping preference questions JSON from agent response.

        Expected JSON structure:
        {
            "agent_message": "Let me help you find the perfect [product]! Answer a few quick questions:",
            "questions": [
                {
                    "question": "What's your budget range?",
                    "options": ["Under $500", "$500-$1000", "$1000-$2000", "Above $2000"]
                },
                ...
            ]
        }

        Args:
            agent_response: Raw response from ShoppingPreferenceAgent

        Returns:
            Validated JSON dict or None if extraction fails
        """
        logger.info("Extracting shopping preference JSON from agent response")

        # First, try to extract JSON directly from the response
        json_data = self._try_direct_json_extraction(agent_response)

        if json_data and self._validate_shopping_preference_structure(json_data):
            logger.info("✅ Successfully extracted valid JSON directly from response")
            return json_data

        # If direct extraction fails, use LLM to structure the output
        logger.info("Direct extraction failed, using LLM to structure output")
        return self._llm_extract_shopping_preference_json(agent_response)

    def extract_product_summary_json(self, agent_response: str) -> Optional[Dict[str, Any]]:
        """Extract and validate product summary JSON from agent response.

        Expected JSON structure:
        {
            "products": [
                {
                    "text_response": "Product description with features and benefits",
                    "image_link": "https://example.com/image.jpg",
                    "product_link": "https://retailer.com/product"
                },
                ...
            ]
        }

        Args:
            agent_response: Raw response from ProductSummarizationAgent

        Returns:
            Validated JSON dict or None if extraction fails
        """
        logger.info("Extracting product summary JSON from agent response")

        # First, try to extract JSON directly from the response
        json_data = self._try_direct_json_extraction(agent_response)

        if json_data and self._validate_product_summary_structure(json_data):
            logger.info("✅ Successfully extracted valid JSON directly from response")
            return json_data

        # If direct extraction fails, use LLM to structure the output
        logger.info("Direct extraction failed, using LLM to structure output")
        return self._llm_extract_product_summary_json(agent_response)

    def _try_direct_json_extraction(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to extract JSON directly from text using multiple strategies.

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON dict or None
        """
        # Strategy 1: Look for JSON code blocks (```json ... ```)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 2: Look for JSON without code block markers
        json_match = re.search(r'\{.*?"(?:questions|products)".*?\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Try to parse the entire text as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        return None

    def _validate_shopping_preference_structure(self, data: Dict[str, Any]) -> bool:
        """Validate shopping preference JSON structure.

        Args:
            data: Parsed JSON data

        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check required fields
            if 'agent_message' not in data or 'questions' not in data:
                logger.warning("Missing required fields: agent_message or questions")
                return False

            # Validate agent_message is a string
            if not isinstance(data['agent_message'], str):
                logger.warning("agent_message is not a string")
                return False

            # Validate questions is a list
            if not isinstance(data['questions'], list) or len(data['questions']) == 0:
                logger.warning("questions is not a non-empty list")
                return False

            # Validate each question structure
            for idx, question in enumerate(data['questions']):
                if not isinstance(question, dict):
                    logger.warning(f"Question {idx} is not a dict")
                    return False

                if 'question' not in question or 'options' not in question:
                    logger.warning(f"Question {idx} missing required fields")
                    return False

                if not isinstance(question['question'], str):
                    logger.warning(f"Question {idx} question field is not a string")
                    return False

                if not isinstance(question['options'], list) or len(question['options']) < 2:
                    logger.warning(f"Question {idx} options must be a list with at least 2 items")
                    return False

            logger.info("✅ Shopping preference structure validated successfully")
            return True

        except Exception as e:
            logger.error(f"Error validating shopping preference structure: {e}")
            return False

    def _validate_product_summary_structure(self, data: Dict[str, Any]) -> bool:
        """Validate product summary JSON structure.

        Args:
            data: Parsed JSON data

        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check required fields
            if 'products' not in data:
                logger.warning("Missing required field: products")
                return False

            # Validate products is a list
            if not isinstance(data['products'], list) or len(data['products']) == 0:
                logger.warning("products is not a non-empty list")
                return False

            # Validate each product structure
            for idx, product in enumerate(data['products']):
                if not isinstance(product, dict):
                    logger.warning(f"Product {idx} is not a dict")
                    return False

                required_fields = ['text_response', 'image_link', 'product_link']
                for field in required_fields:
                    if field not in product:
                        logger.warning(f"Product {idx} missing required field: {field}")
                        return False

                    if not isinstance(product[field], str):
                        logger.warning(f"Product {idx} {field} is not a string")
                        return False

            logger.info("✅ Product summary structure validated successfully")
            return True

        except Exception as e:
            logger.error(f"Error validating product summary structure: {e}")
            return False

    def _llm_extract_shopping_preference_json(self, agent_response: str) -> Optional[Dict[str, Any]]:
        """Use LLM to extract and structure shopping preference JSON from agent response.

        Args:
            agent_response: Raw agent response

        Returns:
            Structured JSON dict or None if extraction fails
        """
        prompt = f"""You are a JSON extraction assistant. Extract the shopping preference questions from the agent response below and format them as valid JSON.

The JSON MUST have this exact structure:
{{
    "agent_message": "A brief message introducing the questions (1 sentence)",
    "questions": [
        {{
            "question": "The question text",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"]
        }}
    ]
}}

RULES:
1. Extract ALL questions and options from the agent response
2. Each question should have 3-4 options (at least 2)
3. The agent_message should be friendly and concise (1 sentence)
4. Return ONLY the JSON object, no additional text
5. If no questions are found, create appropriate shopping preference questions based on the product mentioned

Agent Response:
{agent_response}

Valid JSON Output:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    'temperature': 0.1,  # Low temperature for consistent structured output
                }
            )

            json_text = response.text.strip()

            # Remove markdown code blocks if present
            json_text = re.sub(r'```json\s*', '', json_text)
            json_text = re.sub(r'```\s*$', '', json_text)
            json_text = json_text.strip()

            # Parse JSON
            json_data = json.loads(json_text)

            # Validate structure
            if self._validate_shopping_preference_structure(json_data):
                logger.info("✅ Successfully extracted and validated JSON using LLM")
                return json_data
            else:
                logger.error("LLM-extracted JSON failed validation")
                return None

        except Exception as e:
            logger.error(f"Failed to extract JSON using LLM: {e}")
            return None

    def _llm_extract_product_summary_json(self, agent_response: str) -> Optional[Dict[str, Any]]:
        """Use LLM to extract and structure product summary JSON from agent response.

        Args:
            agent_response: Raw agent response

        Returns:
            Structured JSON dict or None if extraction fails
        """
        prompt = f"""You are a JSON extraction assistant. Extract the product recommendations from the agent response below and format them as valid JSON.

The JSON MUST have this exact structure:
{{
    "products": [
        {{
            "text_response": "3-5 sentences explaining why this product matches preferences, key features, and benefits. Use specific numbers.",
            "image_link": "https://example.com/image.jpg or placeholder URL",
            "product_link": "https://retailer.com/product"
        }}
    ]
}}

RULES:
1. Extract ALL products mentioned in the agent response
2. Each text_response should be 3-5 sentences explaining features and benefits
3. Use actual image URLs if provided, otherwise use: "https://via.placeholder.com/400x400?text=Product+Image"
4. Use actual product purchase links if provided
5. Return ONLY the JSON object, no additional text
6. Maintain the order of products (best matches first)

Agent Response:
{agent_response}

Valid JSON Output:"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    'temperature': 0.1,  # Low temperature for consistent structured output
                }
            )

            json_text = response.text.strip()

            # Remove markdown code blocks if present
            json_text = re.sub(r'```json\s*', '', json_text)
            json_text = re.sub(r'```\s*$', '', json_text)
            json_text = json_text.strip()

            # Parse JSON
            json_data = json.loads(json_text)

            # Validate structure
            if self._validate_product_summary_structure(json_data):
                logger.info("✅ Successfully extracted and validated JSON using LLM")
                return json_data
            else:
                logger.error("LLM-extracted JSON failed validation")
                return None

        except Exception as e:
            logger.error(f"Failed to extract JSON using LLM: {e}")
            return None


# Singleton instance
_enforcer_instance: Optional[JSONStructureEnforcer] = None


def get_json_enforcer() -> JSONStructureEnforcer:
    """Get or create the singleton JSONStructureEnforcer instance.

    Returns:
        JSONStructureEnforcer instance
    """
    global _enforcer_instance
    if _enforcer_instance is None:
        _enforcer_instance = JSONStructureEnforcer()
    return _enforcer_instance

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class RequestData(BaseModel):
    message: str
    data: dict = {}

@app.post("/api/endpoint")
async def post_endpoint(request: RequestData):
    return {
        "status": "success",
        "received_message": request.message,
        "received_data": request.data
    }

@app.get("/")
async def root():
    return {"message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

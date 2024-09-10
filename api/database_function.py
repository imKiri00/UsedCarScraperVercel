from fastapi import FastAPI, HTTPException
import httpx
import logging
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_SERVICE_URL = os.environ.get("DATABASE_SERVICE_URL")

@app.post("/api/save")
async def save_to_database(posts: list):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Calling database service to save {len(posts)} posts")
            database_response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(f"Database service response: {save_result}")
            return save_result
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
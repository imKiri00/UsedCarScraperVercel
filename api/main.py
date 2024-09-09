from fastapi import FastAPI, Query, HTTPException
import os
import logging
import traceback
from dotenv import load_dotenv
import time
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

SCRAPER_SERVICE_URL = "http://localhost:8002"
DATABASE_SERVICE_URL = "http://localhost:8001"

@app.get("/api/scrape")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        start_time = time.time()
        logger.info(f"=== SCRAPE FUNCTION STARTED FOR PAGE {page} ===")

        async with httpx.AsyncClient() as client:
            # Call scraper service
            scraper_response = await client.get(f"{SCRAPER_SERVICE_URL}/scrape", params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Extracted {len(extracted_posts)} posts from page {page}")

            # Call database service
            database_response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=extracted_posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(save_result["message"])

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"=== SCRAPE FUNCTION COMPLETED FOR PAGE {page} ===")
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        return {"message": f"Successfully processed page {page} in {execution_time:.2f} seconds."}
    except httpx.HTTPError as e:
        error_msg = f"HTTP error occurred: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unhandled error in scrape function: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(error_msg)
        logger.error(stack_trace)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the scraping process. Please check the logs for more details.")

@app.get("/api/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
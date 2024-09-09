from fastapi import FastAPI, Query
import os
import logging
import traceback
from dotenv import load_dotenv
from firebase_admin import firestore
from api.firebase_init import db
from api.scraper import extract_car_info
from api.database import save_to_firestore
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

@app.get("/api/scrape")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        start_time = time.time()
        logger.info(f"=== SCRAPE FUNCTION STARTED FOR PAGE {page} ===")
        url = f"https://www.polovniautomobili.com/auto-oglasi/pretraga?page={page}&sort=basic&brand=alfa-romeo&city_distance=0&showOldNew=all&without_price=1"
        
        try:
            logger.info(f"Processing page {page}")
            extracted_posts = extract_car_info(url)
            logger.info(f"Extracted {len(extracted_posts)} posts from page {page}")
            new_posts = save_to_firestore(extracted_posts)
            logger.info(f"Saved {len(new_posts)} new posts to Firestore from page {page}")
        except Exception as e:
            error_msg = f"Error in scrape function for page {page}: {str(e)}"
            stack_trace = traceback.format_exc()
            logger.error(error_msg)
            logger.error(stack_trace)
            return {"error": error_msg}

        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"=== SCRAPE FUNCTION COMPLETED FOR PAGE {page} ===")
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        logger.info(f"New posts processed: {len(new_posts)}")
        return {"message": f"Successfully processed {len(new_posts)} new posts from page {page} in {execution_time:.2f} seconds."}
    except Exception as e:
        error_msg = f"Unhandled error in scrape function: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(error_msg)
        logger.error(stack_trace)
        return {"error": "An unexpected error occurred during the scraping process. Please check the logs for more details."}

@app.get("/api/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI
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
async def scrape():
    try:
        start_time = time.time()
        logger.info("=== SCRAPE FUNCTION STARTED ===")
        total_new_posts = 0
        for a in range(1, 10):
            url = f"https://www.polovniautomobili.com/auto-oglasi/pretraga?page={a}&sort=basic&brand=alfa-romeo&city_distance=0&showOldNew=all&without_price=1"
            try:
                logger.info(f"Processing page {a}/10")
                extracted_posts = extract_car_info(url)
                logger.info(f"Extracted {len(extracted_posts)} posts from page {a}")
                new_posts = save_to_firestore(extracted_posts)
                logger.info(f"Saved {len(new_posts)} new posts to Firestore from page {a}")
                total_new_posts += len(new_posts)
            except Exception as e:
                error_msg = f"Error in scrape function for page {a}: {str(e)}"
                stack_trace = traceback.format_exc()
                logger.error(error_msg)
                logger.error(stack_trace)
                # Continue to the next iteration instead of returning immediately
                continue
       
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"=== SCRAPE FUNCTION COMPLETED ===")
        logger.info(f"Total execution time: {execution_time:.2f} seconds")
        logger.info(f"Total new posts processed: {total_new_posts}")
        return {"message": f"Successfully processed {total_new_posts} new posts across 10 pages in {execution_time:.2f} seconds."}
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

@app.get("/api/debug")
async def debug():
    logger.info("Debug endpoint called")
    try:
        # Test Firebase connection
        docs = db.collection('test').limit(1).get()
        firebase_ok = True
        firebase_error = None
    except Exception as e:
        firebase_ok = False
        firebase_error = str(e)

    return {
        "firebase_initialized": db is not None,
        "firebase_connection_ok": firebase_ok,
        "firebase_error": firebase_error,
        "env_vars": {
            "FIREBASE_TYPE": os.getenv('FIREBASE_TYPE') is not None,
            "FIREBASE_PROJECT_ID": os.getenv('FIREBASE_PROJECT_ID') is not None,
            "FIREBASE_PRIVATE_KEY_ID": os.getenv('FIREBASE_PRIVATE_KEY_ID') is not None,
            "FIREBASE_PRIVATE_KEY": os.getenv('FIREBASE_PRIVATE_KEY') is not None,
            "FIREBASE_CLIENT_EMAIL": os.getenv('FIREBASE_CLIENT_EMAIL') is not None,
            "FIREBASE_CLIENT_ID": os.getenv('FIREBASE_CLIENT_ID') is not None,
            "FIREBASE_AUTH_URI": os.getenv('FIREBASE_AUTH_URI') is not None,
            "FIREBASE_TOKEN_URI": os.getenv('FIREBASE_TOKEN_URI') is not None,
            "FIREBASE_AUTH_PROVIDER_X509_CERT_URL": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL') is not None,
            "FIREBASE_CLIENT_X509_CERT_URL": os.getenv('FIREBASE_CLIENT_X509_CERT_URL') is not None,
            "FIREBASE_UNIVERSE_DOMAIN": os.getenv('FIREBASE_UNIVERSE_DOMAIN') is not None,
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
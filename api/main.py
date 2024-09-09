from fastapi import FastAPI
import os
import logging
import traceback
from dotenv import load_dotenv
from firebase_admin import firestore
from api.firebase_init import db
from api.scraper import extract_posts
from api.database import save_to_firestore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

@app.get("/api/scrape")
async def scrape():
    url = "http://www.phpbb.com/community/viewtopic.php?f=46&t=2159437"
    try:
        logger.info("Starting scrape function")
        extracted_posts = extract_posts(url)
        logger.info(f"Extracted {len(extracted_posts)} posts")
        new_posts = save_to_firestore(extracted_posts)
        logger.info(f"Saved {len(new_posts)} new posts to Firestore")
        return {"message": f"Successfully processed {len(new_posts)} new posts."}
    except Exception as e:
        error_msg = f"Error in scrape function: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.error(error_msg)
        logger.error(stack_trace)
        return {"error": error_msg, "traceback": stack_trace}, 500

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/debug")
async def debug():
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
from fastapi import FastAPI, HTTPException
import re
import requests
import os
import firebase_admin
from firebase_admin import credentials, firestore
import traceback
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
        })
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {str(e)}")
    logger.error(traceback.format_exc())
    raise

def extract_posts(url):
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        logger.info(f"Successfully fetched URL. Content length: {len(content)}")

        pattern = r'<div class="content">(.*?)</div>'
        posts = re.findall(pattern, content, re.DOTALL)
        logger.info(f"Found {len(posts)} raw posts")

        cleaned_posts = []
        for i, post in enumerate(posts, 1):
            clean_post = re.sub(r'<.*?>', '', post)
            clean_post = re.sub(r'\s+', ' ', clean_post).strip()
            cleaned_posts.append((i, clean_post))

        logger.info(f"Successfully extracted and cleaned {len(cleaned_posts)} posts")
        return cleaned_posts
    except requests.RequestException as e:
        logger.error(f"Failed to fetch or parse URL: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in extract_posts: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def save_to_firestore(posts):
    new_posts = []
    try:
        for post_number, content in posts:
            post_id = f"{post_number}-{hash(content)}"
            doc_ref = db.collection('posts').document(post_id)
            
            if not doc_ref.get().exists:
                doc_ref.set({
                    'post_number': post_number,
                    'content': content
                })
                new_posts.append(f"{post_number} [{content}]")
                logger.info(f"Saved new post: {post_id}")
            else:
                logger.info(f"Post already exists: {post_id}")

        logger.info(f"Successfully saved {len(new_posts)} new posts to Firestore")
        return new_posts
    except Exception as e:
        logger.error(f"Error in save_to_firestore: {str(e)}")
        logger.error(traceback.format_exc())
        raise

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
        logger.error(f"Error in scrape function: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}\n{traceback.format_exc()}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/debug")
async def debug():
    try:
        # Test Firebase connection
        db = firestore.client()
        docs = db.collection('test').limit(1).get()
        firebase_ok = True
        firebase_error = None
    except Exception as e:
        firebase_ok = False
        firebase_error = str(e)

    return {
        "firebase_initialized": len(firebase_admin._apps) > 0,
        "firebase_connection_ok": firebase_ok,
        "firebase_error": firebase_error,
        "env_vars": {
            "FIREBASE_PROJECT_ID": os.getenv('FIREBASE_PROJECT_ID') is not None,
            "FIREBASE_PRIVATE_KEY": os.getenv('FIREBASE_PRIVATE_KEY') is not None,
            "FIREBASE_CLIENT_EMAIL": os.getenv('FIREBASE_CLIENT_EMAIL') is not None,
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
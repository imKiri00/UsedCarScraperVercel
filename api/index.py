# api/scrape.py
from fastapi import FastAPI, HTTPException
import re
import requests
import os
import firebase_admin
from firebase_admin import credentials, firestore
import traceback
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        pattern = r'<div class="content">(.*?)</div>'
        posts = re.findall(pattern, content, re.DOTALL)
        cleaned_posts = []
        for i, post in enumerate(posts, 1):
            clean_post = re.sub(r'<.*?>', '', post)
            clean_post = re.sub(r'\s+', ' ', clean_post).strip()
            cleaned_posts.append((i, clean_post))
        logger.info(f"Successfully extracted {len(cleaned_posts)} posts")
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
        extracted_posts = extract_posts(url)
        new_posts = save_to_firestore(extracted_posts)
        return {"message": f"Successfully processed {len(new_posts)} new posts."}
    except Exception as e:
        logger.error(f"Error in scrape function: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Add a simple health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
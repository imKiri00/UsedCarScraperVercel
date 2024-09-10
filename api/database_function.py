from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
import logging
import os
import hashlib
import traceback
from pydantic import BaseModel, ValidationError
from typing import List, Union, Dict

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CarPost(BaseModel):
    title: str = None
    price: str = None
    year_body: str = None
    engine: str = None
    mileage: str = None
    power: str = None
    transmission: str = None
    doors_seats: str = None
    post_link: str = None

@app.post("/api/database")
async def save_to_database(posts: Union[List[CarPost], List[Dict]]):
    try:
        logger.info(f"Received {len(posts)} posts to save to database")
        logger.debug(f"First post sample: {posts[0] if posts else 'No posts received'}")

        # Convert all posts to CarPost objects for validation
        validated_posts = []
        for post in posts:
            if isinstance(post, dict):
                try:
                    validated_posts.append(CarPost(**post))
                except ValidationError as e:
                    logger.error(f"Validation error for post: {post}")
                    logger.error(f"Validation error details: {e}")
                    raise HTTPException(status_code=422, detail=f"Invalid post data: {e}")
            elif isinstance(post, CarPost):
                validated_posts.append(post)
            else:
                logger.error(f"Unexpected post type: {type(post)}")
                raise HTTPException(status_code=422, detail=f"Unexpected post type: {type(post)}")

        new_posts = save_to_firestore(validated_posts)
        logger.info(f"Saved {len(new_posts)} new posts to database")
        return {"new_posts": new_posts}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def save_to_firestore(posts: List[CarPost]):
    new_posts = []
    try:
        for post in posts:
            post_dict = jsonable_encoder(post)
            post_link = post_dict.get('post_link')
            if post_link:
                doc_id = hashlib.md5(post_link.encode()).hexdigest()
                doc_ref = db.collection('posts').document(doc_id)
                doc = doc_ref.get()
                if not doc.exists:
                    doc_ref.set(post_dict)
                    new_posts.append(post_dict)
                    logger.info(f"Saved new post: {post_link}")
                else:
                    logger.info(f"Post already exists, skipping: {post_link}")
            else:
                logger.warning(f"Skipping post without post_link: {post_dict}")
        return new_posts
    except Exception as e:
        logger.error(f"Error in save_to_firestore: {str(e)}")
        logger.error(traceback.format_exc())
        raise

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = {
                "type": os.environ.get("FIREBASE_TYPE"),
                "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
                "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
                "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
                "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN")
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        logger.info("Firebase initialized successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise

# Initialize Firebase when this module is imported
db = initialize_firebase()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
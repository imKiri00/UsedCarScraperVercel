import os
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
import hashlib
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = {
                "type": os.getenv("FIREBASE_TYPE"),
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
                "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
                "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
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


@app.post("/save")
async def save_data(posts: List[dict]):
    new = 0
    old = 0
    new_posts = []
    try:
        for post in posts:
            if isinstance(post, dict) and 'post_link' in post:
                post_link = post['post_link']
                doc_id = hashlib.md5(post_link.encode()).hexdigest()
                doc_ref = db.collection('posts').document(doc_id)
                doc = doc_ref.get()
                if not doc.exists:
                    doc_ref.set(post)
                    new += 1
                    new_posts.append(post)
                else:
                    old += 1
            else:
                logger.warning(f"Skipping invalid post: {post}")
       
        return {
            "message": f"New: {new}, old: {old}",
            "new_posts": new_posts
        }
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
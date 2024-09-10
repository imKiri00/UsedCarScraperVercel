from fastapi import FastAPI, HTTPException
import logging
import os
import hashlib
import traceback
import multipart

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.post("/api/save")
async def save_to_database(posts: list):
    try:
        logger.info(f"Saving {len(posts)} posts to database")
        new_posts = save_to_firestore(posts)
        logger.info(f"Saved {len(new_posts)} new posts to database")
        return {"new_posts": new_posts}
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



def save_to_firestore(posts):
    new_posts = []
    try:
        for post in posts:
            if isinstance(post, dict):
                post_link = post.get('post_link')
                if post_link:
                    # Create a hash of the post_link to use as the document ID
                    doc_id = hashlib.md5(post_link.encode()).hexdigest()
                    doc_ref = db.collection('posts').document(doc_id)
                    doc = doc_ref.get()
                    if not doc.exists:
                        doc_ref.set(post)
                        new_posts.append(post)
                        # Send email notification for new post
                        subject = 'Novi Auto PolovniAutomobili'
                        to_email = os.environ.get("NOTIFICATION_EMAIL")  # Email to receive notifications
                        #send_email_notification(subject, post, to_email)
            elif isinstance(post, str):
                logger.warning(f"Skipping string post: {post[:100]}...")  # Log first 100 chars
            else:
                logger.warning(f"Unexpected post type: {type(post)}")
        return new_posts
    except Exception as e:
        logger.error(f"Error in save_to_firestore: {str(e)}")
        logger.error(traceback.format_exc())
        raise



import os
import firebase_admin
from firebase_admin import credentials, firestore
import logging
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
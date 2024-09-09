from fastapi import FastAPI, HTTPException
from firebase_admin import firestore
from api.firebase_init import db
import logging
import httpx
import os
import hashlib
from dotenv import load_dotenv

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

EMAIL_SERVICE_URL = "http://localhost:8003"

@app.post("/save")
async def save_to_firestore(posts: list):
    try:
        new_posts = []
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
                        await send_email_notification(post)
            elif isinstance(post, str):
                logger.warning(f"Skipping string post: {post[:100]}...")  # Log first 100 chars
            else:
                logger.warning(f"Unexpected post type: {type(post)}")
        
        logger.info(f"Saved {len(new_posts)} new posts to Firestore")
        return {"message": f"Successfully saved {len(new_posts)} new posts to Firestore"}
    except Exception as e:
        logger.error(f"Error saving to Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving to Firestore: {str(e)}")

async def send_email_notification(post):
    subject = 'Novi Auto PolovniAutomobili'
    to_email = os.getenv("NOTIFICATION_EMAIL")  # Email to receive notifications
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{EMAIL_SERVICE_URL}/send_email", json={
                "subject": subject,
                "car_info": post,
                "to_email": to_email
            })
            response.raise_for_status()
            logger.info(f"Email notification sent for post: {post.get('post_link')}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to send email notification: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
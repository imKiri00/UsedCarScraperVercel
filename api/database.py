import logging
import traceback
from api.firebase_init import db

logger = logging.getLogger(__name__)

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
import logging
import traceback
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from api.firebase_init import db
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def send_email_notification(subject, car_info, to_email):
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Create the email body with all car information, nicely formatted
    body = "A new car has been added:\n\n"
    body += "=" * 40 + "\n\n"  # Separator line

    for key, value in car_info.items():
        if value:  # Only include non-None values
            formatted_key = key.replace('_', ' ').title()
            if key == "post_link":
                body += f"{formatted_key}:\n{value}\n\n"
            else:
                body += f"{formatted_key}: {value}\n"

    body += "\n" + "=" * 40 + "\n"  # Separator line at the end
    body += "This is an automated notification. Please do not reply to this email."

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
        logger.info(f"Email notification sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

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
                        to_email = os.getenv("NOTIFICATION_EMAIL")  # Email to receive notifications
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
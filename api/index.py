# api/scrape.py

from fastapi import FastAPI, HTTPException
import re
import requests
import os
import firebase_admin
from firebase_admin import credentials, firestore

app = FastAPI()

from dotenv import load_dotenv
load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
        "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    })
    firebase_admin.initialize_app(cred)
db = firestore.client()

def extract_posts(url):
    response = requests.get(url)
    content = response.text
    pattern = r'<div class="content">(.*?)</div>'
    posts = re.findall(pattern, content, re.DOTALL)
    cleaned_posts = []
    for i, post in enumerate(posts, 1):
        clean_post = re.sub(r'<.*?>', '', post)
        clean_post = re.sub(r'\s+', ' ', clean_post).strip()
        cleaned_posts.append((i, clean_post))
    return cleaned_posts

def save_to_firestore(posts):
    new_posts = []
    for post_number, content in posts:
        # Create a hash of the content to use as a unique identifier
        post_id = f"{post_number}-{hash(content)}"
        doc_ref = db.collection('posts').document(post_id)
        
        # Check if the document already exists
        if not doc_ref.get().exists:
            doc_ref.set({
                'post_number': post_number,
                'content': content
            })
            new_posts.append(f"{post_number} [{content}]")
    return new_posts

@app.get("/api/scrape")
async def scrape():
    url = "http://www.phpbb.com/community/viewtopic.php?f=46&t=2159437"
    try:
        extracted_posts = extract_posts(url)
        new_posts = save_to_firestore(extracted_posts)
        return {"message": f"Successfully processed {len(new_posts)} new posts."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
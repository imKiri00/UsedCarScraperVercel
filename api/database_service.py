import os
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
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
async def save_data(data: dict):
    try:
        # Your logic to save data to Firebase
        # For example:
        doc_ref = db.collection('your_collection').document()
        doc_ref.set(data)
        return {"message": "Data saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        # Perform a simple read operation to check if Firebase is accessible
        db.collection('health_check').document('test').get()
        return {"status": "healthy", "message": "Firebase connection is working"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Firebase connection is not working")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
from fastapi import FastAPI, HTTPException
import httpx
import logging
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003")

@app.post("/api/send_email")
async def send_email(email_data: dict):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Calling email service to send notification")
            email_response = await client.post(f"{EMAIL_SERVICE_URL}/send_email", json=email_data)
            email_response.raise_for_status()
            logger.info("Email notification sent successfully")
            return {"message": "Email sent successfully"}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
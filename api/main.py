from fastapi import FastAPI, Query, HTTPException
import httpx
import asyncio
import logging
import os

app = FastAPI()
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use environment variables for service URLs
SCRAPER_SERVICE_URL = os.getenv("SCRAPER_SERVICE_URL", "http://localhost:8002")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003")
@app.get("/api/scrape")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        async with httpx.AsyncClient() as client:
            # Call scraper service
            logger.info(f"Calling scraper service for page {page}")
            scraper_response = await client.get(f"{SCRAPER_SERVICE_URL}/scrape", params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper service")
           
            # Call database service
            logger.info(f"Calling database service to save {len(extracted_posts)} posts")
            database_response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=extracted_posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(f"Database service response: {save_result}")
           
            
            new_posts = save_result["new_posts"]  # Altered
            new_posts_count = len(new_posts)  # Altered
            logger.info(f"Number of new posts: {new_posts_count}")

            # Send email notifications for new posts (limited to first 5 to avoid timeouts)
            email_tasks = []
            for post in new_posts:
                email_task = client.post(f"{EMAIL_SERVICE_URL}/send_email",
                                         json={"subject": "New Car Listed", "car_info": post})
                email_tasks.append(email_task)
           
            if email_tasks:
                await asyncio.gather(*email_tasks)
                logger.info(f"Sent {len(email_tasks)} email notifications")
           
        return {"message": f"Successfully processed page {page}.", "new_posts": new_posts_count}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
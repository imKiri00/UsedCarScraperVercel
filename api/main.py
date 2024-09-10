from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
import httpx
import asyncio
import logging
import os
from typing import Optional

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use environment variables for service URLs without default values
SCRAPER_FUNCTION_URL = os.getenv("SCRAPER_FUNCTION_URL")
DATABASE_FUNCTION_URL = os.getenv("DATABASE_FUNCTION_URL")
EMAIL_FUNCTION_URL = os.getenv("EMAIL_FUNCTION_URL")

# Check if environment variables are set
if not all([SCRAPER_FUNCTION_URL, DATABASE_FUNCTION_URL, EMAIL_FUNCTION_URL]):
        
    logger.error(f"One or more required environment variables are not set. U have {SCRAPER_FUNCTION_URL}, {DATABASE_FUNCTION_URL}, {EMAIL_FUNCTION_URL}")
    raise EnvironmentError("Missing required environment variables")

async def process_data(page: int) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            # Call scraper function
            logger.info(f"Calling scraper function for page {page}")
            scraper_response = await client.get(SCRAPER_FUNCTION_URL, params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper function")
           
            # Call database function
            logger.info(f"Calling database function to save {len(extracted_posts)} posts")
            database_response = await client.post(DATABASE_FUNCTION_URL, json=extracted_posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(f"Database function response: {save_result}")
           
            new_posts = save_result.get("new_posts", [])
            new_posts_count = len(new_posts)
            logger.info(f"Number of new posts: {new_posts_count}")

            # Send email notifications for new posts
            email_tasks = []
            for post in new_posts:
                email_task = client.post(EMAIL_FUNCTION_URL,
                                         json={"subject": "New Car Listed", "car_info": post})
                email_tasks.append(email_task)
           
            if email_tasks:
                await asyncio.gather(*email_tasks)
                logger.info(f"Sent {len(email_tasks)} email notifications")
           
        logger.info(f"Successfully processed page {page}.")
        return None
    except httpx.HTTPError as e:
        error_message = f"HTTP error occurred while calling {e.request.url}: {str(e)}"
        logger.error(error_message)
        return error_message
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        return error_message

@app.get("/api/scrape")
async def scrape(background_tasks: BackgroundTasks, page: int = Query(..., description="Page number to scrape")):
    try:
        logger.info(f"Received request to scrape page {page}")
        background_tasks.add_task(process_data, page)
        return {"message": f"Processing page {page} in the background."}
    except Exception as e:
        logger.error(f"Error occurred while initiating background task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
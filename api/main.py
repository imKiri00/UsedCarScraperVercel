from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
import httpx
import asyncio
import logging
import os
import json
import traceback
from typing import Optional, List, Dict
from pydantic import BaseModel

app = FastAPI()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use environment variables for service URLs without default values
SCRAPER_FUNCTION_URL = os.environ.get("SCRAPER_FUNCTION_URL")
DATABASE_FUNCTION_URL = os.environ.get("DATABASE_FUNCTION_URL")
EMAIL_FUNCTION_URL = os.environ.get("EMAIL_FUNCTION_URL")

# Check if environment variables are set
if not all([SCRAPER_FUNCTION_URL, DATABASE_FUNCTION_URL, EMAIL_FUNCTION_URL]):
    logger.error(f"One or more required environment variables are not set. U have {SCRAPER_FUNCTION_URL}, {DATABASE_FUNCTION_URL}, {EMAIL_FUNCTION_URL}")
    raise EnvironmentError("Missing required environment variables")

# Configuration
BATCH_SIZE = 5
BATCH_DELAY = 1  # Delay between batches in seconds

async def process_data(page: int) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            # Call scraper function
            logger.info(f"Calling scraper function for page {page}")
            scraper_response = await client.get(SCRAPER_FUNCTION_URL, params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper function")
            
            # Call database function in batches
            new_posts = []
            for i in range(0, len(extracted_posts), BATCH_SIZE):
                batch = extracted_posts[i:i+BATCH_SIZE]
                logger.info(f"Calling database function to save batch {i//BATCH_SIZE + 1} of {len(batch)} posts")
    
                # Send the data in the request body as JSON
                database_response = await client.post(DATABASE_FUNCTION_URL, json={"posts": batch})
                database_response.raise_for_status()
                save_result = database_response.json()
                logger.info(f"Database function response for batch {i//BATCH_SIZE + 1} (parsed): {save_result}")
                new_posts.extend(save_result.get("new_posts", []))

                if i + BATCH_SIZE < len(extracted_posts):
                    logger.info(f"Waiting {BATCH_DELAY} seconds before processing next batch")
                    await asyncio.sleep(BATCH_DELAY)
                        
            new_posts_count = len(new_posts)
            logger.info(f"Total number of new posts: {new_posts_count}")

            # Send email notifications for new posts (in batches to avoid timeout)
            for i in range(0, len(new_posts), BATCH_SIZE):
                batch = new_posts[i:i+BATCH_SIZE]
                email_tasks = []
                for post in batch:
                    email_task = client.post(EMAIL_FUNCTION_URL,
                                             json={"subject": "New Car Listed", "car_info": post})
                    email_tasks.append(email_task)
               
                if email_tasks:
                    await asyncio.gather(*email_tasks)
                    logger.info(f"Sent {len(email_tasks)} email notifications for batch {i//BATCH_SIZE + 1}")
                
                if i + BATCH_SIZE < len(new_posts):
                    logger.info(f"Waiting {BATCH_DELAY} seconds before sending next batch of emails")
                    await asyncio.sleep(BATCH_DELAY)
           
        logger.info(f"Successfully processed page {page}.")
        return None
    except httpx.ReadTimeout as e:
        error_message = f"Read timeout occurred while calling {e.request.url}: {str(e)}"
        logger.error(error_message)
        return error_message
    except httpx.HTTPError as e:
        error_message = f"HTTP error occurred while calling {e.request.url}: {str(e)}"
        logger.error(error_message)
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        else:
            logger.error("No response available for this error.")
        return error_message
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        logger.error(error_message)
        logger.error(f"Error details: {traceback.format_exc()}")
        return error_message

@app.get("/api/main")
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
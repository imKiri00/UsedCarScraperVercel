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

class CarPost(BaseModel):
    title: str = None
    price: str = None
    year_body: str = None
    engine: str = None
    mileage: str = None
    power: str = None
    transmission: str = None
    doors_seats: str = None
    post_link: str = None

def convert_to_car_posts(extracted_posts: List[Dict]) -> List[CarPost]:
    car_posts = []
    for post in extracted_posts:
        try:
            car_post = CarPost(**post)
            car_posts.append(car_post)
        except Exception as e:
            logger.error(f"Error converting post to CarPost: {str(e)}")
            logger.error(f"Problematic post: {json.dumps(post, indent=2)}")
    return car_posts

async def process_data(page: int) -> Optional[str]:
    try:
        async with httpx.AsyncClient() as client:
            # Call scraper function
            logger.info(f"Calling scraper function for page {page}")
            scraper_response = await client.get(SCRAPER_FUNCTION_URL, params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper function")
            logger.debug(f"Sample of extracted posts: {json.dumps(extracted_posts[:2], indent=2)}")
           
            # Convert extracted posts to CarPost objects
            car_posts = convert_to_car_posts(extracted_posts)
            logger.info(f"Converted {len(car_posts)} posts to CarPost objects")
            logger.debug(f"Sample of converted CarPost objects: {json.dumps([post.dict() for post in car_posts[:2]], indent=2)}")

            # Call database function
            logger.info(f"Calling database function to save {len(car_posts)} posts")
            posts_to_save = [post.dict() for post in car_posts]
            logger.debug(f"Sample of posts being sent to database: {json.dumps(posts_to_save[:2], indent=2)}")
            database_response = await client.post(DATABASE_FUNCTION_URL, json=posts_to_save)
            
            # Log the entire response from the database function
            logger.info(f"Database function response status: {database_response.status_code}")
            logger.info(f"Database function response headers: {dict(database_response.headers)}")
            logger.info(f"Database function response content: {database_response.text}")
            
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(f"Database function response (parsed): {save_result}")
           
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
        if e.response:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
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
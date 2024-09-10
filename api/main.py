from fastapi import FastAPI, Query, HTTPException, BackgroundTasks
import httpx
import os
import json
import traceback
from typing import Optional
from asyncio import create_task

app = FastAPI()

# Use environment variables for service URLs without default values
SCRAPER_FUNCTION_URL = os.environ.get("SCRAPER_FUNCTION_URL")
DATABASE_FUNCTION_URL = os.environ.get("DATABASE_FUNCTION_URL")

print(f"DEBUG: SCRAPER_FUNCTION_URL = {SCRAPER_FUNCTION_URL}")
print(f"DEBUG: DATABASE_FUNCTION_URL = {DATABASE_FUNCTION_URL}")

# Check if environment variables are set
if not all([SCRAPER_FUNCTION_URL, DATABASE_FUNCTION_URL]):
    print(f"DEBUG: Missing environment variables. SCRAPER_FUNCTION_URL = {SCRAPER_FUNCTION_URL}, DATABASE_FUNCTION_URL = {DATABASE_FUNCTION_URL}")
    raise EnvironmentError("Missing required environment variables")

async def send_to_database(extracted_posts):
    try:
        print(f"DEBUG: Attempting to send {len(extracted_posts)} posts to database")
        async with httpx.AsyncClient() as client:
            print(f"DEBUG: Sending {len(extracted_posts)} posts to database function")
            await client.post(DATABASE_FUNCTION_URL, json={"posts": extracted_posts}, timeout=None)
           
            print("DEBUG: Data sent to database function")
    except Exception as e:
        print(f"DEBUG: Error sending data to database: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")

async def process_data(page: int) -> Optional[str]:
    try:
        print(f"DEBUG: Starting process_data for page {page}")
        async with httpx.AsyncClient() as client:
            # Call scraper function
            print(f"DEBUG: Calling scraper function for page {page}")
            print(f"DEBUG: Calling scraper function URL: {SCRAPER_FUNCTION_URL}")
            scraper_response = await client.get(SCRAPER_FUNCTION_URL, params={"page": page})
            print(f"DEBUG: Scraper function response status code: {scraper_response.status_code}")
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            print(f"DEBUG: Number of posts extracted: {len(extracted_posts)}")
            print(f"DEBUG: Received {len(extracted_posts)} posts from scraper function")
            print(f"DEBUG: Sample post from scraper: {json.dumps(extracted_posts[0] if extracted_posts else {}, indent=2)}")
           
            # Create a background task for sending data to the database
            print("DEBUG: Creating background task for send_to_database")
            create_task(send_to_database(extracted_posts))
            
        print(f"DEBUG: Successfully processed page {page}.")
        return None
    except httpx.ReadTimeout as e:
        error_message = f"Read timeout occurred while calling {e.request.url}: {str(e)}"
        print(f"DEBUG: Read timeout exception: {error_message}")
        return error_message
    except httpx.HTTPError as e:
        error_message = f"HTTP error occurred while calling {e.request.url}: {str(e)}"
        print(f"DEBUG: HTTP error exception: {error_message}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"DEBUG: Response status code: {e.response.status_code}")
            print(f"DEBUG: Response content: {e.response.text}")
        else:
            print("DEBUG: No response available for this error.")
        return error_message
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"DEBUG: Unexpected exception: {error_message}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return error_message

@app.get("/api/main")
async def scrape(background_tasks: BackgroundTasks, page: int = Query(..., description="Page number to scrape")):
    try:
        print(f"DEBUG: Received request to scrape page {page}")
        result = await process_data(page)
        if result:
            print(f"DEBUG: Error processing page {page}: {result}")
            return {"message": f"Error processing page {page}: {result}"}
        print(f"DEBUG: Successfully processed page {page}")
        return {"message": f"Successfully processed page {page}. Data is being sent to the database in the background."}
    except Exception as e:
        print(f"DEBUG: Exception in scrape function: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
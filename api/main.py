from fastapi import FastAPI, Query, HTTPException
import httpx
import asyncio
import logging
import os

app = FastAPI()
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
            scraper_response = await client.get(f"{SCRAPER_SERVICE_URL}/scrape", params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            
            # Call database service
            database_response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=extracted_posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            
            # Send email notifications for new posts (limited to first 5 to avoid timeouts)
            email_tasks = []
            for new_post in save_result["new_posts"][:5]:  # Limit to first 5 new posts
                email_task = client.post(f"{EMAIL_SERVICE_URL}/send_email", 
                                         json={"subject": "New Car Listed", "car_info": new_post})
                email_tasks.append(email_task)
            
            if email_tasks:
                await asyncio.gather(*email_tasks)
            
        return {"message": f"Successfully processed page {page}.", "new_posts": len(save_result["new_posts"])}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# This is for local development, won't be used on Vercel
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
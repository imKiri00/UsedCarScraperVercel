from fastapi import FastAPI, Query, HTTPException
import httpx
import logging
import os

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCRAPER_SERVICE_URL = os.getenv("SCRAPER_SERVICE_URL", "http://localhost:8002")

@app.get("/api/scrape")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Calling scraper service for page {page}")
            scraper_response = await client.get(f"{SCRAPER_SERVICE_URL}/scrape", params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper service")
            return {"posts": extracted_posts}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
from fastapi import FastAPI, HTTPException
from api.scraper import extract_car_info
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.get("/scrape")
async def scrape(page: int):
    try:
        url = f"https://www.polovniautomobili.com/auto-oglasi/pretraga?page={page}&sort=basic&brand=alfa-romeo&city_distance=0&showOldNew=all&without_price=1"
        extracted_posts = extract_car_info(url)
        logger.info(f"Extracted {len(extracted_posts)} posts from page {page}")
        return {"posts": extracted_posts}
    except Exception as e:
        logger.error(f"Error scraping page {page}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scraping page {page}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
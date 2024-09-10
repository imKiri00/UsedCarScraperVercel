from fastapi import FastAPI, Query, HTTPException
import httpx
import logging
import os
import re


app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.get("/api/scraper")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        logger.info(f"Scraping page {page}")
        result = await scrape_page(page)
        extracted_posts = result["posts"]
        logger.info(f"Received {len(extracted_posts)} posts from scraper")
        return {"posts": extracted_posts}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
async def scrape_page(page: int):
    url = f"https://www.polovniautomobili.com/auto-oglasi/pretraga?page={page}&sort=basic&brand=alfa-romeo&city_distance=0&showOldNew=all&without_price=1"
    
    try:
        car_info_list = await extract_car_info(url)
        
        q = {"posts": car_info_list}
        return q
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def extract_car_info(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    logger.info(f"Fetching URL: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        content = response.text

    # Define regex patterns
    title_pattern = r'title="([^"]+)"'
    price_pattern = r'<span>\s*([0-9.,]+\s*€)\s*</span>'
    year_body_pattern = r'<div class="top" title="([^"]+)">'
    engine_pattern = r'<div class="bottom" title="([^"]+)">'
    mileage_pattern = r'<div class="top" title="(\d+\.?\d*)\s*km">'
    power_pattern = r'<div class="bottom uk-hidden-medium uk-hidden-small" title="(\d+kW\s*\(\d+KS\))">'
    transmission_pattern = r'<div class="top" title="([^"]+)">'
    doors_seats_pattern = r'<div class="bottom" title="([^"]+)">'
    post_link_pattern = r'href="(/auto-oglasi/\d+/[^"]+)"'

    # Find all article elements
    article_pattern = r'<article class="classified[^>]*>(.*?)</article>'
    articles = re.findall(article_pattern, content, re.DOTALL)
    
    car_info_list = []
    for article in articles:
        # Extract information for each article
        title = re.search(title_pattern, article)
        price = re.search(price_pattern, article)
        year_body = re.search(year_body_pattern, article)
        engine = re.search(engine_pattern, article)
        mileage = re.search(mileage_pattern, article)
        power = re.search(power_pattern, article)
        transmission = re.search(transmission_pattern, article)
        doors_seats = re.search(doors_seats_pattern, article)
        post_link = re.search(post_link_pattern, article)
        
        car_info = {
            "title": title.group(1) if title else None,
            "price": price.group(1) if price else None,
            "year_body": year_body.group(1) if year_body else None,
            "engine": engine.group(1) if engine else None,
            "mileage": mileage.group(1) if mileage else None,
            "power": power.group(1) if power else None,
            "transmission": transmission.group(1) if transmission else None,
            "doors_seats": doors_seats.group(1) if doors_seats else None,
            "post_link": "https://www.polovniautomobili.com" + post_link.group(1) if post_link else None
        }
        car_info_list.append(car_info)
    
    logger.info(f"Successfully extracted information for {len(car_info_list)} cars")
    return car_info_list



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
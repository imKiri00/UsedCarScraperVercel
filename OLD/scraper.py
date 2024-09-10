import re
import requests
import logging
import traceback
from fastapi import FastAPI, Query, HTTPException
import httpx
import logging
import os
import re
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)

class CarPost(BaseModel):
    title: str = Field(default="")
    price: str = Field(default="")
    year_body: str = Field(default="")
    engine: str = Field(default="")
    mileage: str = Field(default="")
    power: str = Field(default="")
    transmission: str = Field(default="")
    doors_seats: str = Field(default="")
    post_link: str = Field(default="")

def extract_car_info(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Let requests handle the decoding
        content = response.text

        logger.debug(f"First 50 characters of content (check if encoded) {content[:50]}")

        # Rest of the function remains the same
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
            "title": title.group(1) if title else "",
            "price": price.group(1) if price else "",
            "year_body": year_body.group(1) if year_body else "",
            "engine": engine.group(1) if engine else "",
            "mileage": mileage.group(1) if mileage else "",
            "power": power.group(1) if power else "",
            "transmission": transmission.group(1) if transmission else "",
            "doors_seats": doors_seats.group(1) if doors_seats else "",
            "post_link": "https://www.polovniautomobili.com" + post_link.group(1) if post_link else ""
            }
        
            try:
                car_post = CarPost(**car_info)
                car_info_list.append(car_post)
            except Exception as e:
                logger.error(f"Error creating CarPost object: {str(e)}")
                logger.error(f"Problematic car_info: {car_info}")

                
        logger.info(f"Successfully extracted information for {len(car_info_list)} cars")
        return car_info_list




print(extract_car_info("https://www.polovniautomobili.com/auto-oglasi/pretraga?page=1&sort=basic&brand=alfa-romeo&city_distance=0&showOldNew=all&without_price=1"))
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import requests

app = FastAPI()

@app.get("/api/scrape")
async def scrape(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Example: Scrape all paragraph texts
        paragraphs = [p.text for p in soup.find_all('p')]
        
        return {"paragraphs": paragraphs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape the website: {str(e)}")

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from Python on Vercel!"}
import asyncio
import subprocess
import time
import httpx
from fastapi import FastAPI, Query, HTTPException
import logging
import os
from dotenv import load_dotenv
import socket
import psutil

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SCRAPER_SERVICE_URL = os.getenv("SCRAPER_SERVICE_URL", "http://localhost:8002")
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8003")
MAIN_SERVICE_URL = "http://localhost:8000"

# FastAPI app for the main service
app = FastAPI()

@app.get("/api/scrape")
async def scrape(page: int = Query(..., description="Page number to scrape")):
    try:
        async with httpx.AsyncClient() as client:
            # Call scraper service
            logger.info(f"Calling scraper service for page {page}")
            scraper_response = await client.get(f"{SCRAPER_SERVICE_URL}/cscrape", params={"page": page})
            scraper_response.raise_for_status()
            extracted_posts = scraper_response.json()["posts"]
            logger.info(f"Received {len(extracted_posts)} posts from scraper service")
            
            # Call database service
            logger.info(f"Calling database service to save {len(extracted_posts)} posts")
            database_response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=extracted_posts)
            database_response.raise_for_status()
            save_result = database_response.json()
            logger.info(f"Database service saved {len(save_result['new_posts'])} new posts")
            
            # Send email notifications for new posts
            logger.info(f"Sending email notifications for {len(save_result['new_posts'])} new posts")
            email_tasks = []
            for new_post in save_result["new_posts"]:
                email_task = client.post(f"{EMAIL_SERVICE_URL}/send_email",
                                         json={"subject": "New Car Listed", "car_info": new_post})
                email_tasks.append(email_task)
            
            if email_tasks:
                await asyncio.gather(*email_tasks)
            logger.info(f"Sent {len(email_tasks)} email notifications")
            
        return {"message": f"Successfully processed page {page}.", "new_posts": len(save_result["new_posts"])}
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while calling {e.request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def test_microservices():
    async with httpx.AsyncClient() as client:
        # Test scraper service
        try:
            response = await client.get(f"{SCRAPER_SERVICE_URL}/scrape", params={"page": 1})
            print(f"Scraper service test - Status: {response.status_code}")
        except Exception as e:
            print(f"Scraper service test failed: {str(e)}")

        # Test database service
        try:
            response = await client.post(f"{DATABASE_SERVICE_URL}/save", json=[{"test": "data"}])
            print(f"Database service test - Status: {response.status_code}")
        except Exception as e:
            print(f"Database service test failed: {str(e)}")

        # Test email service
        try:
            response = await client.post(f"{EMAIL_SERVICE_URL}/send_email",
                                        json={"subject": "Test Email", "car_info": {"test": "data"}})
            print(f"Email service test - Status: {response.status_code}")
        except Exception as e:
            print(f"Email service test failed: {str(e)}")


async def test_full_pipeline():
    async with httpx.AsyncClient() as client:
        for page in range(1, 4):  # Test for pages 1 to 2 (you can increase this range)
            try:
                print(f"Attempting to connect to {MAIN_SERVICE_URL}/api/scrape")
                response = await client.get(f"{MAIN_SERVICE_URL}/api/scrape", params={"page": page}, timeout=10.0)
                print(f"Page {page} - Status Code: {response.status_code}")
                if response.status_code == 200:
                    print(f"Page {page} - Response: {response.json()}")
                else:
                    print(f"Page {page} - Error: {response.text}")
            except httpx.ConnectError as e:
                print(f"Page {page} - Connection Error: {str(e)}")
                # Try to get more information about the connection failure
                try:
                    host, port = MAIN_SERVICE_URL.split("://")[1].split(":")
                    sock = socket.create_connection((host, int(port)), timeout=5)
                    sock.close()
                    print(f"Socket connection to {host}:{port} successful")
                except Exception as sock_e:
                    print(f"Socket connection failed: {str(sock_e)}")
            except Exception as e:
                print(f"Page {page} - Exception: {str(e)}")
            print("---")
            await asyncio.sleep(1)  # Add a delay to avoid rate limiting

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def close_process_on_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            try:
                process = psutil.Process(conn.pid)
                process.terminate()
                process.wait(timeout=5)
                print(f"Closed process on port {port} (PID: {conn.pid})")
                return True
            except psutil.NoSuchProcess:
                pass
    return False

def start_service(command, name, port):
    if is_port_in_use(port):
        print(f"Port {port} is already in use. Attempting to close the process...")
        if close_process_on_port(port):
            print(f"Successfully closed process on port {port}")
        else:
            print(f"Failed to close process on port {port}. Please close it manually.")
            return None

    try:
        process = subprocess.Popen(command, shell=True)
        print(f"Started {name} (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Failed to start {name}: {str(e)}")
        return None

async def main():
    # Start microservices
    scraper_process = start_service("python api/service_scraper.py", "Scraper Service", 8002)
    database_process = start_service("python api/service_database.py", "Database Service", 8001)
    email_process = start_service("python api/service_email.py", "Email Service", 8003)
    main_py = start_service("python api/main.py", "Main Service", 8000)
    # Give services time to start up
    await asyncio.sleep(5)
    
    # Run tests
    print("\nTesting individual microservices:")
    await test_microservices()
    
    print("\nTesting full pipeline:")
    await test_full_pipeline()
    
    # Clean up
    for process in [scraper_process, database_process, email_process, main_py]:
        if process:
            process.terminate()
            process.wait()
    
    print("\nAll services stopped.")

if __name__ == "__main__":
    asyncio.run(main())
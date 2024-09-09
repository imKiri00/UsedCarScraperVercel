# Used Car Scraper

This project is a web scraper for used car listings, built with FastAPI and deployed on Vercel. It extracts information from a specific car listing website and stores the data in Firebase Firestore.

## Features

- Scrapes used car listings from a target website
- Stores scraped data in Firebase Firestore
- FastAPI backend with health check and debug endpoints
- Deployed on Vercel for serverless operation
- Automated scraping using GitHub Actions

## Technology Stack

- Python 3.x
- FastAPI
- Firebase Admin SDK
- BeautifulSoup (for web scraping)
- Vercel (for deployment)
- GitHub Actions (for automated scraping)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/UsedCarScraperVercel.git
   cd UsedCarScraperVercel
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up Firebase:
   - Create a Firebase project and obtain the service account key
   - Rename the `.env.example` file to `.env` and fill in the Firebase credentials

5. Configure Vercel:
   - Install the Vercel CLI: `npm i -g vercel`
   - Run `vercel` to link your project to Vercel

## Usage

### Local Development

To run the project locally:

```
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`.

### API Endpoints

- `/api/scrape`: Triggers the scraping process
- `/api/health`: Health check endpoint
- `/api/debug`: Provides debug information about the Firebase connection and environment variables

### Deployment

The project is configured to deploy automatically to Vercel. Any push to the main branch will trigger a new deployment.

To manually deploy:

```
vercel --prod
```

### Automated Scraping

The project includes a GitHub Actions workflow that triggers the scraping process on a schedule. You can modify the schedule in the `.github/workflows/trigger_scrape.yml` file. 

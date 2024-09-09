import re
import requests
import logging
import traceback

logger = logging.getLogger(__name__)

def extract_posts(url):
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        content = response.text
        logger.info(f"Successfully fetched URL. Content length: {len(content)}")

        pattern = r'<div class="content">(.*?)</div>'
        posts = re.findall(pattern, content, re.DOTALL)
        logger.info(f"Found {len(posts)} raw posts")

        cleaned_posts = []
        for i, post in enumerate(posts, 1):
            clean_post = re.sub(r'<.*?>', '', post)
            clean_post = re.sub(r'\s+', ' ', clean_post).strip()
            cleaned_posts.append((i, clean_post))

        logger.info(f"Successfully extracted and cleaned {len(cleaned_posts)} posts")
        return cleaned_posts
    except requests.RequestException as e:
        logger.error(f"Failed to fetch or parse URL: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in extract_posts: {str(e)}")
        logger.error(traceback.format_exc())
        raise
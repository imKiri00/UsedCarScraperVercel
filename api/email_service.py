from fastapi import FastAPI, HTTPException
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

@app.post("/send_email")
async def send_email_notification(subject: str, car_info: dict, to_email: str):
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT"))

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Create the email body with all car information, nicely formatted
    body = "A new car has been added:\n\n"
    body += "=" * 40 + "\n\n"  # Separator line

    for key, value in car_info.items():
        if value:  # Only include non-None values
            formatted_key = key.replace('_', ' ').title()
            if key == "post_link":
                body += f"{formatted_key}:\n{value}\n\n"
            else:
                body += f"{formatted_key}: {value}\n"

    body += "\n" + "=" * 40 + "\n"  # Separator line at the end
    body += "This is an automated notification. Please do not reply to this email."

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
        logger.info(f"Email notification sent to {to_email}")
        return {"message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
from fastapi import FastAPI, HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

app = FastAPI()
logger = logging.getLogger(__name__)
load_dotenv()

@app.post("/send_email")
async def send_email(subject: str, car_info: dict):
    try:
        from_email = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        to_email = os.getenv("NOTIFICATION_EMAIL")

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        body = "A new car has been added:\n\n"
        for key, value in car_info.items():
            if value:
                formatted_key = key.replace('_', ' ').title()
                body += f"{formatted_key}: {value}\n"

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)

        return {"message": "Email sent successfully"}
    except Exception as e:
        logger.error(f"Email error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
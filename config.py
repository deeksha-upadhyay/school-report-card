import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017/school_report_card_db"
)

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "deekshaupadhyay36@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

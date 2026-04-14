MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "2004"  # ← write your MySQL password here
MYSQL_DB = "smart_attendance"

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "adityajha1906@gmail.com"
MAIL_PASSWORD = "irfb haja dtwq faar"
MAIL_USE_TLS = True
MAIL_USE_SSL = False
ADMIN_EMAIL = "adityajha1906@gmail.com"

import os
from dotenv import load_dotenv
load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
PARENT_PHONE = os.getenv("PARENT_PHONE")


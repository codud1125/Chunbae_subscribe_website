from account import *
from imap_tools import MailBox
import smtplib
from email.message import EmailMessage
import sqlite3
import random
import csv
import datetime
import requests


today = datetime.datetime.now()

db = sqlite3.connect("website_subscriber.db")
cursor = db.cursor()

subscriber_db = []

# Setting up DB
try:
    cursor.execute("CREATE TABLE users (name varchar(250), email varchar(250) UNIQUE, zipcode varchar(250))")
    db.commit()
except:
    cursor.execute("SELECT * FROM users")
    subscriber_db = cursor.fetchall()

# Getting Quotes data
with open('positive_affirmations.csv') as csv_file:
    data = csv_file.readlines()

quote_of_the_day = random.choice(data)

# WEATHER_ENDPOINT = 'https://api.openweathermap.org/data/2.5/weather?zip={zip code},{country code}&appid={API key}'
weather_api_key = 'secret'

# Fetching emails
with MailBox("imap.gmail.com", 993).login(EMAIL_ADDRESS, EMAIL_PASSWORD, initial_folder="INBOX") as mailbox:
    for msg in mailbox.fetch('(SENTSINCE 21-Nov-2022)'):
        if "Contact Request from personal website" in msg.subject:
            text = msg.text
            name = (text[text.find('name'):text.find('email')].strip())
            email = (text[text.find('email'):text.find('zipcode')].strip())
            zipcode =(text[text.find('zipcode'):text.find('Submitted')].strip())

            name = name.split(":")[1].strip()
            email = email.split(":")[1].strip()
            zipcode = zipcode.split(":")[1].strip()
            
            try:
                cursor.execute("INSERT INTO users VALUES(?, ?, ?)", (name, email, zipcode,))
                db.commit()
                subscriber_db.append((name, email, zipcode))
            except:
                print("Duplicate email in the system")
                pass

with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.ehlo() # 연결이 잘 수립되는지 확인 
    smtp.starttls() # 모든 내용이 암호화 되어 전송 
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD) # 로그인 작업 수행

    for subscriber in subscriber_db:
        
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?zip={subscriber[2]},{"US"}&appid={weather_api_key}'

        response = requests.get(url=weather_url)
        weather_data = response.json()

        weather = weather_data['weather'][0]['main'].lower()
        city_name = weather_data['name']

        title = 'Your daily reminder from Chunbae'
        content = f"""Hi {subscriber[0]}! 👋

Today's weather in {city_name} is {weather}.

Here's a quote of the day: {quote_of_the_day}

Hope you have an amazing day today! and don't forget, it will all be okay. ❤

With love, 💌
Chunbae"""

        print(content)

        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = EMAIL_ADDRESS
        msg["to"] = subscriber[1]
        msg.set_content(content)
        smtp.send_message(msg)

from account import *
from imap_tools import MailBox
import smtplib
from email.message import EmailMessage
import sqlite3
import random
import csv
from datetime import datetime, timedelta
import requests


today = datetime.now()
yesterday = today - timedelta(days=1)

today = today.strftime('%d-%b-%Y')
yesterday = yesterday.strftime('%d-%b-%Y')

db = sqlite3.connect("website_subscriber.db")
cursor = db.cursor()

subscriber_db = []

# Setting up DB
try:
    cursor.execute("CREATE TABLE users (name varchar(250), email varchar(250) UNIQUE, zipcode varchar(250), stock varchar(250))")
    db.commit()
except:
    cursor.execute("SELECT * FROM users")
    subscriber_db = cursor.fetchall()

# Getting Quotes data
with open('positive_affirmations.csv') as csv_file:
    data = csv_file.readlines()

quote_of_the_day = random.choice(data)

# WEATHER_ENDPOINT = 'https://api.openweathermap.org/data/2.5/weather?zip={zip code},{country code}&appid={API key}'
weather_api_key = '207d9921d71382b6ff73e882a720afc7A'

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
STOCK_API_KEY = 'DLXPYGB0ZGEL39ROA'

# Fetching emails
with MailBox("imap.gmail.com", 993).login(EMAIL_ADDRESS, EMAIL_PASSWORD, initial_folder="INBOX") as mailbox:
    for msg in mailbox.fetch(f'(SENTSINCE {yesterday})'):
        if "Contact Request from personal website" in msg.subject:
            stock_list = []
            text = msg.text
            name = (text[text.find('name'):text.find('email')].strip())
            email = (text[text.find('email'):text.find('zipcode')].strip())
            zipcode =(text[text.find('zipcode')+10:text.find('zipcode')+15].strip())

            if 'AAPL' in text:
                stock_list.append('AAPL')
            if 'TSLA' in text:
                stock_list.append('TSLA')
            if 'AMZN' in text:
                stock_list.append('AMZN')
            if 'MSFT' in text:
                stock_list.append('MSFT')
            if 'QQQ' in text:
                stock_list.append('QQQ')

            name = name.split(":")[1].strip()
            email = email.split(":")[1].strip()

            stock_list = ','.join(stock_list)

            try:
                cursor.execute("INSERT INTO users VALUES(?, ?, ?, ?)", (name, email, zipcode, stock_list, ))
                db.commit()
                subscriber_db.append((name, email, zipcode, stock_list, ))
            except:
                print("Duplicate email in the system")
                pass

stock_content = {}
                
for stock in ['AAPL', 'TSLA', 'AMZN', 'MSFT', 'QQQ']:
    stock_params = {
        "function": 'TIME_SERIES_DAILY_ADJUSTED', 
        "symbol": stock,
        "apikey": STOCK_API_KEY
    }

    response = requests.get(url=STOCK_ENDPOINT, params = stock_params)
    response.raise_for_status
    stock_data = response.json()
    run = 0
    stock_price = []

    for day in stock_data['Time Series (Daily)']:
        stock_price.append(stock_data['Time Series (Daily)'][day]['4. close'])
        run += 1
        if run >= 2:
            break

    diff = float(stock_price[0]) - float(stock_price[1])
    if diff > 0:
        stock_content[stock] = f"{stock} up {round((diff/float(stock_price[0]))*100,2)}% \n\n"
    else:
        stock_content[stock] = f"{stock} down {round((diff/float(stock_price[0]))*100,2)}% \n\n"

print(stock_content)

with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
    smtp.ehlo() # 연결이 잘 수립되는지 확인 
    smtp.starttls() # 모든 내용이 암호화 되어 전송 
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD) # 로그인 작업 수행

    for subscriber in subscriber_db:
        print(subscriber)
        weather_url = f'https://api.openweathermap.org/data/2.5/weather?zip={subscriber[2]},{"US"}&appid={weather_api_key}'

        response = requests.get(url=weather_url)
        response.raise_for_status
        weather_data = response.json()

        weather = weather_data['weather'][0]['main'].lower()
        city_name = weather_data['name']

        stock_content_user = ''

        stock_list_user = subscriber[3].split(",")

        for stock in stock_list_user:
            stock_content_user += stock_content[stock]

        title = 'Your daily reminder from Chunbae'
        content = f"""Hi {subscriber[0]}! 👋

Today's weather in {city_name} is {weather}.

Here's a quote of the day: {quote_of_the_day}

{stock_content_user}
Hope you have an amazing day today! and don't forget, it will all be okay. ❤

With love, 💌
Chunbae"""

        msg = EmailMessage()
        msg["Subject"] = title
        msg["From"] = EMAIL_ADDRESS
        msg["to"] = subscriber[1]
        msg.set_content(content)
        smtp.send_message(msg)

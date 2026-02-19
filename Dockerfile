FROM python:3.11-slim

WORKDIR /app

#install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . . 

#RUN the bot
CMD [ "python", "bot.py" ]

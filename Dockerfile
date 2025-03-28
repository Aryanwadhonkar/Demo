# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables (optional, can also be set at runtime)
# ENV TELEGRAM_BOT_TOKEN=your_token
# ENV LINK_SHORTENER_API=your_api
# ENV DEV_API_KEY=your_dev_key

# Command to run the bot
CMD ["python", "bot.py"]

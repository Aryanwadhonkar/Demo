# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY bot.py .

# Set environment variables (you can also set these in your deployment environment)
ENV TELEGRAM_BOT_TOKEN=7709318237:AAE9gL7l7V9Q0ZUSUGO0XfmoS5JDMi6Km-c
ENV WEBHOOK_URL=https://latin-tracey-wleaks-9a7fe5ea.koyeb.app/7709318237:AAE9gL7l7V9Q0ZUSUGO0XfmoS5JDMi6Km-c
ENV ADMIN_IDS=1672634667

# Expose the port for the Flask app
EXPOSE 5000

# Command to run the bot
CMD ["python", "bot.py"]

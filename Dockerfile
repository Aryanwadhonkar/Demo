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
ENV TELEGRAM_BOT_TOKEN=<your_bot_token>
ENV WEBHOOK_URL=<your_webhook_url>
ENV ADMIN_IDS=<comma_separated_admin_ids>

# Expose the port for the Flask app
EXPOSE 5000

# Command to run the bot
CMD ["python", "bot.py"]

# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set environment variables (optional)
# ENV API_ID=your_api_id
# ENV API_HASH=your_api_hash
# ENV MONGODB_URL=your_mongodb_url
# ENV URL_SHORTNER=your_url_shortner_service
# ENV URL_SHORTNER_API=your_url_shortner_api_token
# ENV OWNER_ID=your_owner_id
# ENV ADMINS_ID=comma_separated_admin_ids
# ENV BOT_TOKEN=your_bot_token
# ENV PORT=8080
# ENV CHANNEL_ID=-1001234567890  # Replace with your private channel ID

# Command to run the bot
CMD ["python", "bot.py"]

# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot source code
COPY . .

# Expose the port for Flask
EXPOSE 5000

# Command to run the bot
CMD ["python", "bot.py"]

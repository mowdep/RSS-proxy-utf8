FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy application files
COPY rss_proxy.py /app/
COPY requirements.txt /app/

# Create a virtual environment and install dependencies
RUN python -m venv /app/venv \
    && /app/venv/bin/python -m pip install --no-cache-dir --upgrade pip \
    && /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Activate the virtual environment for the application
ENV PATH="/app/venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "rss_proxy.py"]


# Use Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the Streamlit app and requirements.txt
COPY streamlit_app/requirements.txt .

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit application code
COPY streamlit_app/ .

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
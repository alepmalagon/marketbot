# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Set the database URL - adjust the path as needed inside the container
ENV DATABASE_URL /data/eve_data.sqlite

# Set work directory
WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY ./app /code/app
# Optional: Copy scripts if needed inside container (e.g., for entrypoint)
# COPY ./scripts /code/scripts

# --- Option A: Copy pre-built database into image (simpler, image rebuild needed for data update) ---
# COPY ./data/eve_data.sqlite /data/eve_data.sqlite
# RUN chown -R <non-root-user>:<non-root-group> /data # If running as non-root

# --- Option B/C: Use a volume for the database (more flexible for updates) ---
# Create the data directory. The volume will be mounted here.
RUN mkdir /data
# Optional: Add entrypoint script here to run load_data.py on container start
# COPY ./entrypoint.sh /code/entrypoint.sh
# RUN chmod +x /code/entrypoint.sh
# ENTRYPOINT ["/code/entrypoint.sh"] # Runs BEFORE the CMD

# Expose port
EXPOSE 8000

# Define command to run app using Uvicorn
# Add --reload for development only
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Optional: Consider running as a non-root user for security
# RUN addgroup --system app && adduser --system --group app
# USER app
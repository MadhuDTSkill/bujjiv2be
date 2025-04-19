# Use Python 3.10 as base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the application code
COPY . .

# Install dependencies
RUN pip install -r requirements_copy.txt

# Expose the port Django runs on
EXPOSE 8000

# Command to run the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM python:3.12-slim

#Prevents Python from writing .pyc files to disk not creating __pycache__ directories, which can save disk space and reduce clutter in the application directory.
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


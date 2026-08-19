# Use an official Python runtime as a parent image
FROM python:3.10-slim
LABEL maintainer="amos@dclmca.onmicrosoft.com"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependencies, app code, and the contrib folder
COPY ./requirements.txt /requirements.txt
COPY ./app /app
WORKDIR /app

# Expose application port
EXPOSE 80

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget xfonts-base xfonts-75dpi fontconfig libjpeg62-turbo libxrender1 \
    netcat-openbsd && \
    wget -q https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.bookworm_amd64.deb && \
    apt-get install -y ./wkhtmltox_0.12.6.1-3.bookworm_amd64.deb && \
    rm wkhtmltox_0.12.6.1-3.bookworm_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install -r /requirements.txt


CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py migrate && python manage.py collectstatic --no-input && gunicorn core.wsgi:application --bind 0.0.0.0:80 --workers 2 --threads 4"]



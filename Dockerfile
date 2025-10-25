# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 user
USER user

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "App.wsgi:app"]
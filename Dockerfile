# Example Dockerfile

FROM python:3.11-slim

WORKDIR /app

COPY ./app /app/app
COPY requirements.txt /app/
COPY .env /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

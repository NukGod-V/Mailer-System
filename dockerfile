FROM python:3.11-alpine

RUN apk add --no-cache gcc musl-dev mariadb-connector-c-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD [ "python", "app.py" ]
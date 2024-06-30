FROM python:3
WORKDIR /app
COPY requirements.txt /app
COPY data/locations.json /app
COPY data/open-meteo-2016-2024.csv /app
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app
ENTRYPOINT ["python3"]
CMD ["producer.py", "--locations", "./data/locations.json", "--data_source", "csv", "--csv_path", "./data/open-meteo-2016-2024.csv", "--loop", "--kafka_broker_address", "kafka"]

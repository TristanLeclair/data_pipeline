FROM python:3
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt --no-cache-dir
COPY . /app
ENTRYPOINT ["python3"]
CMD ["transformer_i18n.py", "--kafka_broker_address", "kafka"]

FROM python:latest
WORKDIR /opt
COPY exporter.py .
COPY config.yml .
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python3","-u","exporter.py"]

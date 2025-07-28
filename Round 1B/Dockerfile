FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y     build-essential     && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt     && python -m spacy download en_core_web_sm

CMD ["python", "document_analyzer.py"]

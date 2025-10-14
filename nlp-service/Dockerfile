FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy Italian model directly from the correct URL
RUN pip install https://github.com/explosion/spacy-models/releases/download/it_core_news_lg-3.7.0/it_core_news_lg-3.7.0-py3-none-any.whl

COPY . .

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]

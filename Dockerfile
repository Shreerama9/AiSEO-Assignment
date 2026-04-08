FROM python:3.11-slim AS deps

WORKDIR /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/pkg -r requirements.txt
RUN python -m spacy download en_core_web_sm --target /pkg/lib/python3.11/site-packages


FROM python:3.11-slim AS runtime

WORKDIR /app
COPY --from=deps /pkg /usr/local
COPY . .

# Uncomment to bake the embedding model into the image (larger image, no cold-start):
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

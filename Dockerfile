# SkillPath hosted demo: the web app and the API in one container (see deploy/server.py and DEPLOY.md).

# 1. Build the web app, pointed at the same server's /api and with the demo notice switched on.
FROM node:24-slim AS web
WORKDIR /app
COPY app/package.json app/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY app/ ./
ENV EXPO_PUBLIC_API_URL=/api \
    EXPO_PUBLIC_DEMO=1
RUN npx expo export --platform web --output-dir dist

# 2. The API, with the CV reader's model baked in so the demo never downloads it at runtime.
FROM python:3.13-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt
COPY skillpath/ skillpath/
COPY api/ api/
COPY data/ data/
COPY deploy/ deploy/
RUN python -c "from skillpath.cv import FastEmbedder; FastEmbedder()"
COPY --from=web /app/dist web/

# One thread and small batches keep the CV reader within a 512 MB free instance (same model, same scores).
ENV SKILLPATH_DEMO=1 \
    SKILLPATH_DB=/tmp/skillpath-demo.db \
    SKILLPATH_CV_THREADS=1 \
    SKILLPATH_CV_BATCH=32 \
    PORT=10000
EXPOSE 10000
CMD ["sh", "-c", "uvicorn deploy.server:site --host 0.0.0.0 --port ${PORT}"]

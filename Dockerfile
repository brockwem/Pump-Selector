FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY app /app/app
COPY sample_data /app/sample_data
ENV HOST=0.0.0.0
ENV PORT=8080
ENV DATA_DIR=/app/sample_data
ENV CURVEPACK_VERSION=curvepack_demo_2025-07-28
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]

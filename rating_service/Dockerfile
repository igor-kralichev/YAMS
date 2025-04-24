FROM python:3.10-slim

WORKDIR /YAMS
ENV PYTHONPATH="${PYTHONPATH}:/YAMS"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./rating_service ./rating_service
COPY ./shared ./shared
COPY ./static ./static

CMD ["uvicorn", "rating_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
FROM python:3.10-slim

WORKDIR /YAMS
ENV PYTHONPATH="${PYTHONPATH}:/YAMS"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./deal_service ./deal_service
COPY ./shared ./shared
COPY ./static ./static

CMD ["uvicorn", "deal_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
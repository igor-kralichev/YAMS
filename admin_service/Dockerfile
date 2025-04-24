FROM python:3.10-slim

WORKDIR /YAMS
ENV PYTHONPATH="${PYTHONPATH}:/YAMS"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./admin_service ./admin_service
COPY ./shared ./shared

CMD ["uvicorn", "admin_service.app.main:app", "--host", "0.0.0.0", "--port", "8005"]
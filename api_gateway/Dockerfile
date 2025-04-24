FROM python:3.10-slim

WORKDIR /YAMS
ENV PYTHONPATH="${PYTHONPATH}:/YAMS"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./api_gateway ./api_gateway
COPY ./shared ./shared

CMD ["uvicorn", "api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
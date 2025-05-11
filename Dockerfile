FROM python:3.12-slim

RUN useradd -m appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown appuser:appuser /app
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV YANDEX_MAPS_API_KEY="6ad7e365-54e3-4482-81b5-bd65125aafbf"
EXPOSE 5000
USER appuser
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
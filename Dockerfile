FROM python:3.10.6-buster
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn==20.1.0
EXPOSE 8080
CMD ["gunicorn", "--workers=4", "--worker-tmp-dir=/dev/shm", "--error-logfile=-", "--bind=0.0.0.0:8080", "wsgi:app"]

# 3.14.6-slim-trixie
FROM python@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn==26.0.0

# Create non-root user to run application
RUN adduser --system --no-create-home flask-runner
USER flask-runner

EXPOSE 8080
CMD ["gunicorn", "--workers=4", "--worker-tmp-dir=/dev/shm", "--error-logfile=-", "--bind=0.0.0.0:8080", "wsgi:app"]

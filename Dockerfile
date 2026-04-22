# 3.14.4-slim-trixie
FROM python@sha256:5c9b9aeee369d854acd666375ebb2a9a45a8ac9d264973bed69dbb28cf48f648

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn==25.1.0

# Create non-root user to run application
RUN adduser --system --no-create-home flask-runner
USER flask-runner

EXPOSE 8080
CMD ["gunicorn", "--workers=4", "--worker-tmp-dir=/dev/shm", "--error-logfile=-", "--bind=0.0.0.0:8080", "wsgi:app"]

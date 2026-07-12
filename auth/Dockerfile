FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY auth/ /app/
EXPOSE 50051
CMD ["python", "main.py"]

FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY datatransf/ /app/
EXPOSE 50053 8000
CMD ["python", "main.py"]

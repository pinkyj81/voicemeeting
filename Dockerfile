FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV DEBUG=False
ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["python", "app.py"]

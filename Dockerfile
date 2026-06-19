FROM python:3.12-slim

WORKDIR /app

# Install ODBC dependencies for pyodbc and SQL Server connectivity
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    gnupg2 \
    curl \
    apt-transport-https \
    ca-certificates \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV DEBUG=False
ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["python", "app.py"]

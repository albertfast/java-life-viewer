FROM python:3.10-slim

# Install Java
RUN apt-get update && apt-get install -y \
    default-jre \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Compile Java files
RUN cd /app/java && javac *.java

EXPOSE 8000

CMD ["python", "backend.py"]

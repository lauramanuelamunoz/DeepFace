FROM python:3.10-slim

WORKDIR /app

# Dependencias del sistema necesarias para OpenCV y DeepFace
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Hugging Face Spaces usa el puerto 7860
EXPOSE 7860

CMD ["gunicorn", "App:app", "--bind", "0.0.0.0:7860", "--timeout", "180", "--workers", "1", "--threads", "2"]

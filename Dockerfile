# syntax=docker/dockerfile:1

# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Evita ficheros .pyc y fuerza salida sin buffer (mejor para logs de EB/CloudWatch)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instala uv (gestor de dependencias)
RUN pip install --no-cache-dir uv

# Directorio de trabajo temporal para la instalacion
WORKDIR /app

# Copia primero el manifiesto de dependencias para aprovechar la cache de capas
COPY backend/pyproject.toml ./backend/

# Instala las dependencias del proyecto en el entorno del sistema usando uv
RUN uv pip install --system --no-cache -r backend/pyproject.toml

# Copia el codigo del backend
COPY backend/ ./backend/

# Directorio de trabajo final: permite que "from app.main" resuelva correctamente
WORKDIR /app/backend

# Puerto esperado por Elastic Beanstalk
EXPOSE 8080

# Arranque del backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

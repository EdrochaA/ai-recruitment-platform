# syntax=docker/dockerfile:1

# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Evita ficheros .pyc y fuerza salida sin buffer (mejor para logs de EB/CloudWatch)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Instala uv (gestor de dependencias)
RUN pip install --no-cache-dir uv

# Directorio de trabajo final: permite que "from app.main" resuelva correctamente
WORKDIR /app/backend

# Copia primero el manifiesto de dependencias para aprovechar la cache de capas
COPY pyproject.toml ./

RUN uv pip install --system --no-cache .

# Copia el resto del codigo del backend
COPY . .

# Puerto esperado por Elastic Beanstalk
EXPOSE 8080

# Arranque del backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
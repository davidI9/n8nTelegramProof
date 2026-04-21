# Usamos la imagen oficial de python-slim
FROM python:3.11-slim

# Copiamos uv desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Variables de entorno básicas de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Copiamos solo los archivos de configuración
COPY pyproject.toml uv.lock ./

# 2. Sincronizamos dependencias. 
# Esto creará automáticamente una carpeta oculta /app/.venv
RUN uv sync --frozen --no-install-project --no-dev

# 3. Copiamos el código
COPY . .

# 4. Instalamos el proyecto
RUN uv sync --frozen --no-dev

# 5. ¡LA MAGIA! Añadimos el entorno virtual de uv al PATH del sistema.
# Así, cualquier comando de Python (como uvicorn) usará este entorno por defecto.
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Como el PATH ya está actualizado, ejecutamos uvicorn directamente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
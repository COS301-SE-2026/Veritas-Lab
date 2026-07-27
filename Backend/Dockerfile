FROM python:3.12-slim AS builder

WORKDIR /app

# System dependencies required by pyexiftool, python-magic and opencv
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libmagic1 \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    --only-binary=:all: \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt


FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system dependencies
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libmagic1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages

COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY . .

RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
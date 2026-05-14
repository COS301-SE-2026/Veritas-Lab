FROM python:3.12-slim AS builder

WORKDIR /app

#system dependencies required by pyexiftool python-magic and opencv -- last one is for when we install all the ML python packages
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

#install PyTorch first on its own layer so Docker cache is not busted every time code changes
# will do this when we start the ML implementations
# RUN pip install --no-cache-dir \
#     torch torchvision torchaudio \
#     --index-url https://download.pytorch.org/whl/cpu

#install remaining Python dependencies adapt to prod when we finish all installs
# COPY requirements/prod.txt .
# RUN pip install --no-cache-dir -r prod.txt
COPY requirements/base.txt .
RUN pip install --no-cache-dir -r base.txt

FROM python:3.12-slim AS runtime

WORKDIR /app

#runtime system dependencies
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libmagic1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

#copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages \
                    /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

#copy app code
COPY . .

EXPOSE 8000

#uvicorn runs the fastapi app
#0.0.0.0 means it can be accessed outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
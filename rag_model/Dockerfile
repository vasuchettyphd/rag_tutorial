# 1) Use an NVIDIA CUDA base image that includes CUDA 11.6
FROM nvidia/cuda:11.6.2-cudnn8-runtime-ubuntu20.04

# 2) Install system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        python3 \
        python3-dev \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Optional: symlink python3 -> python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# 3) Copy your requirements file
WORKDIR /app
COPY streamlit_app/requirements.txt ./

# 4) Install GPU-enabled PyTorch & other Python packages
# For PyTorch 1.13.1 compiled for CUDA 11.6:
RUN pip install torch==1.13.1+cu116 torchvision==0.14.1+cu116 \
    --extra-index-url https://download.pytorch.org/whl/cu116 && \
    pip install -r requirements.txt

# 5) Copy the rest of your app code
COPY streamlit_app/ ./

# 6) Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
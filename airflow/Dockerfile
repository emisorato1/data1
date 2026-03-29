# =============================================================================
# Custom Airflow Image for Enterprise AI Platform
# =============================================================================
# Base: Official Apache Airflow 3.1.7
# Adds: Dependencies for RAG indexing pipeline (psycopg, PyMuPDF, etc.)
# =============================================================================

FROM apache/airflow:3.1.7

USER root

# Install system dependencies required by PyMuPDF and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmupdf-dev \
    mupdf-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy Python requirements and install
COPY airflow/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy enterprise-ai-platform source code and install as package
# This makes src.infrastructure.rag.* modules available to DAGs
# Build context is the repo root, so we can copy src/ and pyproject.toml
COPY --chown=airflow:root src /opt/airflow/enterprise-ai-platform/src
COPY --chown=airflow:root pyproject.toml /opt/airflow/enterprise-ai-platform/pyproject.toml
WORKDIR /opt/airflow/enterprise-ai-platform
RUN pip install --no-cache-dir -e .

# Pre-cache tiktoken encodings (cl100k_base) to avoid runtime downloads
# Required by AdaptiveChunker for token counting
# Without this, tiktoken tries to download from openaipublic.blob.core.windows.net
# which is unreachable from GKE pods behind Cloud NAT
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base'); print('✓ tiktoken cl100k_base cached!')"

# Verify all dependencies including enterprise-ai-platform modules and tiktoken cache
# Skip full verification because some modules require runtime env vars (JWT_SECRET, etc.)
RUN python -c "import psycopg; import fitz; import docx; from langchain_text_splitters import RecursiveCharacterTextSplitter; import tiktoken; enc = tiktoken.get_encoding('cl100k_base'); assert len(enc.encode('test')) > 0; from google.cloud import storage; import src.infrastructure.rag; print('✓ All dependencies installed successfully!')"

# Reset working directory
WORKDIR /opt/airflow

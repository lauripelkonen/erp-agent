# Multi-stage build optimized for speed
FROM python:3.11-slim AS builder

# Install only essential build dependencies including unixODBC headers
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy production requirements and install dependencies
COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install minimal runtime dependencies including unixODBC runtime and SQL Server drivers
RUN apt-get update && apt-get install -y \
    libodbc2 \
    unixodbc \
    curl \
    openconnect \
    iptables \
    procps \
    gnupg2 \
    wget \
    ca-certificates \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && (ACCEPT_EULA=Y apt-get install -y msodbcsql18 msodbcsql17 2>&1 || echo "Microsoft ODBC drivers not available for this architecture, skipping...") || true \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install FreeTDS for legacy "SQL Server" driver compatibility (what works locally!)
# Detect architecture dynamically for library paths
RUN apt-get update && apt-get install -y \
    freetds-dev \
    freetds-bin \
    tdsodbc \
    && ARCH=$(dpkg --print-architecture) \
    && LIB_DIR="/usr/lib/${ARCH}-linux-gnu" \
    && echo "[SQL Server]" >> /etc/odbcinst.ini \
    && echo "Description=FreeTDS Driver for SQL Server" >> /etc/odbcinst.ini \
    && echo "Driver=${LIB_DIR}/odbc/libtdsodbc.so" >> /etc/odbcinst.ini \
    && echo "Setup=${LIB_DIR}/odbc/libtdsS.so" >> /etc/odbcinst.ini \
    && echo "FileUsage=1" >> /etc/odbcinst.ini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configure FreeTDS properly based on Stack Overflow solutions
# Create freetds.conf
RUN echo "[global]" > /etc/freetds/freetds.conf \
    && echo "        tds version = 7.2" >> /etc/freetds/freetds.conf \
    && echo "        client charset = UTF-8" >> /etc/freetds/freetds.conf \
    && echo "        text size = 2147483647" >> /etc/freetds/freetds.conf \
    && echo "        timeout = 30" >> /etc/freetds/freetds.conf \
    && echo "        connect timeout = 30" >> /etc/freetds/freetds.conf \
    && echo "" >> /etc/freetds/freetds.conf \
    && echo "[lemondb]" >> /etc/freetds/freetds.conf \
    && echo "        host = 10.201.164.123" >> /etc/freetds/freetds.conf \
    && echo "        port = 1433" >> /etc/freetds/freetds.conf \
    && echo "        tds version = 7.2" >> /etc/freetds/freetds.conf \
    && echo "        database = LemonDB16" >> /etc/freetds/freetds.conf

# Update odbcinst.ini with proper FreeTDS configuration
# Use architecture detection for library paths
RUN ARCH=$(dpkg --print-architecture) \
    && LIB_DIR="/usr/lib/${ARCH}-linux-gnu" \
    && echo "" >> /etc/odbcinst.ini \
    && echo "[FreeTDS]" >> /etc/odbcinst.ini \
    && echo "Description=FreeTDS Driver v0.91" >> /etc/odbcinst.ini \
    && echo "Driver=${LIB_DIR}/odbc/libtdsodbc.so" >> /etc/odbcinst.ini \
    && echo "Setup=${LIB_DIR}/odbc/libtdsS.so" >> /etc/odbcinst.ini \
    && echo "fileusage=1" >> /etc/odbcinst.ini \
    && echo "dontdlclose=1" >> /etc/odbcinst.ini \
    && echo "UsageCount=1" >> /etc/odbcinst.ini

# Create odbc.ini (missing from our previous setup!)
RUN echo "[lemondb_dsn]" > /etc/odbc.ini \
    && echo "Driver=FreeTDS" >> /etc/odbc.ini \
    && echo "Description=Lemon Database" >> /etc/odbc.ini \
    && echo "Trace=No" >> /etc/odbc.ini \
    && echo "ServerName=lemondb" >> /etc/odbc.ini \
    && echo "Database=LemonDB16" >> /etc/odbc.ini \
    && echo "TDS_Version=7.2" >> /etc/odbc.ini

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/app/.local

# Copy only needed folders
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY docker/ ./docker/

# Create data directory for JSON backup storage
RUN mkdir -p /app/data && chown app:app /app/data

# Fix line endings for shell scripts (Windows CRLF -> Unix LF) and set proper permissions
RUN apt-get update && apt-get install -y dos2unix && \
    dos2unix docker/entrypoint.sh && \
    apt-get remove -y dos2unix && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R app:app /app && \
    chmod +x docker/entrypoint.sh

# Add local bin to PATH and explicit PYTHONPATH for user packages
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/app:/app/src:/home/app/.local/lib/python3.11/site-packages

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/offer-agent/health || exit 1

# Expose port
EXPOSE 8080

# Entry point
ENTRYPOINT ["./docker/entrypoint.sh"] 
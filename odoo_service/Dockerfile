FROM odoo:18

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for custom modules
RUN pip3 install --no-cache-dir --break-system-packages \
    requests \
    python-dotenv \
    PyPDF2 \
    python-docx \
    beautifulsoup4

# Switch back to odoo user
USER odoo

# Set working directory
WORKDIR /var/lib/odoo

# Expose Odoo port
EXPOSE 8069

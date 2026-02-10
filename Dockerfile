FROM node:20-slim

# Install Python3 and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies
COPY package.json ./
RUN npm install --production

# Install Python dependencies
RUN pip3 install pypdf reportlab --break-system-packages

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Start the server
CMD ["node", "server.js"]

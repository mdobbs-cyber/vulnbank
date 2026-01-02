# Build Stage
FROM node:22-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
# Set registry to default and increase timeout for reliability
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retry-maxtimeout 600000 && \
    npm config set fetch-retry-mintimeout 10000 && \
    npm install --verbose

COPY frontend ./
RUN npm run build

# Runtime Stage
FROM python:3.9-slim
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend .

# Copy built frontend assets
COPY --from=build /app/dist /app/frontend_dist

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

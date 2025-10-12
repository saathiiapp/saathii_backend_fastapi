# Saathii API Documentation Deployment

This directory contains the Docker setup for deploying the Saathii Backend API documentation as a web service.

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and start the documentation service
docker-compose -f docker-compose.docs.yml up -d

# View logs
docker-compose -f docker-compose.docs.yml logs -f

# Stop the service
docker-compose -f docker-compose.docs.yml down
```

### Option 2: Using Docker directly

```bash
# Build the documentation image
docker build -f Dockerfile.docs -t saathii-api-docs .

# Run the container
docker run -d -p 8080:80 --name saathii-api-docs saathii-api-docs

# View logs
docker logs -f saathii-api-docs

# Stop and remove
docker stop saathii-api-docs
docker rm saathii-api-docs
```

## 📖 Access the Documentation

Once deployed, the documentation will be available at:

- **Local**: http://localhost:8080
- **Health Check**: http://localhost:8080/health

## 🔧 Configuration

### Port Configuration
The default port is `8080`. To change it, modify the `ports` section in `docker-compose.docs.yml`:

```yaml
ports:
  - "YOUR_PORT:80"
```

### Nginx Configuration
The nginx configuration is in `nginx-docs.conf` and includes:
- Gzip compression
- Static file caching
- Security headers
- CORS support
- Health check endpoint

### Environment Variables
No environment variables are required for basic operation.

## 🏗️ Production Deployment

### Using Traefik (Optional)
The docker-compose file includes Traefik labels for reverse proxy setup:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.docs.rule=Host(`docs.localhost`)"
  - "traefik.http.routers.docs.entrypoints=web"
```

### Using Custom Domain
To use a custom domain, update the Traefik rule:

```yaml
- "traefik.http.routers.docs.rule=Host(`docs.yourdomain.com`)"
```

## 📁 File Structure

```
.
├── api_documentation.html    # Main documentation file
├── Dockerfile.docs          # Docker image definition
├── nginx-docs.conf          # Nginx configuration
├── docker-compose.docs.yml  # Docker Compose configuration
├── .dockerignore           # Docker ignore file
└── README-DOCS.md          # This file
```

## 🔍 Health Monitoring

The service includes a health check endpoint at `/health` that returns:
- Status: `200 OK`
- Response: `healthy`

## 🛠️ Troubleshooting

### Container won't start
```bash
# Check container logs
docker logs saathii-api-docs

# Check if port is already in use
lsof -i :8080
```

### Documentation not loading
```bash
# Check nginx configuration
docker exec saathii-api-docs nginx -t

# Restart nginx
docker exec saathii-api-docs nginx -s reload
```

### Permission issues
```bash
# Check file permissions
ls -la api_documentation.html

# Fix permissions if needed
chmod 644 api_documentation.html
```

## 🔄 Updates

To update the documentation:

1. Modify `api_documentation.html`
2. Rebuild the container:
   ```bash
   docker-compose -f docker-compose.docs.yml up -d --build
   ```

## 📊 Performance

The nginx configuration includes:
- Gzip compression for faster loading
- Static file caching (1 year for assets)
- Optimized headers for better performance

## 🔒 Security

The nginx configuration includes security headers:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Referrer-Policy

## 📝 Notes

- The documentation is served as a static HTML file
- No database or backend services are required
- The container is lightweight (~15MB base image)
- Perfect for hosting on any Docker-compatible platform

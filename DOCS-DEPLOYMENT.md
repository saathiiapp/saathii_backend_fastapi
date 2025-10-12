# Saathii Documentation Deployment

This guide explains how to deploy the Saathii Backend API documentation using Docker Compose.

## 🚀 Quick Deployment

### Deploy Documentation Only

```bash
# Deploy just the documentation
./deploy-docs.sh
```

### Deploy Everything (API + Docs)

```bash
# Deploy both API and documentation
docker-compose up -d
```

## 📁 Project Structure

```
saathii_backend_fastapi/
├── docker-compose.yml          # Main Docker Compose file
├── deploy-docs.sh              # Documentation deployment script
├── docs/                       # Documentation source
│   ├── Dockerfile.docs         # Documentation Docker image
│   ├── nginx.conf              # Nginx configuration
│   ├── docusaurus.config.ts    # Docusaurus configuration
│   └── docs/                   # Documentation content
└── DOCS-DEPLOYMENT.md          # This file
```

## 🌐 URLs

After deployment, the following URLs will be available:

- **Documentation**: https://docs.saathiiapp.com
- **API Swagger UI**: https://saathiiapp.com/docs
- **API ReDoc**: https://saathiiapp.com/redoc
- **Traefik Dashboard**: http://your-server:8080

## 🛠️ Manual Deployment

### 1. Build Documentation

```bash
cd docs
npm install
npm run build
```

### 2. Build Docker Image

```bash
docker-compose build docs
```

### 3. Start Services

```bash
# Start documentation only
docker-compose up -d docs

# Or start everything
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

The documentation uses the following configuration:

- **Documentation URL**: `https://docs.saathiiapp.com`
- **API URL**: `https://saathiiapp.com`
- **SSL**: Automatic Let's Encrypt certificates
- **Traefik**: Reverse proxy with automatic HTTPS

### Traefik Labels

The documentation service includes the following Traefik labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.docs.rule=Host(`docs.saathiiapp.com`)"
  - "traefik.http.routers.docs.entrypoints=websecure"
  - "traefik.http.routers.docs.tls.certresolver=myresolver"
  - "traefik.http.routers.docs-http.rule=Host(`docs.saathiiapp.com`)"
  - "traefik.http.routers.docs-http.entrypoints=web"
  - "traefik.http.routers.docs-http.middlewares=redirect-to-https"
  - "traefik.http.services.docs.loadbalancer.server.port=80"
```

## 📊 Monitoring

### Check Service Status

```bash
# Check all services
docker-compose ps

# Check documentation service only
docker-compose ps docs
```

### View Logs

```bash
# View documentation logs
docker-compose logs docs

# Follow logs in real-time
docker-compose logs -f docs
```

### Restart Services

```bash
# Restart documentation
docker-compose restart docs

# Restart everything
docker-compose restart
```

## 🔄 Updates

### Update Documentation

1. **Make changes** to the documentation in the `docs/` directory
2. **Rebuild and redeploy**:
   ```bash
   ./deploy-docs.sh
   ```

### Update API URLs

If your API URL changes, update the following files:

1. `docs/docusaurus.config.ts` - Update navbar and footer links
2. `docs/src/components/SwaggerUI.tsx` - Update default Swagger UI URL
3. `docs/docs/api/swagger-ui.md` - Update embedded Swagger UI URL
4. `docs/docs/guides/react-native-integration.md` - Update code examples

## 🐛 Troubleshooting

### Common Issues

#### 1. Documentation Not Loading

```bash
# Check if service is running
docker-compose ps docs

# Check logs
docker-compose logs docs

# Restart service
docker-compose restart docs
```

#### 2. SSL Certificate Issues

```bash
# Check Traefik logs
docker-compose logs traefik

# Verify Let's Encrypt storage
ls -la letsencrypt/
```

#### 3. Build Failures

```bash
# Clean build
docker-compose build --no-cache docs

# Check build logs
docker-compose build docs
```

### Debug Mode

```bash
# Run documentation in debug mode
docker-compose up docs

# Check container logs
docker logs saathiiapp_docs_1
```

## 🔒 Security

### SSL/TLS

- **Automatic HTTPS**: Traefik automatically handles SSL certificates
- **Let's Encrypt**: Free SSL certificates with automatic renewal
- **HTTP Redirect**: All HTTP traffic is redirected to HTTPS

### Access Control

- **Public Access**: Documentation is publicly accessible
- **API Access**: API endpoints require authentication
- **Rate Limiting**: Configured at the API level

## 📈 Performance

### Nginx Configuration

The documentation uses Nginx with the following optimizations:

- **Gzip Compression**: Enabled for text files
- **Static File Caching**: 1-year cache for assets
- **Security Headers**: XSS protection, content type sniffing prevention
- **Client-side Routing**: Proper handling of SPA routing

### Monitoring

- **Health Check**: Available at `/health` endpoint
- **Logs**: Accessible via `docker-compose logs`
- **Metrics**: Traefik provides built-in metrics

## 🚀 Production Deployment

### Prerequisites

1. **Domain Setup**: Ensure `docs.saathiiapp.com` points to your server
2. **Docker**: Install Docker and Docker Compose
3. **Traefik**: Already configured in the main docker-compose.yml
4. **SSL**: Let's Encrypt certificates will be automatically generated

### Deployment Steps

1. **Clone Repository**:
   ```bash
   git clone https://github.com/saathii/saathii-backend-api.git
   cd saathii-backend-api
   ```

2. **Deploy Documentation**:
   ```bash
   ./deploy-docs.sh
   ```

3. **Verify Deployment**:
   - Visit https://docs.saathiiapp.com
   - Check that Swagger UI loads correctly
   - Verify all links work

## 📞 Support

If you encounter issues:

1. **Check Logs**: `docker-compose logs docs`
2. **Verify Configuration**: Check Traefik labels and routing
3. **Test Locally**: Run `npm start` in the docs directory
4. **GitHub Issues**: [Report issues](https://github.com/saathii/saathii-backend-api/issues)

---

**Happy Documenting! 📚✨**

---
sidebar_position: 1
title: Installation Guide
description: Step-by-step installation guide for the Saathii Backend API
---

# Installation Guide

This guide will walk you through installing and setting up the Saathii Backend API on your local development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 12+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis 6+** - [Download Redis](https://redis.io/download)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Optional Prerequisites

- **Docker** - [Download Docker](https://www.docker.com/get-started) (for containerized deployment)
- **Node.js 16+** - [Download Node.js](https://nodejs.org/) (for documentation)

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/saathii/saathii-backend-api.git

# Navigate to the project directory
cd saathii-backend-api
```

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Step 4: Database Setup

### Install PostgreSQL

**Windows:**
1. Download PostgreSQL installer from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the setup wizard
3. Remember the password you set for the `postgres` user

**macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu/Debian):**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE saathii;

# Create user (optional)
CREATE USER saathii_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE saathii TO saathii_user;

# Exit PostgreSQL
\q
```

## Step 5: Redis Setup

### Install Redis

**Windows:**
1. Download Redis from [GitHub releases](https://github.com/microsoftarchive/redis/releases)
2. Extract and run `redis-server.exe`

**macOS:**
```bash
# Using Homebrew
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Verify Redis Installation

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

## Step 6: Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL="postgresql://saathii_user:your_password@localhost/saathii"

# Redis Configuration
REDIS_URL="redis://localhost:6379"

# JWT Configuration
JWT_SECRET_KEY="your-super-secret-key-here-change-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# AWS S3 Configuration (Optional)
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="us-east-1"
S3_BUCKET_NAME="your-s3-bucket-name"

# Server Configuration
HOST="0.0.0.0"
PORT="8000"
DEBUG="true"
```

## Step 7: Database Migration

```bash
# Run database migrations
python -m alembic upgrade head
```

If you don't have Alembic set up, the application will create tables automatically on first run.

## Step 8: Start the Server

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 9: Verify Installation

Open your browser and navigate to:

- **API Documentation**: https://saathiiapp.com/docs
- **ReDoc Documentation**: https://saathiiapp.com/redoc
- **API Base URL**: https://saathiiapp.com
- **WebSocket**: wss://saathiiapp.com

You should see the Swagger UI with all available endpoints.

## Docker Installation (Alternative)

If you prefer using Docker:

### 1. Install Docker

Follow the [Docker installation guide](https://docs.docker.com/get-docker/) for your platform.

### 2. Use Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access the Application

- **API Base URL**: https://saathiiapp.com
- **API Documentation**: https://saathiiapp.com/docs
- **ReDoc Documentation**: https://saathiiapp.com/redoc
- **WebSocket**: wss://saathiiapp.com
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL if not running
sudo systemctl start postgresql

# Check if database exists
psql -U postgres -l
```

#### 2. Redis Connection Error

**Error:** `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
sudo systemctl start redis-server
# or
brew services start redis
```

#### 3. Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### 4. Permission Denied

**Error:** `Permission denied: '/path/to/venv'`

**Solution:**
```bash
# Fix permissions
chmod -R 755 venv/

# Or recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Issues

#### 1. Python Version

**Error:** `Python 3.8+ is required`

**Solution:**
```bash
# Check Python version
python --version

# Install correct Python version
# On macOS with Homebrew:
brew install python@3.9

# On Ubuntu:
sudo apt install python3.9 python3.9-venv
```

#### 2. Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Next Steps

After successful installation:

1. **Configure Environment**: Set up your environment variables
2. **Test API**: Try the API endpoints using the Swagger UI
3. **Set up S3**: Configure AWS S3 for file uploads (optional)
4. **Deploy**: Follow the [deployment guide](./react-native-authentication) for production setup

## Getting Help

If you encounter issues:

1. **Check Logs**: Look at the server logs for error messages
2. **Verify Prerequisites**: Ensure all required software is installed
3. **Check Configuration**: Verify your environment variables
4. **GitHub Issues**: [Report issues](https://github.com/saathii/saathii-backend-api/issues)
5. **Discussions**: [Ask questions](https://github.com/saathii/saathii-backend-api/discussions)

## Production Considerations

For production deployment:

1. **Use Environment Variables**: Never hardcode sensitive information
2. **Use Production Database**: Use a managed PostgreSQL service
3. **Use Production Redis**: Use a managed Redis service
4. **Enable SSL**: Use HTTPS in production
5. **Set up Monitoring**: Implement logging and monitoring
6. **Use Process Manager**: Use PM2 or similar for process management

---

Ready to start developing? Check out the [API Documentation](../api/authentication) to learn about the available endpoints!

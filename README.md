# Lunch App Production Backend

This is the production-ready backend for the Lunch App, designed for scalable deployment on AWS using Docker.

## Features
- FastAPI backend for lunch poll management
- Slack integration for DM-based polling and QR code delivery
- MongoDB for persistent storage
- Production-ready Dockerfile
- Environment variable-based configuration

## Directory Structure
```
lunch_app_prod/
├── backend/
│   ├── server_dm_polls.py
│   └── requirements.txt
├── Dockerfile
├── .env.example
├── README.md
```

## Environment Variables
Copy `.env.example` to `.env` and fill in your production values:
- `MONGODB_URI` - MongoDB connection string
- `DB_NAME` - MongoDB database name
- `SLACK_BOT_TOKEN` - Slack bot token
- `SLACK_CHANNEL_ID` - Slack channel ID for lunch polls

## Docker Usage
Build and run the container:
```bash
docker build -t lunch-app-backend .
docker run --env-file .env -p 8000:8000 lunch-app-backend
```

## AWS Deployment
- Use ECS, EKS, or EC2 with Docker support
- Set environment variables via AWS Secrets Manager or ECS task definition
- Use a managed MongoDB (e.g., DocumentDB, Atlas) or a separate container with persistent storage
- Expose port 8000 via a load balancer

## Health Check
- Endpoint: `/api/health`

## Notes
- No test/demo/frontend code is included
- All configuration is via environment variables
- For support, see the main project documentation 
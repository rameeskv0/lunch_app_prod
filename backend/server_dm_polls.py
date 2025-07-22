from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import logging
import uuid
import qrcode
import io
import base64
import json
import hashlib
import hmac
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import bcrypt
import re
import html
import uvicorn
from contextlib import asynccontextmanager
import asyncio
import requests
# Using built-in timezone support instead of pytz

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables for proper startup"""
    required_vars = ['MONGODB_URI', 'SLACK_BOT_TOKEN', 'SLACK_CHANNEL_ID']
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        logger.warning(f"⚠️  Warning: Missing environment variables: {missing}")
        logger.warning("Server will start but some features may not work properly")
        return False
    
    # Validate Slack token format
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    if slack_token and not slack_token.startswith('xoxb-'):
        logger.warning("⚠️  Warning: SLACK_BOT_TOKEN format may be incorrect. Should start with 'xoxb-'")
    
    logger.info("✅ Environment validation passed")
    return True

# Validate environment before proceeding
validate_environment()

# MongoDB connection with resilience
mongo_url = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'lunch_app')

client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,
    serverSelectionTimeoutMS=5000,
    retryWrites=True,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000
)
db = client[db_name]

# Slack client
slack_client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
SLACK_CHANNEL_ID = os.environ.get('SLACK_CHANNEL_ID')

# Security
security = HTTPBearer()

# ============== MODELS ==============

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slack_user_id: str
    username: str
    real_name: str
    email: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DMPoll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date  # Poll for this date's lunch
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, completed
    total_responses: int = 0
    yes_responses: int = 0
    additional_responses: int = 0

class DMResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    poll_id: str
    user_id: str
    slack_user_id: str
    username: str
    real_name: str
    response_type: str  # "yes", "additional" (no "no" stored)
    additional_count: Optional[int] = None  # For additional lunch responses
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    qr_code: Optional[str] = None
    qr_token: Optional[str] = None
    qr_sent: bool = False

class ConversationState(BaseModel):
    user_id: str
    state: str  # "waiting_response", "waiting_count", "completed"
    poll_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class QRScan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dm_response_id: str
    user_id: str
    slack_user_id: str
    username: str
    scanned_by: str
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    poll_date: date
    scan_number: int = 1  # For multi-use QRs
    total_scans_allowed: int = 1

class StaffLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class QRVerificationRequest(BaseModel):
    qr_token: str = Field(..., min_length=16, max_length=16, pattern='^[a-zA-Z0-9]{16}$')
    scanned_by: str = Field(..., min_length=1, max_length=50)

class LunchSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    started_by: str  # staff username who started the session
    ended_by: Optional[str] = None  # staff username who ended the session
    status: str = "pending"  # pending, active, ended
    total_expected: int = 0  # total people expected for lunch
    total_served: int = 0  # total people who were served
    created_at: datetime = Field(default_factory=datetime.utcnow)
    slack_start_message_ts: Optional[str] = None
    slack_end_message_ts: Optional[str] = None

# ... existing code ... (truncated for brevity, will append the rest next) 
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app import schemas, models
from backend.app.database import get_db

router = APIRouter(prefix="/api/practice", tags=["practice"])

# Add practice endpoints here

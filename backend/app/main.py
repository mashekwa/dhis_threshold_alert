import os
from fastapi import FastAPI, HTTPException, Query, Depends
from sqlalchemy import create_engine, Column, Integer, String, Date, func, case
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# SQLAlchemy Setup
DATABASE_URL = os.getenv("DATABASE_URL") #"postgresql+psycopg2://postgres:postgres@localhost:5433/alert_app"

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Alert(Base):
    __tablename__ = "alerts"
    trackedEntityInstance = Column(String, primary_key=True)
    disease_name = Column(String)
    alert_disease = Column(String)
    alert_id = Column(Integer)
    notificationDate = Column(Date)
    org_unit_name = Column(String)
    org_unit_id = Column(Integer)
    week = Column(String)
    status = Column(String)

class Location(Base):
    __tablename__ = "locations"
    district_id = Column(Integer, primary_key=True)
    province = Column(String)
    district = Column(Integer)
    district_name = Column(String)

# Pydantic Models
class AlertSummary(BaseModel):
    name: str
    newAlerts: int
    verified: int
    pending: int
    discarded: int

class DistrictAlertSummary(BaseModel):
    district_name: str
    newAlerts: int
    verified: int
    pending: int
    discarded: int

# Utility Function: Calculate Last Epidemiological Week
def get_last_epidemiological_week() -> str:
    today = datetime.now()
    current_week = today.strftime("%U")
    year = today.year
    last_epi_week = f"{year}W{int(current_week)}"
    return last_epi_week

# FastAPI App
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint 1: Get Alerts Summary by Province
# Endpoint 1: Get Alerts Summary by Province
@app.get("/api/province-summary", response_model=List[AlertSummary])
def get_province_summary(
    week: str = Query(get_last_epidemiological_week(), description="Epidemiological week format (YYYYWww)"),
    disease_name: Optional[str] = None,
    db: SessionLocal = Depends(get_db)
):
    query = db.query(
        Location.province,
        func.sum(case((Alert.status == 'VERIFICATION_STATUS_PENDING', 1), else_=0)).label('newAlerts'),
        func.sum(case((Alert.status == 'verified', 1), else_=0)).label('verified'),
        func.sum(case((Alert.status == 'VERIFICATION_STATUS_PENDING', 1), else_=0)).label('pending'),
        func.sum(case((Alert.status == 'discarded', 1), else_=0)).label('discarded')
    ).join(Alert, Alert.org_unit_id == Location.district_id).filter(Alert.week == week)
    
    if disease_name:
        query = query.filter(Alert.disease_name == disease_name)

    query = query.group_by(Location.province)
    
    results = query.all()

    return [
        AlertSummary(
            name=result.province,
            newAlerts=result.newAlerts,
            verified=result.verified,
            pending=result.pending,
            discarded=result.discarded
        )
        for result in results
    ]

@app.get("/api/province/{province}/districts", response_model=List[DistrictAlertSummary])
def get_district_alerts(
    province: str,
    week: str = Query(get_last_epidemiological_week(), description="Epidemiological week format (YYYYWww)"),
    disease_name: Optional[str] = None,
    db: SessionLocal = Depends(get_db)
):
    query = db.query(
        Location.district,  # Use org_unit_name from Location
        func.sum(case((Alert.status == 'VERIFICATION_STATUS_PENDING', 1), else_=0)).label('newAlerts'),
        func.sum(case((Alert.status == 'verified', 1), else_=0)).label('verified'),
        func.sum(case((Alert.status == 'VERIFICATION_STATUS_PENDING', 1), else_=0)).label('pending'),
        func.sum(case((Alert.status == 'discarded', 1), else_=0)).label('discarded')
    ).join(Alert, Alert.org_unit_id == Location.district_id).filter(and_(Location.province == province, Alert.week == week))
    
    if disease_name:
        query = query.filter(Alert.disease_name == disease_name)

    query = query.group_by(Location.district)
    
    results = query.all()

    return [
        DistrictAlertSummary(
            district_name=result.district,
            newAlerts=result.newAlerts,
            verified=result.verified,
            pending=result.pending,
            discarded=result.discarded
        )
        for result in results
    ]
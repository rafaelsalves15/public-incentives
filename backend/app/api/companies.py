from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.database import SessionLocal
from app.db.models import Company, IncentiveCompanyMatch
from typing import List, Optional
import logging

router = APIRouter(prefix="/companies", tags=["companies"])
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    activity_sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List companies with optional filtering"""
    try:
        query = db.query(Company)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Company.company_name.ilike(f"%{search}%"),
                    Company.trade_description_native.ilike(f"%{search}%"),
                    Company.cae_primary_label.ilike(f"%{search}%")
                )
            )
        
        if activity_sector:
            query = query.filter(Company.cae_primary_label.ilike(f"%{activity_sector}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        companies = query.offset(skip).limit(limit).all()
        
        return {
            "companies": [
                {
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                    "cae_primary_label": company.cae_primary_label,
                    "trade_description_native": company.trade_description_native,
                    "website": company.website,
                    "activity_sector": company.activity_sector,
                    "company_size": company.company_size,
                    "is_active": company.is_active
                }
                for company in companies
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}")
async def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific company"""
    try:
        company = db.query(Company).filter(
            Company.company_id == company_id
        ).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return {
            "company_id": str(company.company_id),
            "company_name": company.company_name,
            "cae_primary_label": company.cae_primary_label,
            "trade_description_native": company.trade_description_native,
            "website": company.website,
            "activity_sector": company.activity_sector,
            "company_size": company.company_size,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat() if company.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/incentives")
async def get_company_incentives(company_id: str, db: Session = Depends(get_db)):
    """Get incentives that match a specific company"""
    try:
        # Check if company exists
        company = db.query(Company).filter(
            Company.company_id == company_id
        ).first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Get matches
        matches = db.query(IncentiveCompanyMatch).filter(
            IncentiveCompanyMatch.company_id == company_id
        ).order_by(IncentiveCompanyMatch.match_score.desc()).all()
        
        return {
            "company_id": company_id,
            "company_name": company.company_name,
            "incentives": [
                {
                    "incentive_id": str(match.incentive.incentive_id),
                    "incentive_title": match.incentive.title,
                    "match_score": float(match.match_score),
                    "reasons": match.match_reasons or [],
                    "ranking_position": match.ranking_position,
                    "total_budget": float(match.incentive.total_budget) if match.incentive.total_budget else None
                }
                for match in matches
            ],
            "total_incentives": len(matches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting incentives for company {company_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/by-activity")
async def search_companies_by_activity(
    activity: str = Query(..., description="Activity or sector to search for"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Search companies by activity or sector"""
    try:
        companies = db.query(Company).filter(
            or_(
                Company.cae_primary_label.ilike(f"%{activity}%"),
                Company.trade_description_native.ilike(f"%{activity}%"),
                Company.activity_sector.ilike(f"%{activity}%")
            )
        ).limit(limit).all()
        
        return {
            "search_term": activity,
            "companies": [
                {
                    "company_id": str(company.company_id),
                    "company_name": company.company_name,
                    "cae_primary_label": company.cae_primary_label,
                    "trade_description_native": company.trade_description_native,
                    "website": company.website,
                    "activity_sector": company.activity_sector
                }
                for company in companies
            ],
            "total_found": len(companies)
        }
        
    except Exception as e:
        logger.error(f"Error searching companies by activity {activity}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

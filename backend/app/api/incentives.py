from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.database import SessionLocal
from app.db.models import Incentive, IncentiveCompanyMatch
from typing import List, Optional
import logging

router = APIRouter(prefix="/incentives", tags=["incentives"])
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def list_incentives(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List incentives with optional filtering"""
    try:
        query = db.query(Incentive)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Incentive.title.ilike(f"%{search}%"),
                    Incentive.description.ilike(f"%{search}%")
                )
            )
        
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        incentives = query.offset(skip).limit(limit).all()
        
        return {
            "incentives": [
                {
                    "incentive_id": str(incentive.incentive_id),
                    "title": incentive.title,
                    "description": incentive.description,
                    "ai_description": incentive.ai_description,
                    "total_budget": float(incentive.total_budget) if incentive.total_budget else None,
                    "publication_date": incentive.publication_date.isoformat() if incentive.publication_date else None,
                    "start_date": incentive.start_date.isoformat() if incentive.start_date else None,
                    "end_date": incentive.end_date.isoformat() if incentive.end_date else None,
                    "source_link": incentive.source_link
                }
                for incentive in incentives
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error listing incentives: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incentive_id}")
async def get_incentive(incentive_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific incentive"""
    try:
        incentive = db.query(Incentive).filter(
            Incentive.incentive_id == incentive_id
        ).first()
        
        if not incentive:
            raise HTTPException(status_code=404, detail="Incentive not found")
        
        return {
            "incentive_id": str(incentive.incentive_id),
            "title": incentive.title,
            "description": incentive.description,
            "ai_description": incentive.ai_description,
            "document_urls": incentive.document_urls,
            "publication_date": incentive.publication_date.isoformat() if incentive.publication_date else None,
            "start_date": incentive.start_date.isoformat() if incentive.start_date else None,
            "end_date": incentive.end_date.isoformat() if incentive.end_date else None,
            "total_budget": float(incentive.total_budget) if incentive.total_budget else None,
            "source_link": incentive.source_link
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting incentive {incentive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incentive_id}/matches")
async def get_incentive_matches(incentive_id: str, db: Session = Depends(get_db)):
    """Get company matches for a specific incentive"""
    try:
        # Check if incentive exists
        incentive = db.query(Incentive).filter(
            Incentive.incentive_id == incentive_id
        ).first()
        
        if not incentive:
            raise HTTPException(status_code=404, detail="Incentive not found")
        
        # Get matches
        matches = db.query(IncentiveCompanyMatch).filter(
            IncentiveCompanyMatch.incentive_id == incentive_id
        ).order_by(IncentiveCompanyMatch.ranking_position).all()
        
        return {
            "incentive_id": incentive_id,
            "incentive_title": incentive.title,
            "matches": [
                {
                    "company_name": match.company.company_name,
                    "company_activity": match.company.cae_primary_label,
                    "company_description": match.company.trade_description_native,
                    "company_website": match.company.website,
                    "match_score": float(match.match_score),
                    "reasons": match.match_reasons or [],
                    "ranking_position": match.ranking_position
                }
                for match in matches
            ],
            "total_matches": len(matches)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting matches for incentive {incentive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incentive_id}/summary")
async def get_incentive_summary(incentive_id: str, db: Session = Depends(get_db)):
    """Get AI-generated summary of an incentive"""
    try:
        incentive = db.query(Incentive).filter(
            Incentive.incentive_id == incentive_id
        ).first()
        
        if not incentive:
            raise HTTPException(status_code=404, detail="Incentive not found")
        
        # Check if we have AI-generated summary in all_data
        ai_summary = None
        if incentive.all_data and "ai_summary" in incentive.all_data:
            ai_summary = incentive.all_data["ai_summary"]
        
        return {
            "incentive_id": incentive_id,
            "title": incentive.title,
            "ai_summary": ai_summary,
            "has_ai_summary": ai_summary is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for incentive {incentive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

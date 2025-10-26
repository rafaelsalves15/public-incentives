from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.data_importer import DataImporter
from app.services.ai_processor import AIProcessor
from app.services.company_matcher_unified import CompanyMatcherUnified
import os
import logging

router = APIRouter(prefix="/data", tags=["data-management"])
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/import")
async def import_data(
    background_tasks: BackgroundTasks,
    companies_file: str = "companies.csv",
    incentives_file: str = "incentives.csv"
):
    """Import data from local CSV files"""
    try:
        # Use local file paths
        data_dir = "data"
        companies_path = os.path.join(data_dir, companies_file)
        incentives_path = os.path.join(data_dir, incentives_file)
        
        # Check if files exist
        if not os.path.exists(companies_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Companies CSV not found: {companies_path}. Please place your CSV file in the data/ directory."
            )
        if not os.path.exists(incentives_path):
            raise HTTPException(
                status_code=404, 
                detail=f"Incentives CSV not found: {incentives_path}. Please place your CSV file in the data/ directory."
            )
        
        # Import data in background
        background_tasks.add_task(import_data_task, companies_path, incentives_path)
        
        return {
            "message": "Data import started in background",
            "companies_file": companies_path,
            "incentives_file": incentives_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting data import: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def import_data_task(companies_path: str, incentives_path: str):
    """Background task to import data from local files"""
    try:
        importer = DataImporter()
        result = importer.import_from_local_files(companies_path, incentives_path)
        importer.close()
        
        logger.info(f"Data import completed: {result}")
        
    except Exception as e:
        logger.error(f"Error in background data import: {e}")


@router.post("/process-ai/{incentive_id}")
async def process_incentive_ai(incentive_id: str, db: Session = Depends(get_db)):
    """Process AI analysis for a specific incentive (complete processing)"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        ai_processor = AIProcessor(api_key, db)
        success = ai_processor.process_incentive_complete(db, incentive_id)
        
        if success:
            return {"message": f"AI processing completed for incentive {incentive_id}"}
        else:
            raise HTTPException(status_code=500, detail="AI processing failed")
            
    except Exception as e:
        logger.error(f"Error processing AI for incentive {incentive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-companies/{incentive_id}")
async def match_companies(incentive_id: str, db: Session = Depends(get_db)):
    """Find and save company matches for a specific incentive"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        ai_processor = AIProcessor(api_key, db)
        matcher = CompanyMatcherUnified(ai_processor)
        
        result = matcher.process_incentive_matches(db, incentive_id)
        
        return {
            "message": f"Company matching completed for incentive {incentive_id}",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error matching companies for incentive {incentive_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-all-matches")
async def process_all_matches(background_tasks: BackgroundTasks):
    """Process company matches for all incentives"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Process in background
        background_tasks.add_task(process_all_matches_task, api_key)
        
        return {"message": "Company matching started for all incentives"}
        
    except Exception as e:
        logger.error(f"Error starting company matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def process_all_matches_task(api_key: str):
    """Background task to process all matches"""
    try:
        db = SessionLocal()
        ai_processor = AIProcessor(api_key, db)
        matcher = CompanyMatcherUnified(ai_processor)
        
        result = matcher.process_all_incentives(db)
        db.close()
        
        logger.info(f"All matches processing completed: {result}")
        
    except Exception as e:
        logger.error(f"Error in background matches processing: {e}")


@router.get("/files/status")
async def check_data_files():
    """Check if required data files exist"""
    companies_path = "data/companies.csv"
    incentives_path = "data/incentives.csv"
    
    companies_exists = os.path.exists(companies_path)
    incentives_exists = os.path.exists(incentives_path)
    
    return {
        "companies_file": {
            "path": companies_path,
            "exists": companies_exists,
            "size": os.path.getsize(companies_path) if companies_exists else 0
        },
        "incentives_file": {
            "path": incentives_path,
            "exists": incentives_exists,
            "size": os.path.getsize(incentives_path) if incentives_exists else 0
        },
        "ready_for_import": companies_exists and incentives_exists
    }


@router.post("/process-ai/batch")
async def process_ai_batch(
    background_tasks: BackgroundTasks,
    limit: int = None,
    only_pending: bool = True
):
    """
    Process AI for multiple incentives in batch.
    
    Parameters:
    - limit: Maximum number of incentives to process (None = all)
    - only_pending: Only process incentives with status 'pending' (default: True)
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Start background task
        background_tasks.add_task(
            process_ai_batch_task,
            api_key,
            limit,
            only_pending
        )
        
        return {
            "message": "Batch AI processing started in background",
            "limit": limit,
            "only_pending": only_pending
        }
        
    except Exception as e:
        logger.error(f"Error starting batch AI processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def process_ai_batch_task(api_key: str, limit: int = None, only_pending: bool = True):
    """Background task to process AI for multiple incentives"""
    try:
        db = SessionLocal()
        ai_processor = AIProcessor(api_key, db)
        
        # Build query - filter by metadata status
        query = db.query(Incentive).join(IncentiveMetadata)
        if only_pending:
            query = query.filter(IncentiveMetadata.ai_processing_status == "pending")
        
        if limit:
            query = query.limit(limit)
        
        incentives = query.all()
        
        logger.info(f"Starting batch processing for {len(incentives)} incentives")
        
        success_count = 0
        failed_count = 0
        
        for incentive in incentives:
            try:
                success = ai_processor.process_incentive_complete(db, str(incentive.incentive_id))
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                
                # Log progress every 10 incentives
                if (success_count + failed_count) % 10 == 0:
                    logger.info(f"Batch progress: {success_count} success, {failed_count} failed")
                    
            except Exception as e:
                logger.error(f"Error processing incentive {incentive.incentive_id}: {e}")
                failed_count += 1
        
        db.close()
        logger.info(f"Batch processing completed: {success_count} success, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Error in batch AI processing task: {e}")


@router.get("/processing-status")
async def get_processing_status(db: Session = Depends(get_db)):
    """Get detailed AI processing status for all incentives"""
    try:
        from sqlalchemy import func
        
        # Count by status (from metadata table)
        status_counts = db.query(
            IncentiveMetadata.ai_processing_status,
            func.count(IncentiveMetadata.metadata_id).label('count')
        ).group_by(IncentiveMetadata.ai_processing_status).all()
        
        # Total count
        total = db.query(func.count(Incentive.incentive_id)).scalar()
        
        # Build response
        status_dict = {status: count for status, count in status_counts}
        
        # Get some example IDs for each status
        examples = {}
        for status in ['pending', 'processing', 'completed', 'failed']:
            results = db.query(Incentive, IncentiveMetadata).join(IncentiveMetadata).filter(
                IncentiveMetadata.ai_processing_status == status
            ).limit(5).all()
            
            examples[status] = [
                {
                    "incentive_id": str(i.incentive_id),
                    "title": i.title,
                    "fields_completed": m.fields_completed_by_ai or []
                }
                for i, m in results
            ]
        
        return {
            "total": total,
            "status_counts": {
                "pending": status_dict.get("pending", 0),
                "processing": status_dict.get("processing", 0),
                "completed": status_dict.get("completed", 0),
                "failed": status_dict.get("failed", 0)
            },
            "completion_percentage": (status_dict.get("completed", 0) / total * 100) if total > 0 else 0,
            "examples": examples
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_import_status():
    """Get current import and processing status (legacy endpoint)"""
    try:
        # Redirect to new processing-status endpoint
        return {
            "status": "ready",
            "message": "Data management endpoints are available. Use /data/processing-status for detailed status."
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess-failed")
async def reprocess_failed_incentives(background_tasks: BackgroundTasks, limit: int = None):
    """Reprocess incentives that failed AI processing"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Start background task to reprocess failed
        background_tasks.add_task(
            reprocess_failed_task,
            api_key,
            limit
        )
        
        return {
            "message": "Reprocessing failed incentives started in background",
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error starting reprocessing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def reprocess_failed_task(api_key: str, limit: int = None):
    """Background task to reprocess failed incentives"""
    try:
        db = SessionLocal()
        ai_processor = AIProcessor(api_key, db)
        
        # Get failed incentives (check metadata table)
        query = db.query(Incentive).join(IncentiveMetadata).filter(
            IncentiveMetadata.ai_processing_status == "failed"
        )
        if limit:
            query = query.limit(limit)
        
        failed_incentives = query.all()
        
        logger.info(f"Reprocessing {len(failed_incentives)} failed incentives")
        
        success_count = 0
        still_failed = 0
        
        for incentive in failed_incentives:
            # Reset status to pending in metadata
            metadata = db.query(IncentiveMetadata).filter(
                IncentiveMetadata.incentive_id == incentive.incentive_id
            ).first()
            
            if metadata:
                metadata.ai_processing_status = "pending"
                metadata.ai_processing_error = None
                db.commit()
            
            # Try processing again
            success = ai_processor.process_incentive_complete(db, str(incentive.incentive_id))
            if success:
                success_count += 1
            else:
                still_failed += 1
        
        db.close()
        logger.info(f"Reprocessing completed: {success_count} recovered, {still_failed} still failed")
        
    except Exception as e:
        logger.error(f"Error in reprocessing task: {e}")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get memory cache statistics.
    Shows cache hits, misses, hit rate, and estimated savings.
    
    Note: Statistics are per AIProcessor instance (resets on restart).
    """
    try:
        # Create temporary processor to get stats
        # In production, you'd want to maintain a singleton instance
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return {
                "error": "OpenAI API key not configured",
                "stats": None
            }
        
        # Note: This creates a new instance, so stats will be empty
        # For real stats, need to track across the actual processor instance used in processing
        return {
            "message": "Cache statistics are tracked during batch processing",
            "note": "Stats reset on each new AIProcessor instance",
            "recommendation": "Check logs during batch processing to see cache hits/misses"
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/stats")
async def get_cost_stats(db: Session = Depends(get_db)):
    """
    Get detailed cost statistics from OpenAI API usage.
    
    Returns:
        - Total costs (all time)
        - Cost breakdown by operation type (ai_description, extract_dates, extract_budget)
        - Token usage statistics
        - Cache hit rate and savings
        - Average cost per call
    """
    try:
        from app.services.cost_tracker import CostTracker
        
        cost_tracker = CostTracker(db)
        stats = cost_tracker.get_total_stats()
        
        return {
            "success": True,
            "data": stats,
            "message": "Cost statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting cost stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/recent")
async def get_recent_costs(limit: int = 20, db: Session = Depends(get_db)):
    """
    Get recent API calls with cost details.
    
    Args:
        limit: Number of recent calls to return (default: 20)
    
    Returns:
        List of recent API calls with timestamps, costs, and tokens
    """
    try:
        from app.db.models import AICostTracking
        
        recent_calls = db.query(AICostTracking)\
            .order_by(AICostTracking.created_at.desc())\
            .limit(limit)\
            .all()
        
        results = []
        for call in recent_calls:
            results.append({
                "tracking_id": str(call.tracking_id),
                "incentive_id": str(call.incentive_id) if call.incentive_id else None,
                "operation_type": call.operation_type,
                "model_name": call.model_name,
                "tokens": {
                    "input": call.input_tokens,
                    "output": call.output_tokens,
                    "total": call.total_tokens
                },
                "cost": {
                    "input": float(call.input_cost),
                    "output": float(call.output_cost),
                    "total": float(call.total_cost),
                    "formatted": f"${float(call.total_cost):.6f}"
                },
                "cache_hit": call.cache_hit,
                "success": call.success,
                "error_message": call.error_message,
                "created_at": call.created_at.isoformat() if call.created_at else None
            })
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error getting recent costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

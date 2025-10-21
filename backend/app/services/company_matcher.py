import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company, IncentiveCompanyMatch
from .ai_processor import AIProcessor

logger = logging.getLogger(__name__)


class CompanyMatcher:
    def __init__(self, ai_processor: AIProcessor):
        self.ai_processor = ai_processor
    
    def find_top_matches(self, session: Session, incentive_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find top matching companies for a specific incentive"""
        logger.info(f"Finding top {limit} matches for incentive {incentive_id}")
        
        # Get the incentive
        incentive = session.query(Incentive).filter(
            Incentive.incentive_id == incentive_id
        ).first()
        
        if not incentive:
            logger.error(f"Incentive {incentive_id} not found")
            return []
        
        # Get all companies
        companies = session.query(Company).all()
        logger.info(f"Analyzing {len(companies)} companies for incentive {incentive_id}")
        
        matches = []
        
        for company in companies:
            try:
                # Analyze match using AI
                match_analysis = self.ai_processor.analyze_company_match(incentive, company)
                
                if match_analysis.get("match_score", 0) > 0.1:  # Only consider matches above 10%
                    matches.append({
                        "company": company,
                        "incentive": incentive,
                        "match_score": match_analysis.get("match_score", 0),
                        "reasons": match_analysis.get("reasons", []),
                        "concerns": match_analysis.get("concerns", []),
                        "recommendations": match_analysis.get("recommendations", [])
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing company {company.name}: {e}")
                continue
        
        # Sort by match score and get top matches
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        top_matches = matches[:limit]
        
        logger.info(f"Found {len(top_matches)} top matches for incentive {incentive_id}")
        return top_matches
    
    def save_matches(self, session: Session, matches: List[Dict[str, Any]]) -> bool:
        """Save company matches to database"""
        try:
            # Clear existing matches for this incentive
            if matches:
                incentive_id = matches[0]["incentive"].incentive_id
                session.query(IncentiveCompanyMatch).filter(
                    IncentiveCompanyMatch.incentive_id == incentive_id
                ).delete()
            
            # Save new matches
            for i, match in enumerate(matches):
                match_record = IncentiveCompanyMatch(
                    incentive_id=match["incentive"].incentive_id,
                    company_id=match["company"].company_id,
                    match_score=match["match_score"],
                    match_reasons=match["reasons"],
                    ranking_position=i + 1
                )
                session.add(match_record)
            
            session.commit()
            logger.info(f"Saved {len(matches)} matches to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving matches: {e}")
            session.rollback()
            return False
    
    def process_incentive_matches(self, session: Session, incentive_id: str) -> Dict[str, Any]:
        """Process and save matches for a specific incentive"""
        logger.info(f"Processing matches for incentive {incentive_id}")
        
        # Find top matches
        matches = self.find_top_matches(session, incentive_id)
        
        if not matches:
            logger.warning(f"No matches found for incentive {incentive_id}")
            return {"success": False, "matches_count": 0}
        
        # Save matches to database
        success = self.save_matches(session, matches)
        
        if success:
            logger.info(f"Successfully processed {len(matches)} matches for incentive {incentive_id}")
            return {
                "success": True,
                "matches_count": len(matches),
                "top_match_score": matches[0]["match_score"] if matches else 0
            }
        else:
            logger.error(f"Failed to save matches for incentive {incentive_id}")
            return {"success": False, "matches_count": 0}
    
    def get_incentive_matches(self, session: Session, incentive_id: str) -> List[Dict[str, Any]]:
        """Get saved matches for a specific incentive"""
        matches = session.query(IncentiveCompanyMatch).filter(
            IncentiveCompanyMatch.incentive_id == incentive_id
        ).order_by(IncentiveCompanyMatch.ranking_position).all()
        
        result = []
        for match in matches:
            result.append({
                "company_name": match.company.name,
                "company_activity": match.company.cae_primary_label,
                "match_score": float(match.match_score),
                "reasons": match.match_reasons or [],
                "ranking_position": match.ranking_position
            })
        
        return result
    
    def process_all_incentives(self, session: Session, batch_size: int = 10) -> Dict[str, Any]:
        """Process matches for all incentives in batches"""
        logger.info("Processing matches for all incentives")
        
        # Get all incentives
        incentives = session.query(Incentive).all()
        total_incentives = len(incentives)
        
        processed = 0
        successful = 0
        failed = 0
        
        for i in range(0, total_incentives, batch_size):
            batch = incentives[i:i + batch_size]
            
        for incentive in batch:
            try:
                result = self.process_incentive_matches(session, incentive.incentive_id)
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
                processed += 1
                
                logger.info(f"Processed {processed}/{total_incentives} incentives")
                
            except Exception as e:
                logger.error(f"Error processing incentive {incentive.incentive_id}: {e}")
                failed += 1
                processed += 1
        
        return {
            "total_incentives": total_incentives,
            "processed": processed,
            "successful": successful,
            "failed": failed
        }

"""
Company Matcher com Sistema Unificado - Fase 2

Pipeline de 2 fases para maximizar qualidade e minimizar custos:

FASE 1: Unified Scoring (GRÁTIS, ~10ms)
    ├─ Pontua TODAS as empresas (não elimina nenhuma)
    ├─ Sistema de ganho/perda de pontos
    └─ Ranking de todas as empresas por qualidade

FASE 2: LLM Refinement (PAGO, ~2s)
    ├─ Análise detalhada do Top 15 candidatas
    ├─ Geração de scores finais, razões e recomendações
    └─ Custo: ~$0.002 por incentivo

Vantagens:
- SEMPRE retorna 5 empresas (mesmo que não sejam perfeitas)
- Sistema mais robusto e confiável
- Menos complexidade (elimina filtros rígidos)
- Melhor qualidade de matching
"""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company, IncentiveCompanyMatch
from .ai_processor import AIProcessor
from .unified_scorer import UnifiedScorer

logger = logging.getLogger(__name__)


class CompanyMatcherUnified:
    """
    Sistema de Matching com Sistema Unificado - Fase 2
    
    Pipeline de 2 fases:
    1. Unified Scoring: Pontua TODAS as empresas
    2. LLM Refinement: Análise detalhada do top 15
    """
    
    def __init__(self, ai_processor: AIProcessor):
        self.ai_processor = ai_processor
        self.unified_scorer = UnifiedScorer(ai_processor)
    
    def find_top_matches(
        self, 
        session: Session, 
        incentive_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Encontra as melhores empresas para um incentivo.
        
        Args:
            session: Sessão da base de dados
            incentive_id: ID do incentivo
            limit: Número máximo de matches (padrão: 5)
            
        Returns:
            Lista de matches com scores e razões
            
        Example:
            >>> matcher = CompanyMatcherUnified(ai_processor)
            >>> matches = matcher.find_top_matches(session, incentive_id)
            >>> print(f"Found {len(matches)} matches")
        """
        logger.info(f"Finding top {limit} matches for incentive {incentive_id}")
        
        # Get the incentive
        incentive = session.query(Incentive).filter(
            Incentive.incentive_id == incentive_id
        ).first()
        
        if not incentive:
            logger.error(f"Incentive {incentive_id} not found")
            return []
        
        # Get all companies
        all_companies = session.query(Company).all()
        logger.info(f"Starting with {len(all_companies)} companies")
        
        return self._find_matches_unified(incentive, all_companies, limit)
    
    def _find_matches_unified(
        self, 
        incentive: Incentive, 
        all_companies: List[Company], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Pipeline unificado de matching.
        
        FASE 1: Unified Scoring → pontua TODAS as empresas (grátis)
        FASE 2: LLM Refinement → análise detalhada top N (pago)
        """
        # ==========================================
        # FASE 1: UNIFIED SCORING (GRÁTIS)
        # ==========================================
        logger.info("📊 FASE 1: Unified scoring...")
        
        scored_companies = []
        for company in all_companies:
            score_data = self.unified_scorer.score_company(incentive, company)
            scored_companies.append({
                'company': company,
                'unified_score': score_data['score'],
                'reasons': score_data['details']
            })
        
        # Sort by score (highest first)
        scored_companies.sort(key=lambda x: x['unified_score'], reverse=True)
        
        logger.info(f"✅ Unified scoring: {len(scored_companies)} companies scored")
        if scored_companies:
            logger.info(f"   Top score: {scored_companies[0]['unified_score']:.1f}")
            logger.info(f"   Bottom score: {scored_companies[-1]['unified_score']:.1f}")
        
        # ==========================================
        # FASE 2: LLM REFINEMENT (PAGO)
        # ==========================================
        logger.info("🤖 FASE 2: LLM refinement...")
        
        # Get top candidates for LLM processing (top 15 for better context)
        top_candidates = scored_companies[:15]
        
        if len(top_candidates) < limit:
            # If we have fewer candidates than needed, use all
            top_candidates = scored_companies
        
        # Prepare data for LLM - keep Company objects
        companies_data = []
        for item in top_candidates:
            company = item['company']
            # Add unified score info to company object for LLM context
            company.unified_score = item['unified_score']
            company.unified_reasons = item['reasons']
            companies_data.append(company)
        
        # LLM analysis
        try:
            llm_results = self.ai_processor.analyze_batch_match(
                incentive=incentive,
                companies=companies_data,
                raw_csv_data={},
                select_top_n=limit
            )
            
            if not llm_results:
                logger.error("❌ LLM analysis failed")
                return []
            
            # Process LLM results
            final_matches = []
            for i, result in enumerate(llm_results[:limit]):
                company_id = result.get('company_id')
                if not company_id:
                    continue
                
                # Find the original company
                company = next((c for c in all_companies if str(c.company_id) == company_id), None)
                if not company:
                    continue
                
                # Get unified score and reasons
                unified_data = next((item for item in scored_companies if str(item['company'].company_id) == company_id), None)
                
                final_matches.append({
                    'company_id': company_id,
                    'company_name': company.company_name,
                    'cae_primary_label': company.cae_primary_label,
                    'website': company.website,
                    'llm_score': result.get('match_score', 0),  # FIXED: use match_score
                    'unified_score': unified_data['unified_score'] if unified_data else 0,
                    'unified_reasons': unified_data['reasons'] if unified_data else [],
                    'llm_reasons': result.get('reasons', []),
                    'ranking_position': i + 1
                })
            
            logger.info(f"✅ LLM refinement: {len(final_matches)} final matches")
            return final_matches
            
        except Exception as e:
            logger.error(f"❌ Error in LLM analysis: {e}")
            # FALLBACK: Use Unified Scorer results when LLM fails
            logger.info("🔄 Using Unified Scorer fallback due to LLM error")
            
            final_matches = []
            for i, item in enumerate(top_candidates[:limit]):
                company = item['company']
                unified_data = next((scored for scored in scored_companies 
                                   if scored['company'].company_id == company.company_id), None)
                
                final_matches.append({
                    'company_id': str(company.company_id),
                    'company_name': company.company_name,
                    'cae_primary_label': company.cae_primary_label,
                    'website': company.website,
                    'llm_score': 0.0,  # LLM failed
                    'unified_score': unified_data['unified_score'] if unified_data else 0,
                    'unified_reasons': unified_data['reasons'] if unified_data else [],
                    'llm_reasons': ['LLM analysis failed - using unified scorer'],
                    'ranking_position': i + 1
                })
            
            logger.info(f"✅ Unified Scorer fallback: {len(final_matches)} matches")
            return final_matches
    
    def save_matches(
        self, 
        session: Session, 
        incentive_id: str, 
        matches: List[Dict[str, Any]]
    ) -> bool:
        """
        Salva matches na base de dados.
        
        Args:
            session: Sessão da base de dados
            incentive_id: ID do incentivo
            matches: Lista de matches para salvar
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Remove existing matches for this incentive
            session.query(IncentiveCompanyMatch).filter(
                IncentiveCompanyMatch.incentive_id == incentive_id
            ).delete()
            
            # Save new matches
            for match in matches:
                db_match = IncentiveCompanyMatch(
                    incentive_id=incentive_id,
                    company_id=match['company_id'],
                    match_score=match.get('llm_score', 0),
                    match_reasons=match.get('llm_reasons', []),
                    ranking_position=match.get('ranking_position', 0)
                )
                session.add(db_match)
            
            session.commit()
            logger.info(f"✅ Saved {len(matches)} matches for incentive {incentive_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving matches: {e}")
            session.rollback()
            return False
    
    def get_scorer_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do unified scorer."""
        return self.unified_scorer.get_stats()
    
    def reset_scorer_stats(self):
        """Reseta estatísticas do unified scorer."""
        self.unified_scorer.reset_stats()
    
    def process_incentive_matches(self, session: Session, incentive_id: str) -> Dict[str, Any]:
        """Process and save matches for a specific incentive"""
        logger.info(f"Processing matches for incentive {incentive_id}")
        
        # Find top matches
        matches = self.find_top_matches(session, incentive_id)
        
        if not matches:
            return {
                "incentive_id": incentive_id,
                "matches_found": 0,
                "message": "No matches found"
            }
        
        # Save matches
        success = self.save_matches(session, incentive_id, matches)
        
        return {
            "incentive_id": incentive_id,
            "matches_found": len(matches),
            "matches_saved": success,
            "matches": matches
        }
    
    def process_all_incentives(self, session: Session, batch_size: int = 10) -> Dict[str, Any]:
        """Process matches for all incentives in batches"""
        logger.info("Processing matches for all incentives")
        
        # Get all incentives
        incentives = session.query(Incentive).all()
        total_incentives = len(incentives)
        
        results = []
        processed = 0
        
        for i in range(0, total_incentives, batch_size):
            batch = incentives[i:i + batch_size]
            
            for incentive in batch:
                try:
                    result = self.process_incentive_matches(session, str(incentive.incentive_id))
                    results.append(result)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing incentive {incentive.incentive_id}: {e}")
                    results.append({
                        "incentive_id": str(incentive.incentive_id),
                        "error": str(e)
                    })
        
        return {
            "total_incentives": total_incentives,
            "processed": processed,
            "results": results
        }

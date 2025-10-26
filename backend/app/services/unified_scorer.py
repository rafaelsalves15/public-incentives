"""
Unified Scorer - Sistema de Pontuação Unificado

Sistema de pontuação contínua que substitui filtros rígidos por um sistema
de ganho/perda de pontos baseado em compatibilidade.

Vantagens:
- Não elimina empresas (pontua todas)
- Sistema mais flexível e robusto
- Melhor discriminação entre candidatos
- Elimina complexidade de filtros rígidos
"""

import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.db.models import Incentive, Company
from .ai_processor import AIProcessor

logger = logging.getLogger(__name__)


class UnifiedScorer:
    """
    Sistema de Pontuação Unificado
    
    Pontua TODAS as empresas baseado em compatibilidade:
    - CAE codes (exato, relacionado, setor)
    - Região
    - Tamanho da empresa
    - Penalties por incompatibilidade
    """
    
    def __init__(self, ai_processor: AIProcessor):
        self.ai_processor = ai_processor
        
        # Pesos ajustados para melhor discriminação
        self.WEIGHTS = {
            "cae_exact_match": 150,      # Mais peso para CAE exato
            "cae_related_match": 75,     # CAE relacionado
            "sector_match": 40,          # Setor compatível
            "sector_partial_match": 20,  # Setor parcial
            "region_match": 30,          # Menos peso para região
            "size_match": 30,            # Menos peso para tamanho
        }
    
    def score_company(self, incentive: Incentive, company: Company) -> Dict[str, Any]:
        """
        Pontua uma empresa baseado na compatibilidade com o incentivo
        
        Returns:
            Dict com score total e detalhes dos pontos ganhos/perdidos
        """
        score = 0
        details = []
        
        # Obter dados do incentivo
        incentive_data = incentive.ai_description or {}
        eligible_cae_codes = incentive_data.get('eligible_cae_codes', [])
        eligible_sectors = incentive_data.get('eligible_sectors', [])
        target_region = incentive_data.get('target_region', '')
        target_company_size = incentive_data.get('target_company_size', '')
        
        # Obter dados da empresa
        company_cae = company.cae_primary_code
        company_sector = company.cae_primary_label
        company_region = company.region
        company_size = company.company_size
        
        # 1. CAE CODE MATCHING
        if company_cae and eligible_cae_codes:
            # Verificar se algum CAE da empresa está elegível
            for cae in company_cae:
                if cae in eligible_cae_codes:
                    # CAE exato
                    score += self.WEIGHTS["cae_exact_match"]
                    details.append(f"CAE exato: {cae} (+{self.WEIGHTS['cae_exact_match']})")
                    break  # Só conta o primeiro match
            else:
                # Verificar CAE relacionado (mesmo grupo) se não houve match exato
                for cae in company_cae:
                    cae_group = cae[:2] if len(cae) >= 2 else cae
                    for eligible_cae in eligible_cae_codes:
                        eligible_cae_group = eligible_cae[:2] if len(eligible_cae) >= 2 else eligible_cae
                        if cae_group == eligible_cae_group:
                            score += self.WEIGHTS["cae_related_match"]
                            details.append(f"CAE relacionado: {cae} (+{self.WEIGHTS['cae_related_match']})")
                            break
                    if score > 0:  # Se já encontrou match relacionado, para
                        break
        
        # 2. SECTOR MATCHING
        if company_sector and eligible_sectors:
            company_sector_lower = company_sector.lower()
            for eligible_sector in eligible_sectors:
                eligible_sector_lower = eligible_sector.lower()
                
                # Match exato
                if company_sector_lower == eligible_sector_lower:
                    score += self.WEIGHTS["sector_match"]
                    details.append(f"Setor exato: {company_sector} (+{self.WEIGHTS['sector_match']})")
                    break
                # Match parcial
                elif any(word in company_sector_lower for word in eligible_sector_lower.split()):
                    score += self.WEIGHTS["sector_partial_match"]
                    details.append(f"Setor parcial: {company_sector} (+{self.WEIGHTS['sector_partial_match']})")
                    break
        
        # 3. REGION MATCHING
        if company_region and target_region:
            if company_region.lower() == target_region.lower():
                score += self.WEIGHTS["region_match"]
                details.append(f"Região: {company_region} (+{self.WEIGHTS['region_match']})")
        
        # 4. COMPANY SIZE MATCHING
        if company_size and target_company_size:
            if company_size.lower() == target_company_size.lower():
                score += self.WEIGHTS["size_match"]
                details.append(f"Tamanho: {company_size} (+{self.WEIGHTS['size_match']})")
        
        
        return {
            "score": score,
            "details": details,
            "company_id": company.company_id,
            "company_name": company.company_name,
            "cae_code": company_cae,
            "sector": company_sector,
            "region": company_region,
            "size": company_size
        }
    
    def score_all_companies(self, session: Session, incentive_id: str) -> List[Dict[str, Any]]:
        """
        Pontua TODAS as empresas para um incentivo
        
        Returns:
            Lista de scores ordenada por pontuação (maior primeiro)
        """
        incentive = session.query(Incentive).filter(Incentive.id == incentive_id).first()
        if not incentive:
            logger.error(f"Incentivo {incentive_id} não encontrado")
            return []
        
        companies = session.query(Company).all()
        if not companies:
            logger.warning("Nenhuma empresa encontrada")
            return []
        
        logger.info(f"Pontuando {len(companies)} empresas para incentivo '{incentive.title}'")
        
        scores = []
        for company in companies:
            score_data = self.score_company(incentive, company)
            scores.append(score_data)
        
        # Ordenar por score (maior primeiro)
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Scores calculados: {len(scores)} empresas")
        logger.info(f"Top 5 scores: {[s['score'] for s in scores[:5]]}")
        
        return scores
    
    def get_top_companies(self, session: Session, incentive_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retorna as top N empresas com melhor score
        
        Args:
            session: Sessão da base de dados
            incentive_id: ID do incentivo
            limit: Número máximo de empresas a retornar
            
        Returns:
            Lista das top empresas ordenadas por score
        """
        all_scores = self.score_all_companies(session, incentive_id)
        return all_scores[:limit]

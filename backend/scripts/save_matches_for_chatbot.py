#!/usr/bin/env python3
"""
Salvar Matches para Chatbot
============================

Este script gera e salva matches na tabela IncentiveCompanyMatch.
Deve ser executado APÓS o setup principal.
"""

import sys
import logging
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Incentive, Company, IncentiveCompanyMatch
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from app.services.hybrid_matching_service import HybridMatchingService
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_matches_for_chatbot():
    """Gera e salva matches na base de dados"""
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    db = SessionLocal()
    
    try:
        # Inicializar serviços
        ai_processor = AIProcessor(api_key=api_key, session=db)
        embedding_service = EmbeddingService(api_key, db)
        vector_db = VectorDatabaseService(embedding_service)
        hybrid_matcher = HybridMatchingService(
            ai_processor,
            embedding_service, 
            vector_db
        )
        
        # Obter todos os incentivos
        incentives = db.query(Incentive).all()
        logger.info(f"🎯 Gerando matches para {len(incentives)} incentiv os...")
        
        total_matches = 0
        
        for i, incentive in enumerate(incentives, 1):
            logger.info(f"🔍 Processing {i}/{len(incentives)}: {incentive.title[:50]}...")
            
            try:
                # Gerar matches
                matches = hybrid_matcher.find_top_matches(
                    session=db, 
                    incentive_id=incentive.incentive_id, 
                    limit=10
                )
                
                if not matches:
                    continue
                
                logger.info(f"   ✅ {len(matches)} matches encontrados")
                
                # Limpar matches existentes
                db.query(IncentiveCompanyMatch).filter(
                    IncentiveCompanyMatch.incentive_id == incentive.incentive_id
                ).delete()
                
                # Salvar novos matches
                for rank, match in enumerate(matches, 1):
                    company_id = match.get('company_id')
                    if not company_id:
                        company = match.get('company')
                        if company:
                            company_id = company.company_id
                    
                    # ✅ VERIFICAR se empresa existe na BD antes de salvar
                    company_exists = db.query(Company).filter(Company.company_id == company_id).first()
                    if not company_exists:
                        logger.warning(f"   ⚠️ Empresa {company_id} não existe na BD, a ignorar")
                        continue
                    
                    match_record = IncentiveCompanyMatch(
                        incentive_id=incentive.incentive_id,
                        company_id=company_id,
                        match_score=match.get('total_score', match.get('llm_score', match.get('match_score', 0.0))),
                        match_reasons=match.get('reasons', match.get('match_reasons', [])),
                        ranking_position=rank
                    )
                    db.add(match_record)
                
                db.commit()
                total_matches += len(matches)
                
            except Exception as e:
                logger.error(f"❌ Erro para incentivo {i}: {e}")
                db.rollback()
                continue
        
        logger.info(f"\n🎉 Total de matches salvos: {total_matches}")
        
        # Verificar total na BD
        db_total = db.query(IncentiveCompanyMatch).count()
        logger.info(f"📊 Total na base de dados: {db_total}")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    save_matches_for_chatbot()

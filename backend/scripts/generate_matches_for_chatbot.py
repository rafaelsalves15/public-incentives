#!/usr/bin/env python3
"""
Gerar Matches para o Chatbot

Gera matches para todos os incentivos que ainda não têm matches,
para que o chatbot possa responder corretamente.
"""

import sys
import os

# Adicionar path do app
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Incentive, IncentiveCompanyMatch
from app.services.ai_processor import AIProcessor
from app.services.hybrid_matching_service import HybridMatchingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_matches_for_chatbot():
    """Gera matches para incentivos que ainda não têm matches"""
    
    # Inicializar serviços
    db = SessionLocal()
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'sk-REPLACE_ME':
            logger.error("OPENAI_API_KEY não configurada corretamente!")
            return False
        
        ai_processor = AIProcessor(api_key, db)
        embedding_service = EmbeddingService(api_key, db)
        vector_db = VectorDatabaseService(embedding_service)
        hybrid_matcher = HybridMatchingService(ai_processor, embedding_service, vector_db)
        
        # Buscar incentivos sem matches
        all_incentives = db.query(Incentive).all()
        
        logger.info(f"📊 Total de incentivos: {len(all_incentives)}")
        
        for incentive in all_incentives:
            # Verificar se já tem matches
            existing_matches = db.query(IncentiveCompanyMatch).filter(
                IncentiveCompanyMatch.incentive_id == incentive.incentive_id
            ).count()
            
            if existing_matches > 0:
                logger.info(f"✅ Incentivo '{incentive.title[:50]}...' já tem {existing_matches} matches")
                continue
            
            logger.info(f"🔄 Gerando matches para: {incentive.title[:50]}...")
            
            try:
                # Gerar matches usando o sistema híbrido
                matches = hybrid_matcher.find_matches(db, str(incentive.incentive_id), limit=5)
                
                # Salvar matches na BD
                for i, match in enumerate(matches, 1):
                    match_record = IncentiveCompanyMatch(
                        incentive_id=incentive.incentive_id,
                        company_id=match['company'].company_id,
                        match_score=match.get('match_score', 0.0),
                        match_reasons=match.get('reasons', []),
                        ranking_position=i
                    )
                    db.add(match_record)
                
                db.commit()
                logger.info(f"✅ Salvos {len(matches)} matches para o incentivo")
                
            except Exception as e:
                logger.error(f"❌ Erro ao gerar matches: {e}")
                db.rollback()
                continue
        
        # Estatísticas finais
        total_matches = db.query(IncentiveCompanyMatch).count()
        logger.info(f"\n🎉 Total de matches na BD: {total_matches}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro geral: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    generate_matches_for_chatbot()




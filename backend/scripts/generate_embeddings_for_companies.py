#!/usr/bin/env python3
"""
Gerar Embeddings para Empresas Existentes
==========================================

Este script gera embeddings para todas as empresas que estão na base de dados
mas ainda não têm embeddings no ChromaDB.
"""

import sys
sys.path.insert(0, '/app')

import logging
from app.db.database import SessionLocal
from app.db.models import Company, Incentive
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_all_embeddings():
    """Gera embeddings para todas as empresas e incentiv os que ainda não têm"""
    
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    db = SessionLocal()
    
    try:
        # Inicializar serviços
        ai_processor = AIProcessor(api_key=api_key, session=db)
        embedding_service = EmbeddingService(api_key, db)
        vector_db = VectorDatabaseService(embedding_service)
        
        # Empresas
        companies = db.query(Company).all()
        logger.info(f"🏢 Gerando embeddings para {len(companies)} empresas...")
        
        for i, company in enumerate(companies, 1):
            try:
                success = vector_db.add_company_embedding(company)
                if success:
                    if i % 100 == 0:
                        logger.info(f"✅ Progresso: {i}/{len(companies)} empresas")
            except Exception as e:
                logger.error(f"❌ Erro para empresa {i}: {e}")
                continue
        
        logger.info(f"✅ {len(companies)} empresas processadas")
        
        # Incentiv os
        incentives = db.query(Incentive).all()
        logger.info(f"📝 Gerando embeddings para {len(incentives)} incentiv os...")
        
        for i, incentive in enumerate(incentives, 1):
            try:
                success = vector_db.add_incentive_embedding(incentive)
                if success:
                    logger.info(f"✅ Incentive {i}/{len(incentives)}: {incentive.title[:50]}...")
            except Exception as e:
                logger.error(f"❌ Erro para incentivo {i}: {e}")
                continue
        
        # Verificar total
        companies_count = vector_db.companies_collection.count()
        incentives_count = vector_db.incentives_collection.count()
        
        logger.info(f"\n🎉 Embeddings gerados:")
        logger.info(f"   Companies: {companies_count}")
        logger.info(f"   Incentives: {incentives_count}")
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_all_embeddings()

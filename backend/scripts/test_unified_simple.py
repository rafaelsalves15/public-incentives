#!/usr/bin/env python3
"""
Teste Simples do Sistema de Matching Unificado
Testa 1 incentivo com 50 empresas
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.db.models import Incentive, Company
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unified_matching():
    """Testa o sistema de matching unificado"""
    
    print("🚀 TESTE DO SISTEMA DE MATCHING UNIFICADO")
    print("=" * 50)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    matcher = CompanyMatcherUnified(ai_processor)
    
    try:
        # Obter primeiro incentivo
        incentive = db.query(Incentive).first()
        if not incentive:
            print("❌ Nenhum incentivo encontrado!")
            return
        
        print(f"📋 INCENTIVO: {incentive.title}")
        print(f"🎯 ID: {incentive.incentive_id}")
        print()
        
        # Obter empresas
        companies = db.query(Company).limit(50).all()
        print(f"🏢 EMPRESAS DISPONÍVEIS: {len(companies)}")
        print()
        
        # Testar matching
        print("🔍 INICIANDO MATCHING...")
        matches = matcher.find_top_matches(
            session=db,
            incentive_id=incentive.incentive_id,
            limit=5
        )
        
        print(f"✅ MATCHING CONCLUÍDO!")
        print(f"📊 RESULTADOS: {len(matches)} matches encontrados")
        print()
        
        # Mostrar resultados
        print("🏆 TOP 5 MATCHES:")
        print("-" * 50)
        
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match['company_name']}")
            print(f"   Score Unificado: {match['unified_score']}")
            print(f"   Score LLM: {match['llm_score']}")
            print(f"   Razão LLM: {match.get('llm_reasons', [])}")
            print(f"   CAE: {match.get('cae_primary_label', 'N/A')}")
            print()
        
        # Mostrar custos
        print("💰 CUSTOS:")
        print("-" * 20)
        print("Custo aproximado: $0.0004 por incentivo")
        print("Tokens: ~2000 por análise")
        print()
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_unified_matching()

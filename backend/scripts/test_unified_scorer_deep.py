#!/usr/bin/env python3
"""
Teste Profundo do Unified Scorer
Investiga por que todos os scores são 0
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.unified_scorer import UnifiedScorer
from app.db.models import Incentive, Company
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unified_scorer_deep():
    """Teste profundo do Unified Scorer"""
    
    print("🔍 TESTE PROFUNDO DO UNIFIED SCORER")
    print("=" * 50)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    scorer = UnifiedScorer(ai_processor)
    
    try:
        # Obter primeiro incentivo
        incentive = db.query(Incentive).first()
        if not incentive:
            print("❌ Nenhum incentivo encontrado!")
            return
        
        print(f"📋 INCENTIVO: {incentive.title}")
        print(f"🎯 ID: {incentive.incentive_id}")
        print()
        
        # Analisar dados do incentivo
        print("🔍 ANÁLISE DOS DADOS DO INCENTIVO:")
        print("-" * 40)
        
        ai_desc = incentive.ai_description or {}
        print(f"AI Description: {ai_desc}")
        print()
        
        eligible_cae_codes = ai_desc.get('eligible_cae_codes', [])
        eligible_sectors = ai_desc.get('eligible_sectors', [])
        target_region = ai_desc.get('target_region', '')
        target_company_size = ai_desc.get('target_company_size', '')
        
        print(f"CAE Codes Elegíveis: {eligible_cae_codes}")
        print(f"Setores Elegíveis: {eligible_sectors}")
        print(f"Região Alvo: {target_region}")
        print(f"Tamanho Alvo: {target_company_size}")
        print()
        
        # Obter algumas empresas para teste
        companies = db.query(Company).limit(5).all()
        print(f"🏢 TESTANDO COM {len(companies)} EMPRESAS:")
        print("-" * 40)
        
        for i, company in enumerate(companies, 1):
            print(f"\n{i}. {company.company_name}")
            print(f"   CAE Code: {company.cae_primary_code}")
            print(f"   CAE Label: {company.cae_primary_label}")
            print(f"   Região: {company.region}")
            print(f"   Tamanho: {company.company_size}")
            
            # Testar scoring detalhado
            score_data = scorer.score_company(incentive, company)
            print(f"   Score: {score_data['score']}")
            print(f"   Detalhes: {score_data['details']}")
            
            # Análise manual
            print(f"   🔍 ANÁLISE MANUAL:")
            
            # CAE matching
            if company.cae_primary_code and eligible_cae_codes:
                if company.cae_primary_code in eligible_cae_codes:
                    print(f"      ✅ CAE EXATO: {company.cae_primary_code}")
                else:
                    print(f"      ❌ CAE NÃO ENCONTRADO: {company.cae_primary_code} not in {eligible_cae_codes}")
            else:
                print(f"      ⚠️ CAE DADOS FALTAM: company={company.cae_primary_code}, eligible={eligible_cae_codes}")
            
            # Sector matching
            if company.cae_primary_label and eligible_sectors:
                company_sector_lower = company.cae_primary_label.lower()
                found_match = False
                for eligible_sector in eligible_sectors:
                    if company_sector_lower == eligible_sector.lower():
                        print(f"      ✅ SETOR EXATO: {company.cae_primary_label}")
                        found_match = True
                        break
                    elif any(word in company_sector_lower for word in eligible_sector.lower().split()):
                        print(f"      ✅ SETOR PARCIAL: {company.cae_primary_label}")
                        found_match = True
                        break
                
                if not found_match:
                    print(f"      ❌ SETOR NÃO ENCONTRADO: {company.cae_primary_label} not in {eligible_sectors}")
            else:
                print(f"      ⚠️ SETOR DADOS FALTAM: company={company.cae_primary_label}, eligible={eligible_sectors}")
        
        print("\n" + "=" * 50)
        print("🎯 CONCLUSÕES:")
        
        if not eligible_cae_codes and not eligible_sectors:
            print("❌ PROBLEMA: Incentivo não tem CAE codes nem setores elegíveis!")
            print("   Isso explica por que todos os scores são 0.")
        elif not eligible_cae_codes:
            print("⚠️ AVISO: Incentivo não tem CAE codes elegíveis definidos.")
        elif not eligible_sectors:
            print("⚠️ AVISO: Incentivo não tem setores elegíveis definidos.")
        
        print("\n💡 SOLUÇÕES:")
        print("1. Verificar se o AI Processor está gerando dados corretos")
        print("2. Verificar se os incentivos têm dados suficientes")
        print("3. Implementar fallback para incentivos sem dados")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_unified_scorer_deep()

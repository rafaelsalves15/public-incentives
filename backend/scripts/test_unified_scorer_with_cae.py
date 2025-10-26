#!/usr/bin/env python3
"""
Teste do Unified Scorer com incentivo que tem CAE codes
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

def test_unified_scorer_with_cae_codes():
    """Testa o Unified Scorer com incentivo que tem CAE codes"""
    
    print("🎯 TESTE UNIFIED SCORER COM INCENTIVO QUE TEM CAE CODES")
    print("=" * 60)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    scorer = UnifiedScorer(ai_processor)
    
    try:
        # Obter incentivo "Mobilidade a Pedido (IT)"
        incentive = db.query(Incentive).filter(
            Incentive.title.like('%Mobilidade a Pedido%')
        ).first()
        
        if not incentive:
            print("❌ Incentivo 'Mobilidade a Pedido' não encontrado!")
            return
        
        print(f"📋 INCENTIVO: {incentive.title}")
        print()
        
        ai_desc = incentive.ai_description or {}
        eligible_cae_codes = ai_desc.get('eligible_cae_codes', [])
        eligible_sectors = ai_desc.get('eligible_sectors', [])
        
        print(f"🎯 CAE CODES ELEGÍVEIS: {eligible_cae_codes}")
        print(f"🏭 SETORES ELEGÍVEIS: {eligible_sectors}")
        print()
        
        # Obter todas as empresas
        companies = db.query(Company).all()
        print(f"🏢 TESTANDO COM {len(companies)} EMPRESAS:")
        print("-" * 50)
        
        scores = []
        for i, company in enumerate(companies, 1):
            print(f"\n{i}. {company.company_name}")
            print(f"   CAE Code: {company.cae_primary_code}")
            print(f"   CAE Label: {company.cae_primary_label}")
            
            # Testar scoring
            score_data = scorer.score_company(incentive, company)
            score = score_data['score']
            details = score_data['details']
            
            print(f"   Score: {score}")
            if details:
                print(f"   Detalhes: {details}")
            
            scores.append((company.company_name, score, details, company.cae_primary_code))
            
            # Análise específica
            if company.cae_primary_code:
                matches = []
                for cae in company.cae_primary_code:
                    if cae in eligible_cae_codes:
                        matches.append(cae)
                
                if matches:
                    print(f"   🎉 MATCH EXATO COM CAE: {matches}")
                else:
                    print(f"   ❌ CAE {company.cae_primary_code} não está em {eligible_cae_codes}")
            else:
                print(f"   ⚠️ Empresa sem CAE code")
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS SCORES (ORDENADO POR SCORE):")
        print("-" * 50)
        
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score, details, cae_codes) in enumerate(scores, 1):
            print(f"{i:2d}. {name}: {score:3d} pontos")
            if details:
                print(f"     Razões: {details}")
            if cae_codes:
                print(f"     CAE: {cae_codes}")
        
        print(f"\n🎯 CONCLUSÃO:")
        positive_scores = [score for _, score, _, _ in scores if score > 0]
        if positive_scores:
            print(f"✅ Unified Scorer está funcionando! {len(positive_scores)} empresas com score positivo")
            print(f"   Melhor score: {max(positive_scores)}")
            print(f"   Pior score: {min(scores, key=lambda x: x[1])[1]}")
        else:
            print("❌ Nenhuma empresa teve score positivo")
            print("💡 Possíveis causas:")
            print("   - Nenhuma empresa tem CAE codes compatíveis")
            print("   - Lógica de matching precisa ajuste")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_unified_scorer_with_cae_codes()

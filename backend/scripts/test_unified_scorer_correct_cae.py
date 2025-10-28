#!/usr/bin/env python3
"""
Teste do Unified Scorer com CAE Code correto
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

def test_unified_scorer_with_correct_cae():
    """Testa o Unified Scorer com CAE code correto"""
    
    print("🎯 TESTE UNIFIED SCORER COM CAE CODE CORRETO")
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
        print()
        
        # Simular AI description com CAE code correto
        correct_ai_desc = {
            'summary': 'Este benefício fiscal oferece isenção para a Igreja Católica na aquisição de propriedades e bens gratuitos para fins religiosos.',
            'objective': 'Proporcionar isenção tributária para a Igreja Católica em aquisições relacionadas a atividades religiosas.',
            'target_audience': ['Igreja Católica'],
            'eligible_sectors': ['Religião'],
            'eligible_cae_codes': ['94910'],  # CAE code correto para atividades religiosas
            'eligible_regions': [],
            'company_sizes': [],
            'key_requirements': [],
            'funding_details': {'max_funding_percentage': None, 'max_amount': None, 'min_amount': None, 'funding_type': 'tax_benefit'},
            'supported_activities': ['Aquisição de imóveis', 'Aquisição de bens gratuitos'],
            'application_process': 'Não se aplica.',
            'important_notes': []
        }
        
        # Temporariamente substituir a AI description
        original_ai_desc = incentive.ai_description
        incentive.ai_description = correct_ai_desc
        
        print("🔍 TESTANDO COM CAE CODE CORRETO:")
        print(f"CAE Code Elegível: {correct_ai_desc['eligible_cae_codes']}")
        print()
        
        # Obter algumas empresas para teste
        companies = db.query(Company).limit(10).all()
        print(f"🏢 TESTANDO COM {len(companies)} EMPRESAS:")
        print("-" * 40)
        
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
            print(f"   Detalhes: {details}")
            
            scores.append((company.company_name, score, details))
            
            # Análise específica
            if company.cae_primary_code and '94910' in company.cae_primary_code:
                print(f"   🎉 MATCH EXATO COM CAE 94910!")
            elif company.cae_primary_code:
                print(f"   ❌ CAE {company.cae_primary_code} não é 94910")
            else:
                print(f"   ⚠️ Empresa sem CAE code")
        
        # Restaurar AI description original
        incentive.ai_description = original_ai_desc
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS SCORES:")
        print("-" * 30)
        
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, score, details) in enumerate(scores, 1):
            print(f"{i}. {name}: {score} pontos")
            if details:
                print(f"   Razões: {details}")
        
        print(f"\n🎯 CONCLUSÃO:")
        if any(score > 0 for _, score, _ in scores):
            print("✅ Unified Scorer está funcionando corretamente!")
            print("💡 O problema era a falta de CAE codes elegíveis nos incentivos")
        else:
            print("❌ Unified Scorer ainda não está funcionando")
            print("💡 Verificar lógica de matching")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_unified_scorer_with_correct_cae()

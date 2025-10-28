#!/usr/bin/env python3
"""
Teste Específico dos Campos Setor, Região e Tamanho
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

def test_sector_region_size_fields():
    """Testa especificamente os campos setor, região e tamanho"""
    
    print("🔍 TESTE ESPECÍFICO: SETOR, REGIÃO E TAMANHO")
    print("=" * 60)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    scorer = UnifiedScorer(ai_processor)
    
    try:
        # Criar incentivo de teste com dados específicos
        test_incentive_data = {
            'summary': 'Incentivo de teste para verificar setor, região e tamanho',
            'eligible_sectors': ['Tecnologia', 'Software development'],
            'target_region': 'Norte',
            'target_company_size': 'small',
            'eligible_cae_codes': ['62010', '62020'],  # CAE codes de tecnologia
        }
        
        # Criar objeto Incentive mock
        class MockIncentive:
            def __init__(self, data):
                self.ai_description = data
        
        incentive = MockIncentive(test_incentive_data)
        
        print("📋 INCENTIVO DE TESTE:")
        print(f"   Setores elegíveis: {test_incentive_data['eligible_sectors']}")
        print(f"   Região alvo: {test_incentive_data['target_region']}")
        print(f"   Tamanho alvo: {test_incentive_data['target_company_size']}")
        print(f"   CAE codes elegíveis: {test_incentive_data['eligible_cae_codes']}")
        print()
        
        # Obter algumas empresas para teste
        companies = db.query(Company).limit(10).all()
        print(f"🏢 TESTANDO COM {len(companies)} EMPRESAS:")
        print("-" * 50)
        
        for i, company in enumerate(companies, 1):
            print(f"\n{i}. {company.company_name}")
            print(f"   CAE Code: {company.cae_primary_code}")
            print(f"   CAE Label: {company.cae_primary_label}")
            print(f"   Região: {company.region}")
            print(f"   Tamanho: {company.company_size}")
            
            # Testar scoring
            score_data = scorer.score_company(incentive, company)
            score = score_data['score']
            details = score_data['details']
            
            print(f"   Score: {score}")
            print(f"   Detalhes: {details}")
            
            # Análise específica de cada campo
            print(f"   🔍 ANÁLISE DETALHADA:")
            
            # 1. CAE MATCHING
            if company.cae_primary_code and test_incentive_data['eligible_cae_codes']:
                matches = []
                for cae in company.cae_primary_code:
                    if cae in test_incentive_data['eligible_cae_codes']:
                        matches.append(cae)
                
                if matches:
                    print(f"      ✅ CAE MATCH: {matches}")
                else:
                    print(f"      ❌ CAE NO MATCH: {company.cae_primary_code} not in {test_incentive_data['eligible_cae_codes']}")
            else:
                print(f"      ⚠️ CAE DADOS FALTAM")
            
            # 2. SECTOR MATCHING
            if company.cae_primary_label and test_incentive_data['eligible_sectors']:
                company_sector_lower = company.cae_primary_label.lower()
                found_match = False
                
                for eligible_sector in test_incentive_data['eligible_sectors']:
                    eligible_sector_lower = eligible_sector.lower()
                    
                    if company_sector_lower == eligible_sector_lower:
                        print(f"      ✅ SETOR EXATO: '{company.cae_primary_label}' = '{eligible_sector}'")
                        found_match = True
                        break
                    elif any(word in company_sector_lower for word in eligible_sector_lower.split()):
                        print(f"      ✅ SETOR PARCIAL: '{company.cae_primary_label}' contém '{eligible_sector}'")
                        found_match = True
                        break
                
                if not found_match:
                    print(f"      ❌ SETOR NO MATCH: '{company.cae_primary_label}' not in {test_incentive_data['eligible_sectors']}")
            else:
                print(f"      ⚠️ SETOR DADOS FALTAM")
            
            # 3. REGION MATCHING
            if company.region and test_incentive_data['target_region']:
                if company.region.lower() == test_incentive_data['target_region'].lower():
                    print(f"      ✅ REGIÃO MATCH: '{company.region}' = '{test_incentive_data['target_region']}'")
                else:
                    print(f"      ❌ REGIÃO NO MATCH: '{company.region}' != '{test_incentive_data['target_region']}'")
            else:
                print(f"      ⚠️ REGIÃO DADOS FALTAM")
            
            # 4. SIZE MATCHING
            if company.company_size and test_incentive_data['target_company_size']:
                if company.company_size.lower() == test_incentive_data['target_company_size'].lower():
                    print(f"      ✅ TAMANHO MATCH: '{company.company_size}' = '{test_incentive_data['target_company_size']}'")
                else:
                    print(f"      ❌ TAMANHO NO MATCH: '{company.company_size}' != '{test_incentive_data['target_company_size']}'")
            else:
                print(f"      ⚠️ TAMANHO DADOS FALTAM")
        
        print("\n" + "=" * 60)
        print("🎯 CONCLUSÕES:")
        print("1. Verificar se os campos setor, região e tamanho estão sendo comparados corretamente")
        print("2. Verificar se os dados das empresas estão preenchidos")
        print("3. Verificar se a lógica de matching está funcionando")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_sector_region_size_fields()

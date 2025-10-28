#!/usr/bin/env python3
"""
Teste Completo do Matching (Unified Scorer + LLM)
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

def test_complete_matching():
    """Testa o pipeline completo de matching"""
    
    print("🎯 TESTE COMPLETO DO MATCHING (UNIFIED SCORER + LLM)")
    print("=" * 60)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    matcher = CompanyMatcherUnified(ai_processor)
    
    try:
        # Obter incentivo "Mobilidade a Pedido (IT)" que tem CAE codes
        incentive = db.query(Incentive).filter(
            Incentive.title.like('%Mobilidade a Pedido%')
        ).first()
        
        if not incentive:
            print("❌ Incentivo 'Mobilidade a Pedido' não encontrado!")
            return
        
        print(f"📋 INCENTIVO: {incentive.title}")
        print()
        
        ai_desc = incentive.ai_description or {}
        print(f"🎯 CAE CODES ELEGÍVEIS: {ai_desc.get('eligible_cae_codes', [])}")
        print(f"🏭 SETORES ELEGÍVEIS: {ai_desc.get('eligible_sectors', [])}")
        print(f"🌍 REGIÃO ALVO: {ai_desc.get('target_region', 'N/A')}")
        print(f"📏 TAMANHO ALVO: {ai_desc.get('target_company_size', 'N/A')}")
        print()
        
        # Testar matching completo
        print("🔍 INICIANDO MATCHING COMPLETO...")
        print("-" * 40)
        
        matches = matcher.find_top_matches(
            session=db,
            incentive_id=incentive.incentive_id,
            limit=5
        )
        
        print(f"✅ MATCHING CONCLUÍDO!")
        print(f"📊 RESULTADOS: {len(matches)} matches encontrados")
        print()
        
        # Mostrar resultados detalhados
        print("🏆 TOP 5 MATCHES (UNIFIED SCORER + LLM):")
        print("=" * 60)
        
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['company_name']}")
            print(f"   📊 Score Unificado: {match['unified_score']}")
            print(f"   🤖 Score LLM: {match['llm_score']}")
            print(f"   🏷️ CAE: {match.get('cae_primary_label', 'N/A')}")
            print(f"   📝 Razões LLM: {match.get('llm_reasons', [])}")
            print(f"   📍 Razões Unificadas: {match.get('unified_reasons', [])}")
            
            # Análise da qualidade do match
            total_score = match['unified_score'] + (match['llm_score'] * 100)  # Normalizar LLM score
            print(f"   🎯 Score Total Estimado: {total_score:.1f}")
            
            if match['unified_score'] > 0:
                print(f"   ✅ Tem características desejadas (Unified Score > 0)")
            else:
                print(f"   ⚠️ Sem características desejadas (Unified Score = 0)")
        
        print("\n" + "=" * 60)
        print("📊 ANÁLISE DOS RESULTADOS:")
        print("-" * 30)
        
        # Estatísticas
        unified_scores = [m['unified_score'] for m in matches]
        llm_scores = [m['llm_score'] for m in matches]
        
        print(f"Unified Scores: {unified_scores}")
        print(f"LLM Scores: {[f'{s:.2f}' for s in llm_scores]}")
        
        positive_unified = sum(1 for s in unified_scores if s > 0)
        high_llm = sum(1 for s in llm_scores if s > 0.5)
        
        print(f"\n✅ Empresas com Unified Score > 0: {positive_unified}/5")
        print(f"✅ Empresas com LLM Score > 0.5: {high_llm}/5")
        
        # Verificar se TRANSPORTELA está nos resultados
        transportela_found = any('TRANSPORTELA' in m['company_name'].upper() for m in matches)
        if transportela_found:
            print(f"🎉 TRANSPORTELA encontrada nos resultados!")
        else:
            print(f"⚠️ TRANSPORTELA não encontrada nos resultados")
        
        print("\n🎯 CONCLUSÕES:")
        if positive_unified > 0:
            print("✅ Unified Scorer está funcionando (encontrou empresas com características desejadas)")
        else:
            print("❌ Unified Scorer não encontrou empresas com características desejadas")
        
        if high_llm > 0:
            print("✅ LLM está funcionando (encontrou empresas com boa compatibilidade)")
        else:
            print("❌ LLM não encontrou empresas com boa compatibilidade")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_complete_matching()

#!/usr/bin/env python3
"""
Teste Específico: 5 Incentivos + 200 Empresas
Testa o sistema de matching com output claro e tracking de custos
"""

import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.database import SessionLocal
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.services.ai_processor import AIProcessor
from app.db.models import Incentive, Company, AICostTracking
from sqlalchemy.orm import Session

# Configure logging - silencioso para output limpo
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def test_5_incentives_200_companies():
    """Testa 5 incentivos com 200 empresas"""
    
    print("🎯 TESTE ESPECÍFICO: 5 INCENTIVOS + 200 EMPRESAS")
    print("=" * 70)
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize database
    db = SessionLocal()
    
    try:
        # Check OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY não configurada!")
            return
        
        # Initialize services
        ai_processor = AIProcessor(api_key=api_key, session=db)
        matcher = CompanyMatcherUnified(ai_processor)
        
        # Get 5 incentives
        incentives = db.query(Incentive).limit(5).all()
        if len(incentives) < 5:
            print(f"❌ Apenas {len(incentives)} incentivos disponíveis. Precisa de pelo menos 5.")
            return
        
        # Get 200 companies
        companies = db.query(Company).limit(200).all()
        if len(companies) < 200:
            print(f"⚠️ Apenas {len(companies)} empresas disponíveis (objetivo: 200)")
        
        print(f"📊 DADOS DO TESTE:")
        print(f"   • Incentivos: {len(incentives)}")
        print(f"   • Empresas: {len(companies)}")
        print(f"   • Total combinações: {len(incentives) * len(companies):,}")
        print()
        
        # Track costs before test
        start_time = datetime.now()
        cost_before = get_total_cost(db)
        
        print("🚀 INICIANDO PROCESSAMENTO...")
        print("=" * 70)
        
        all_results = []
        successful_incentives = 0
        total_matches = 0
        
        for i, incentive in enumerate(incentives, 1):
            print(f"\n[{i}/5] 📋 {incentive.title[:60]}...")
            print("-" * 70)
            
            try:
                # Find matches
                matches = matcher.find_top_matches(
                    db, 
                    str(incentive.incentive_id),
                    limit=5
                )
                
                if matches:
                    print(f"✅ {len(matches)} matches encontrados:")
                    successful_incentives += 1
                    total_matches += len(matches)
                    
                    # Show all 5 matches with details
                    for j, match in enumerate(matches, 1):
                        company_name = match.get('company_name', 'N/A')
                        llm_score = match.get('llm_score', 0)
                        unified_score = match.get('unified_score', 0)
                        reasons = match.get('llm_reasons', [])
                        
                        print(f"   {j}. {company_name}")
                        print(f"      💯 LLM Score: {llm_score:.2f} | Unified Score: {unified_score:.1f}")
                        if reasons:
                            print(f"      💡 Razões: {' | '.join(reasons[:2])}")
                        print()
                    
                    # Store results
                    all_results.append({
                        'incentive_id': str(incentive.incentive_id),
                        'incentive_title': incentive.title,
                        'matches': matches
                    })
                    
                else:
                    print("❌ Nenhum match encontrado")
                    
            except Exception as e:
                print(f"❌ Erro: {e}")
        
        # Final results
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        cost_after = get_total_cost(db)
        test_cost = cost_after - cost_before
        
        print("\n" + "=" * 70)
        print("📊 RESUMO FINAL DO TESTE")
        print("=" * 70)
        print(f"✅ Incentivos processados com sucesso: {successful_incentives}/5")
        print(f"❌ Incentivos falhados: {5 - successful_incentives}/5")
        print(f"📈 Total matches gerados: {total_matches}")
        print(f"⏱️ Tempo total: {duration:.1f}s")
        print(f"⚡ Tempo médio por incentivo: {duration/5:.1f}s")
        
        print(f"\n💰 CUSTOS:")
        print(f"   • Custo antes do teste: ${cost_before:.4f}")
        print(f"   • Custo após o teste: ${cost_after:.4f}")
        print(f"   • Custo do teste: ${test_cost:.4f}")
        print(f"   • Custo por incentivo: ${test_cost/5:.4f}")
        print(f"   • Custo por match: ${test_cost/total_matches:.4f}" if total_matches > 0 else "   • Custo por match: N/A")
        
        # Show detailed results summary
        print(f"\n📋 RESUMO POR INCENTIVO:")
        print("-" * 70)
        for i, result in enumerate(all_results, 1):
            print(f"{i}. {result['incentive_title'][:50]}...")
            print(f"   Matches: {len(result['matches'])}")
            if result['matches']:
                best_match = result['matches'][0]
                print(f"   Melhor match: {best_match.get('company_name', 'N/A')[:40]} (Score: {best_match.get('llm_score', 0):.2f})")
            print()
        
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def get_total_cost(db: Session) -> float:
    """Obtém o custo total atual da base de dados"""
    try:
        total_cost = db.query(AICostTracking).with_entities(
            db.func.sum(AICostTracking.total_cost)
        ).scalar()
        return float(total_cost) if total_cost else 0.0
    except:
        return 0.0

if __name__ == "__main__":
    test_5_incentives_200_companies()

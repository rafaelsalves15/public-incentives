#!/usr/bin/env python3
"""
Teste do Sistema Híbrido com Monitorização de Custos em Tempo Real

Este script testa o sistema híbrido e mostra todos os custos da OpenAI API
em tempo real, incluindo:
- Custos de embeddings
- Custos de LLM
- Cache hits/misses
- Economias totais
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_database_service import VectorDatabaseService
from app.services.hybrid_matching_service import HybridMatchingService
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.db.models import Incentive, Company, IncentiveMetadata
import logging
import time
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_hybrid_matching_with_cost_tracking():
    """Testa o sistema híbrido com monitorização completa de custos"""
    
    print("🚀 TESTE DO SISTEMA HÍBRIDO COM MONITORIZAÇÃO DE CUSTOS")
    print("=" * 70)
    
    # Inicializar serviços
    db = SessionLocal()
    
    try:
        # 1. Inicializar serviços
        print("🔧 Inicializando serviços...")
        ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
        embedding_service = EmbeddingService(api_key=os.getenv('OPENAI_API_KEY'), session=db)
        vector_db_service = VectorDatabaseService(embedding_service)
        hybrid_service = HybridMatchingService(ai_processor, embedding_service, vector_db_service)
        
        # Sistema original para comparação
        original_matcher = CompanyMatcherUnified(ai_processor)
        
        print("✅ Serviços inicializados")
        print()
        
        # 2. Mostrar estatísticas iniciais de custos
        print("💰 ESTATÍSTICAS INICIAIS DE CUSTOS")
        print("-" * 50)
        initial_stats = ai_processor.cost_tracker.get_total_stats()
        print(f"Total histórico: {initial_stats['all_time']['total_cost_formatted']}")
        print(f"Total de chamadas: {initial_stats['all_time']['total_calls']}")
        print()
        
        # 3. Obter incentivo de teste
        print("📋 Selecionando incentivo de teste...")
        incentive = db.query(Incentive).filter(
            Incentive.title.like('%Digitalização%')
        ).first()
        
        if not incentive:
            print("❌ Incentivo 'Digitalização' não encontrado!")
            return
        
        print(f"🎯 INCENTIVO: {incentive.title}")
        print(f"📝 Descrição: {incentive.description[:100]}...")
        
        ai_desc = incentive.ai_description or {}
        print(f"🏭 CAE Codes Elegíveis: {ai_desc.get('eligible_cae_codes', [])}")
        print(f"🌍 Setores Elegíveis: {ai_desc.get('eligible_sectors', [])}")
        print()
        
        # 4. Resetar estatísticas de sessão para teste limpo
        ai_processor.cost_tracker.reset_session_stats()
        embedding_service.cost_tracker.reset_session_stats()
        
        print("🔄 Estatísticas de sessão resetadas para teste limpo")
        print()
        
        # 5. Testar sistema híbrido com tracking visual
        print("🧠 TESTANDO SISTEMA HÍBRIDO...")
        print("-" * 50)
        
        # Iniciar tracking visual do incentivo
        ai_processor.cost_tracker.start_incentive(incentive.title, 1, 1)
        
        start_time = time.time()
        
        hybrid_matches = hybrid_service.find_top_matches(
            session=db,
            incentive_id=str(incentive.incentive_id),
            limit=5,
            use_hybrid=True
        )
        
        hybrid_time = time.time() - start_time
        
        # Finalizar tracking visual
        ai_processor.cost_tracker.end_incentive()
        
        print(f"✅ Sistema Híbrido: {len(hybrid_matches)} matches em {hybrid_time:.2f}s")
        print()
        
        # 6. Testar sistema original para comparação
        print("🔄 TESTANDO SISTEMA ORIGINAL...")
        print("-" * 50)
        
        # Resetar estatísticas para teste original
        ai_processor.cost_tracker.reset_session_stats()
        
        # Iniciar tracking visual
        ai_processor.cost_tracker.start_incentive(f"{incentive.title} (Original)", 1, 1)
        
        start_time = time.time()
        
        original_matches = hybrid_service.find_top_matches(
            session=db,
            incentive_id=str(incentive.incentive_id),
            limit=5,
            use_hybrid=False
        )
        
        original_time = time.time() - start_time
        
        # Finalizar tracking visual
        ai_processor.cost_tracker.end_incentive()
        
        print(f"✅ Sistema Original: {len(original_matches)} matches em {original_time:.2f}s")
        print()
        
        # 7. Análise detalhada de custos
        print("💰 ANÁLISE DETALHADA DE CUSTOS")
        print("=" * 70)
        
        # Estatísticas finais
        final_stats = ai_processor.cost_tracker.get_total_stats()
        
        print("📊 ESTATÍSTICAS GERAIS:")
        print(f"   Total histórico: {final_stats['all_time']['total_cost_formatted']}")
        print(f"   Total de chamadas: {final_stats['all_time']['total_calls']}")
        print(f"   Cache hit rate: {final_stats['all_time']['cache_stats']['hit_rate']:.1f}%")
        print()
        
        print("📈 BREAKDOWN POR OPERAÇÃO:")
        for op in final_stats['by_operation']:
            print(f"   {op['operation']:25}: {op['calls']:3} chamadas, ${op['cost']:.6f}, ${op['avg_cost_per_call']:.6f}/chamada")
        
        print()
        
        # 8. Comparação de resultados
        print("📊 COMPARAÇÃO DE RESULTADOS")
        print("=" * 70)
        
        print("🏆 SISTEMA HÍBRIDO (com embeddings):")
        print("-" * 40)
        
        for i, match in enumerate(hybrid_matches, 1):
            print(f"\n{i}. {match['company_name']}")
            print(f"   🧠 Similaridade Semântica: {match['semantic_similarity']:.3f}")
            print(f"   📊 Score Unificado: {match['unified_score']}")
            print(f"   🤖 Score LLM: {match['llm_score']:.3f}")
            print(f"   🎯 Score Total: {match['total_score']:.3f}")
            print(f"   🏷️ CAE: {match.get('cae_primary_label', 'N/A')}")
        
        print("\n🔄 SISTEMA ORIGINAL (sem embeddings):")
        print("-" * 40)
        
        for i, match in enumerate(original_matches, 1):
            print(f"\n{i}. {match['company_name']}")
            print(f"   🧠 Similaridade Semântica: {match['semantic_similarity']:.3f} (N/A)")
            print(f"   📊 Score Unificado: {match['unified_score']}")
            print(f"   🤖 Score LLM: {match['llm_score']:.3f}")
            print(f"   🎯 Score Total: {match['total_score']:.3f}")
            print(f"   🏷️ CAE: {match.get('cae_primary_label', 'N/A')}")
        
        # 9. Análise de performance e custos
        print("\n📈 ANÁLISE DE PERFORMANCE E CUSTOS")
        print("=" * 70)
        
        # Tempo de execução
        time_improvement = ((original_time - hybrid_time) / original_time) * 100 if original_time > 0 else 0
        print(f"⏱️ Tempo de Execução:")
        print(f"   Sistema Híbrido: {hybrid_time:.2f}s")
        print(f"   Sistema Original: {original_time:.2f}s")
        print(f"   Melhoria: {time_improvement:+.1f}%")
        
        # Qualidade dos matches
        hybrid_avg_score = sum(m['total_score'] for m in hybrid_matches) / len(hybrid_matches) if hybrid_matches else 0
        original_avg_score = sum(m['total_score'] for m in original_matches) / len(original_matches) if original_matches else 0
        
        print(f"\n🎯 Qualidade dos Matches:")
        print(f"   Score Médio Híbrido: {hybrid_avg_score:.3f}")
        print(f"   Score Médio Original: {original_avg_score:.3f}")
        print(f"   Melhoria: {((hybrid_avg_score - original_avg_score) / original_avg_score * 100):+.1f}%" if original_avg_score > 0 else "N/A")
        
        # 10. Conclusões e recomendações
        print("\n🎯 CONCLUSÕES E RECOMENDAÇÕES")
        print("=" * 70)
        
        if hybrid_avg_score > original_avg_score:
            print("✅ Sistema Híbrido mostra MELHOR qualidade de matching")
        elif hybrid_avg_score == original_avg_score:
            print("⚖️ Sistema Híbrido mostra QUALIDADE EQUIVALENTE")
        else:
            print("⚠️ Sistema Híbrido mostra qualidade INFERIOR (pode precisar de ajustes)")
        
        if time_improvement > 0:
            print(f"✅ Sistema Híbrido é {time_improvement:.1f}% MAIS RÁPIDO")
        else:
            print(f"⚠️ Sistema Híbrido é {abs(time_improvement):.1f}% MAIS LENTO")
        
        print("\n🚀 RECOMENDAÇÕES:")
        print("- Sistema Híbrido é recomendado para produção")
        print("- Monitore custos regularmente usando o CostTracker")
        print("- Considere popular base de dados vectorial completa para melhor cobertura")
        print("- Use cache persistente para reduzir custos de embeddings")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def show_cost_summary():
    """Mostra resumo de custos do sistema"""
    
    print("\n💰 RESUMO DE CUSTOS DO SISTEMA")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
        stats = ai_processor.cost_tracker.get_total_stats()
        
        print(f"Total histórico: {stats['all_time']['total_cost_formatted']}")
        print(f"Total de chamadas: {stats['all_time']['total_calls']}")
        print(f"Cache hit rate: {stats['all_time']['cache_stats']['hit_rate']:.1f}%")
        print(f"Custo médio por chamada: ${stats['all_time']['average_cost_per_call']:.6f}")
        
        print("\nBreakdown por operação:")
        for op in stats['by_operation']:
            print(f"  {op['operation']:25}: ${op['cost']:.6f} ({op['calls']} chamadas)")
        
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_hybrid_matching_with_cost_tracking()
    show_cost_summary()

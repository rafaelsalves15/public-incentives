#!/usr/bin/env python3
"""
Teste do Sistema Híbrido de Matching com Embeddings

Este script testa o novo sistema híbrido que combina:
1. Busca Semântica (Vector Search) 
2. Scoring Determinístico (Unified Scorer)
3. Refinamento LLM (AI Processor)

Compara performance com o sistema original e mostra melhorias.
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

def test_hybrid_matching_system():
    """Testa o sistema híbrido completo"""
    
    print("🚀 TESTE DO SISTEMA HÍBRIDO DE MATCHING COM EMBEDDINGS")
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
        
        # 2. Obter incentivo de teste
        print("📋 Selecionando incentivo de teste...")
        incentive = db.query(Incentive).filter(
            Incentive.title.like('%Mobilidade a Pedido%')
        ).first()
        
        if not incentive:
            print("❌ Incentivo 'Mobilidade a Pedido' não encontrado!")
            return
        
        print(f"🎯 INCENTIVO: {incentive.title}")
        print(f"📝 Descrição: {incentive.description[:100]}...")
        
        ai_desc = incentive.ai_description or {}
        print(f"🏭 CAE Codes Elegíveis: {ai_desc.get('eligible_cae_codes', [])}")
        print(f"🌍 Setores Elegíveis: {ai_desc.get('eligible_sectors', [])}")
        print()
        
        # 3. Popular base de dados vectorial (se necessário)
        print("🗄️ Verificando base de dados vectorial...")
        db_stats = vector_db_service.get_database_stats()
        
        if db_stats['companies_count'] == 0:
            print("📊 Populando base de dados vectorial...")
            print("   (Isso pode demorar alguns minutos na primeira execução)")
            
            # Popular com uma amostra de empresas para teste
            sample_companies = db.query(Company).limit(100).all()
            vector_db_service.batch_populate_database(
                session=db,
                company_ids=[str(c.company_id) for c in sample_companies]
            )
            
            print("✅ Base de dados vectorial populada")
        else:
            print(f"✅ Base de dados vectorial já populada: {db_stats['companies_count']} empresas")
        
        print()
        
        # 4. Testar sistema híbrido
        print("🧠 TESTANDO SISTEMA HÍBRIDO...")
        print("-" * 50)
        
        start_time = time.time()
        
        hybrid_matches = hybrid_service.find_top_matches(
            session=db,
            incentive_id=str(incentive.incentive_id),
            limit=5,
            use_hybrid=True
        )
        
        hybrid_time = time.time() - start_time
        
        print(f"✅ Sistema Híbrido: {len(hybrid_matches)} matches em {hybrid_time:.2f}s")
        print()
        
        # 5. Testar sistema original
        print("🔄 TESTANDO SISTEMA ORIGINAL...")
        print("-" * 50)
        
        start_time = time.time()
        
        original_matches = hybrid_service.find_top_matches(
            session=db,
            incentive_id=str(incentive.incentive_id),
            limit=5,
            use_hybrid=False
        )
        
        original_time = time.time() - start_time
        
        print(f"✅ Sistema Original: {len(original_matches)} matches em {original_time:.2f}s")
        print()
        
        # 6. Comparar resultados
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
            print(f"   📝 Razões LLM: {match.get('llm_reasons', [])}")
        
        print("\n🔄 SISTEMA ORIGINAL (sem embeddings):")
        print("-" * 40)
        
        for i, match in enumerate(original_matches, 1):
            print(f"\n{i}. {match['company_name']}")
            print(f"   🧠 Similaridade Semântica: {match['semantic_similarity']:.3f} (N/A)")
            print(f"   📊 Score Unificado: {match['unified_score']}")
            print(f"   🤖 Score LLM: {match['llm_score']:.3f}")
            print(f"   🎯 Score Total: {match['total_score']:.3f}")
            print(f"   🏷️ CAE: {match.get('cae_primary_label', 'N/A')}")
            print(f"   📝 Razões LLM: {match.get('llm_reasons', [])}")
        
        # 7. Análise de performance
        print("\n📈 ANÁLISE DE PERFORMANCE")
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
        
        # Diversidade semântica
        hybrid_semantic_scores = [m['semantic_similarity'] for m in hybrid_matches if m['semantic_similarity'] > 0]
        if hybrid_semantic_scores:
            print(f"\n🧠 Diversidade Semântica (Híbrido):")
            print(f"   Similaridade Média: {sum(hybrid_semantic_scores) / len(hybrid_semantic_scores):.3f}")
            print(f"   Range: {min(hybrid_semantic_scores):.3f} - {max(hybrid_semantic_scores):.3f}")
        
        # 8. Estatísticas do sistema
        print("\n📊 ESTATÍSTICAS DO SISTEMA")
        print("=" * 70)
        
        matching_stats = hybrid_service.get_matching_stats()
        print(f"🗄️ Base de Dados Vectorial:")
        print(f"   Empresas: {matching_stats['vector_database_stats']['companies_count']}")
        print(f"   Incentivos: {matching_stats['vector_database_stats']['incentives_count']}")
        
        cache_stats = matching_stats['embedding_cache_stats']
        print(f"\n💾 Cache de Embeddings:")
        print(f"   Cache Hits: {cache_stats['cache_hits']}")
        print(f"   Cache Misses: {cache_stats['cache_misses']}")
        print(f"   Taxa de Hit: {cache_stats['hit_rate_percentage']:.1f}%")
        print(f"   Economia Estimada: ${cache_stats['estimated_savings_usd']:.4f}")
        
        # 9. Conclusões
        print("\n🎯 CONCLUSÕES")
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
        
        if hybrid_semantic_scores:
            print("✅ Sistema Híbrido oferece BUSCA SEMÂNTICA adicional")
        
        print("\n🚀 RECOMENDAÇÕES:")
        print("- Sistema Híbrido é recomendado para produção")
        print("- Monitore performance e ajuste thresholds conforme necessário")
        print("- Considere popular base de dados vectorial completa para melhor cobertura")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_embedding_generation():
    """Testa geração de embeddings individual"""
    
    print("\n🧪 TESTE DE GERAÇÃO DE EMBEDDINGS")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        embedding_service = EmbeddingService(api_key=os.getenv('OPENAI_API_KEY'), session=db)
        
        # Testar incentivo
        incentive = db.query(Incentive).first()
        if incentive:
            print(f"📋 Testando embedding para incentivo: {incentive.title[:50]}...")
            embedding = embedding_service.generate_incentive_embedding(incentive)
            if embedding:
                print(f"✅ Embedding gerado: {len(embedding)} dimensões")
            else:
                print("❌ Falha na geração do embedding")
        
        # Testar empresa
        company = db.query(Company).first()
        if company:
            print(f"🏢 Testando embedding para empresa: {company.company_name[:50]}...")
            embedding = embedding_service.generate_company_embedding(company)
            if embedding:
                print(f"✅ Embedding gerado: {len(embedding)} dimensões")
            else:
                print("❌ Falha na geração do embedding")
        
        # Estatísticas do cache
        cache_stats = embedding_service.get_cache_stats()
        print(f"\n💾 Estatísticas do Cache:")
        print(f"   Hits: {cache_stats['cache_hits']}")
        print(f"   Misses: {cache_stats['cache_misses']}")
        print(f"   Taxa de Hit: {cache_stats['hit_rate_percentage']:.1f}%")
        
    except Exception as e:
        logger.error(f"Erro no teste de embeddings: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_hybrid_matching_system()
    test_embedding_generation()

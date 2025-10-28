#!/usr/bin/env python3
"""
Script de teste visual para sistema de matching com tracking de custos.

Este script testa o sistema de matching entre incentivos e empresas e mostra:
- Progresso em tempo real
- Custos de LLM
- Qualidade dos matches
- Estatísticas de performance
"""

import sys
import os
import argparse
import time
from datetime import datetime

# Adicionar o path da aplicação
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.company_matcher_unified import CompanyMatcherUnified
from app.db.models import Incentive, Company, IncentiveCompanyMatch
from sqlalchemy.orm import Session


def print_header():
    """Imprime cabeçalho do script"""
    print("=" * 80)
    print("🎯 TESTE DE MATCHING VISUAL")
    print("=" * 80)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def print_progress_bar(current: int, total: int, width: int = 50):
    """Imprime barra de progresso"""
    progress = current / total if total > 0 else 0
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = progress * 100
    print(f"\r📊 Progresso: [{bar}] {percentage:.1f}% ({current}/{total})", end="", flush=True)


def print_match_summary(matches: list, incentive_title: str):
    """Imprime resumo dos matches"""
    print(f"\n🏆 Top 5 matches para: {incentive_title[:60]}...")
    print("-" * 60)
    
    for i, match in enumerate(matches[:5], 1):
        company_name = match.get('company_name', 'N/A')
        score = match.get('match_score', 0)
        reasons = match.get('reasons', [])
        
        print(f"{i}. {company_name}")
        print(f"   Score: {score:.3f}")
        print(f"   Razões: {', '.join(reasons[:2])}")  # Mostrar apenas 2 razões
        print()


def test_single_incentive(db: Session, ai_processor: AIProcessor):
    """Testa matching com um único incentivo"""
    print_header()
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: OPENAI_API_KEY não configurada!")
        return False
    
    # Obter primeiro incentivo
    incentive = db.query(Incentive).first()
    if not incentive:
        print("❌ Nenhum incentivo encontrado na base de dados!")
        return False
    
    print(f"🎯 Testando com incentivo: {incentive.title}")
    print()
    
    # Inicializar matcher
    matcher = CompanyMatcherUnified(ai_processor)
    
    # Executar matching
    print("🔄 Executando matching...")
    start_time = time.time()
    
    try:
        result = matcher.process_incentive_matches(db, str(incentive.incentive_id))
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result['success']:
            print(f"✅ Matching concluído em {duration:.2f} segundos")
            print(f"📊 Matches encontrados: {result['matches_count']}")
            
            # Mostrar top 5 matches
            print_match_summary(result['matches'], incentive.title)
            
            return True
        else:
            print(f"❌ Falha no matching: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_sample_incentives(db: Session, ai_processor: AIProcessor):
    """Testa matching com sample de incentivos"""
    print_header()
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: OPENAI_API_KEY não configurada!")
        return False
    
    # Obter incentivos com AI description (processados)
    incentives = db.query(Incentive).filter(
        Incentive.ai_description.isnot(None)
    ).limit(5).all()
    
    if not incentives:
        print("❌ Nenhum incentivo processado encontrado!")
        print("   Execute primeiro: make process-ai")
        return False
    
    print(f"📋 Testando com {len(incentives)} incentivos processados")
    print(f"🎯 Modelo: GPT-4o-mini")
    print(f"💰 Custo estimado: ~${len(incentives) * 0.01:.4f}")
    print()
    
    # Inicializar matcher
    matcher = CompanyMatcherUnified(ai_processor)
    
    # Processar cada incentivo
    success_count = 0
    failed_count = 0
    total_matches = 0
    start_time = time.time()
    
    for i, incentive in enumerate(incentives, 1):
        try:
            print_progress_bar(i - 1, len(incentives))
            print(f"\n🔄 Processando {i}/{len(incentives)}: {incentive.title[:60]}...")
            
            result = matcher.process_incentive_matches(db, str(incentive.incentive_id))
            
            if result['success']:
                success_count += 1
                total_matches += result['matches_count']
                print(f"✅ {result['matches_count']} matches encontrados")
                
                # Mostrar top 3 matches
                if result['matches']:
                    print("🏆 Top 3:")
                    for j, match in enumerate(result['matches'][:3], 1):
                        print(f"   {j}. {match['company_name']} (score: {match['match_score']:.3f})")
            else:
                failed_count += 1
                print(f"❌ Falhou: {result['error']}")
            
        except Exception as e:
            failed_count += 1
            print(f"❌ Erro: {str(e)}")
    
    # Finalizar barra de progresso
    print_progress_bar(len(incentives), len(incentives))
    
    # Resumo final
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("🎉 TESTE DE MATCHING CONCLUÍDO!")
    print("=" * 80)
    print(f"⏱️  Duração: {duration:.1f} segundos")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Falhas: {failed_count}")
    print(f"📊 Total de matches: {total_matches}")
    print(f"📈 Média por incentivo: {total_matches / success_count if success_count > 0 else 0:.1f}")
    
    return success_count > 0


def test_full_dataset(db: Session, ai_processor: AIProcessor):
    """Testa matching com dataset completo"""
    print_header()
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: OPENAI_API_KEY não configurada!")
        return False
    
    # Obter todos os incentivos processados
    incentives = db.query(Incentive).filter(
        Incentive.ai_description.isnot(None)
    ).all()
    
    if not incentives:
        print("❌ Nenhum incentivo processado encontrado!")
        print("   Execute primeiro: make process-ai")
        return False
    
    total_incentives = len(incentives)
    estimated_cost = total_incentives * 0.01
    
    print(f"📋 Dataset completo: {total_incentives} incentivos")
    print(f"🎯 Modelo: GPT-4o-mini")
    print(f"💰 Custo estimado: ~${estimated_cost:.2f}")
    print()
    
    # Confirmação
    response = input("⚠️  Confirmar processamento completo? (y/N): ")
    if response.lower() != 'y':
        print("❌ Processamento cancelado")
        return False
    
    print("\n🚀 Iniciando processamento completo...")
    print()
    
    # Inicializar matcher
    matcher = CompanyMatcherUnified(ai_processor)
    
    # Processar todos os incentivos
    success_count = 0
    failed_count = 0
    total_matches = 0
    start_time = time.time()
    
    for i, incentive in enumerate(incentives, 1):
        try:
            print_progress_bar(i - 1, total_incentives)
            
            if i % 10 == 0 or i == total_incentives:
                print(f"\n📊 Progresso: {i}/{total_incentives} ({i/total_incentives*100:.1f}%)")
            
            result = matcher.process_incentive_matches(db, str(incentive.incentive_id))
            
            if result['success']:
                success_count += 1
                total_matches += result['matches_count']
            else:
                failed_count += 1
            
        except Exception as e:
            failed_count += 1
            print(f"\n❌ Erro no incentivo {i}: {str(e)}")
    
    # Finalizar barra de progresso
    print_progress_bar(total_incentives, total_incentives)
    
    # Resumo final
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("🎉 PROCESSAMENTO COMPLETO CONCLUÍDO!")
    print("=" * 80)
    print(f"⏱️  Duração: {duration:.1f} segundos")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Falhas: {failed_count}")
    print(f"📊 Total de matches: {total_matches}")
    print(f"📈 Taxa de sucesso: {(success_count / total_incentives * 100):.1f}%")
    
    return success_count > 0


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Teste visual de matching")
    parser.add_argument("--single", action="store_true", help="Testar com um único incentivo")
    parser.add_argument("--sample", action="store_true", help="Testar com sample de incentivos")
    parser.add_argument("--full", action="store_true", help="Testar com dataset completo")
    args = parser.parse_args()
    
    # Obter sessão da base de dados
    db = SessionLocal()
    
    try:
        # Verificar se há dados na base de dados
        total_incentives = db.query(Incentive).count()
        total_companies = db.query(Company).count()
        
        if total_incentives == 0:
            print("❌ Nenhum incentivo encontrado na base de dados!")
            print("   Execute primeiro: make setup-sample")
            return False
        
        if total_companies == 0:
            print("❌ Nenhuma empresa encontrada na base de dados!")
            print("   Execute primeiro: make setup-sample")
            return False
        
        print(f"📊 Base de dados: {total_incentives} incentivos, {total_companies} empresas")
        
        # Inicializar AI processor
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY não configurada!")
            return False
        
        ai_processor = AIProcessor(api_key, db)
        
        # Executar teste baseado nos argumentos
        if args.single:
            success = test_single_incentive(db, ai_processor)
        elif args.sample:
            success = test_sample_incentives(db, ai_processor)
        elif args.full:
            success = test_full_dataset(db, ai_processor)
        else:
            # Default: teste com sample
            success = test_sample_incentives(db, ai_processor)
        
        return success
        
    except Exception as e:
        print(f"❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

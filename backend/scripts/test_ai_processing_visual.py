#!/usr/bin/env python3
"""
Script de teste visual para processamento de IA com tracking de custos em tempo real.

Este script processa incentivos com IA e mostra:
- Progresso em tempo real
- Custos acumulados
- Cache hits/misses
- Status de cada operação
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
from app.db.models import Incentive, IncentiveMetadata
from sqlalchemy.orm import Session


def print_header():
    """Imprime cabeçalho do script"""
    print("=" * 80)
    print("🤖 PROCESSAMENTO DE IA COM TRACKING VISUAL")
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


def print_cost_summary(ai_processor: AIProcessor):
    """Imprime resumo de custos"""
    print("\n" + "=" * 60)
    print("💰 RESUMO DE CUSTOS")
    print("=" * 60)
    
    # Cache statistics
    cache_hits = ai_processor._cache_hits
    cache_misses = ai_processor._cache_misses
    total_cache_calls = cache_hits + cache_misses
    hit_rate = (cache_hits / total_cache_calls * 100) if total_cache_calls > 0 else 0
    
    print(f"🎯 Cache Hits: {cache_hits}")
    print(f"❌ Cache Misses: {cache_misses}")
    print(f"📈 Hit Rate: {hit_rate:.1f}%")
    
    if cache_hits > 0:
        print(f"💡 Economia estimada: ~${cache_hits * 0.001:.4f} (cache hits)")
    
    print()


def process_incentives_visual(db: Session, ai_processor: AIProcessor, auto_run: bool = False):
    """
    Processa incentivos com visualização em tempo real.
    
    Args:
        db: Sessão da base de dados
        ai_processor: Instância do AIProcessor
        auto_run: Se True, processa automaticamente sem confirmação
    """
    print_header()
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERRO: OPENAI_API_KEY não configurada!")
        print("   Configure a variável de ambiente antes de executar.")
        return False
    
    # Obter incentivos pendentes
    pending_incentives = db.query(Incentive).join(IncentiveMetadata).filter(
        IncentiveMetadata.ai_processing_status == "pending"
    ).all()
    
    total_pending = len(pending_incentives)
    
    if total_pending == 0:
        print("✅ Todos os incentivos já foram processados!")
        print("   Status: Não há incentivos com status 'pending'")
        return True
    
    print(f"📋 Incentivos pendentes: {total_pending}")
    print(f"🎯 Modelo: GPT-4o-mini")
    print(f"💰 Custo estimado: ~${total_pending * 0.001:.4f}")
    print()
    
    if not auto_run:
        response = input("🤔 Continuar com o processamento? (y/N): ")
        if response.lower() != 'y':
            print("❌ Processamento cancelado pelo utilizador")
            return False
    
    print("\n🚀 Iniciando processamento...")
    print()
    
    # Processar cada incentivo
    success_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, incentive in enumerate(pending_incentives, 1):
        try:
            # Atualizar barra de progresso
            print_progress_bar(i - 1, total_pending)
            
            # Processar incentivo
            print(f"\n🔄 Processando {i}/{total_pending}: {incentive.title[:60]}...")
            
            success = ai_processor.process_incentive_complete(db, str(incentive.incentive_id))
            
            if success:
                success_count += 1
                print(f"✅ Sucesso!")
            else:
                failed_count += 1
                print(f"❌ Falhou!")
            
            # Mostrar custos acumulados a cada 5 incentivos
            if i % 5 == 0 or i == total_pending:
                print_cost_summary(ai_processor)
            
        except Exception as e:
            failed_count += 1
            print(f"❌ Erro: {str(e)}")
    
    # Finalizar barra de progresso
    print_progress_bar(total_pending, total_pending)
    
    # Resumo final
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("🎉 PROCESSAMENTO CONCLUÍDO!")
    print("=" * 80)
    print(f"⏱️  Duração: {duration:.1f} segundos")
    print(f"✅ Sucessos: {success_count}")
    print(f"❌ Falhas: {failed_count}")
    print(f"📊 Taxa de sucesso: {(success_count / total_pending * 100):.1f}%")
    
    print_cost_summary(ai_processor)
    
    return success_count > 0


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Teste visual de processamento de IA")
    parser.add_argument("--auto", action="store_true", help="Executar automaticamente sem confirmação")
    args = parser.parse_args()
    
    # Obter sessão da base de dados
    db = SessionLocal()
    
    try:
        # Verificar se há incentivos na base de dados
        total_incentives = db.query(Incentive).count()
        if total_incentives == 0:
            print("❌ Nenhum incentivo encontrado na base de dados!")
            print("   Execute primeiro: make setup-sample")
            return False
        
        # Inicializar AI processor
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY não configurada!")
            return False
        
        ai_processor = AIProcessor(api_key, db)
        
        # Executar processamento
        success = process_incentives_visual(db, ai_processor, args.auto)
        
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

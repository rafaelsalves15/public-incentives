#!/usr/bin/env python3
"""
Teste do AI Processor - Por que não gera CAE codes elegíveis?
"""

import sys
import os
sys.path.append('/app')

from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.db.models import Incentive
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_processor_cae_generation():
    """Testa por que o AI Processor não gera CAE codes elegíveis"""
    
    print("🤖 TESTE DO AI PROCESSOR - GERAÇÃO DE CAE CODES")
    print("=" * 60)
    
    # Inicializar serviços
    db = SessionLocal()
    ai_processor = AIProcessor(api_key=os.getenv('OPENAI_API_KEY'), session=db)
    
    try:
        # Obter primeiro incentivo
        incentive = db.query(Incentive).first()
        if not incentive:
            print("❌ Nenhum incentivo encontrado!")
            return
        
        print(f"📋 INCENTIVO: {incentive.title}")
        print(f"🎯 ID: {incentive.incentive_id}")
        print()
        
        # Verificar se já tem AI description
        current_ai_desc = incentive.ai_description
        print("🔍 AI DESCRIPTION ATUAL:")
        print("-" * 30)
        print(f"CAE Codes: {current_ai_desc.get('eligible_cae_codes', []) if current_ai_desc else 'None'}")
        print(f"Setores: {current_ai_desc.get('eligible_sectors', []) if current_ai_desc else 'None'}")
        print()
        
        # Testar geração de AI description
        print("🤖 GERANDO NOVA AI DESCRIPTION...")
        print("-" * 40)
        
        # Simular o que o AI Processor faz
        prompt = f"""
        Analise este incentivo e gere uma descrição estruturada em JSON:

        TÍTULO: {incentive.title}
        DESCRIÇÃO: {incentive.description or 'N/A'}

        IMPORTANTE: Você DEVE inferir e incluir:
        1. eligible_cae_codes: Lista de códigos CAE específicos que se aplicam
        2. eligible_sectors: Setores elegíveis
        3. target_audience: Público-alvo
        4. summary: Resumo do incentivo

        Retorne APENAS JSON válido com estes campos.
        """
        
        print("📝 PROMPT ENVIADO:")
        print(prompt)
        print()
        
        # Tentar gerar nova descrição
        try:
            # Obter dados CSV do metadata
            metadata = incentive.incentive_metadata
            raw_csv_data = metadata.raw_csv_data if metadata else {}
            
            new_ai_desc = ai_processor.generate_ai_description(incentive, raw_csv_data)
            print("✅ NOVA AI DESCRIPTION GERADA:")
            print("-" * 30)
            print(f"CAE Codes: {new_ai_desc.get('eligible_cae_codes', [])}")
            print(f"Setores: {new_ai_desc.get('eligible_sectors', [])}")
            print(f"Público-alvo: {new_ai_desc.get('target_audience', [])}")
            print(f"Resumo: {new_ai_desc.get('summary', 'N/A')}")
            print()
            
            # Comparar com a atual
            if new_ai_desc.get('eligible_cae_codes'):
                print("🎉 SUCESSO: Nova descrição tem CAE codes!")
                print("💡 SOLUÇÃO: Reprocessar incentivos com AI Processor atualizado")
            else:
                print("❌ PROBLEMA: Nova descrição também não tem CAE codes")
                print("💡 SOLUÇÃO: Verificar prompt do AI Processor")
                
        except Exception as e:
            print(f"❌ ERRO ao gerar nova descrição: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 CONCLUSÕES:")
        print("1. Verificar se o prompt do AI Processor está correto")
        print("2. Verificar se o modelo está sendo instruído a gerar CAE codes")
        print("3. Considerar reprocessar todos os incentivos")
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        print(f"❌ ERRO: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_processor_cae_generation()

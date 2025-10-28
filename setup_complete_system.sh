#!/bin/bash
# Setup Completo do Sistema de Incentivos Públicos
# Este script configura tudo: BD + Import + Matching + Chatbot

set -e  # Exit on error

echo "🚀 SETUP COMPLETO DO SISTEMA"
echo "============================"
echo ""

# 1. Verificar se CSV files existem
echo "📋 Verificando ficheiros CSV..."
if [ ! -f "data/incentives.csv" ]; then
    echo "❌ Ficheiro data/incentives.csv não encontrado!"
    echo "   Por favor, coloque o ficheiro CSV completo em data/incentives.csv"
    exit 1
fi

if [ ! -f "data/companies.csv" ]; then
    echo "❌ Ficheiro data/companies.csv não encontrado!"
    echo "   Por favor, coloque o ficheiro CSV completo em data/companies.csv"
    exit 1
fi

echo "✅ Ficheiros CSV encontrados"
echo ""

# 2. Verificar .env
echo "🔑 Verificando configuração..."
if [ ! -f ".env" ]; then
    echo "📝 Criando .env..."
    cp .env.sample .env || true
    echo ""
    echo "⚠️  IMPORTANTE: Edite o .env e adicione a sua OPENAI_API_KEY!"
    echo "   Exemplo: OPENAI_API_KEY=sk-..."
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OPENAI_API_KEY não configurada no .env!"
    echo "   Edite o .env e adicione: OPENAI_API_KEY=sk-..."
    exit 1
fi

echo "✅ Configuração OK"
echo ""

# 3. Subir containers
echo "🐳 Subindo containers Docker..."
docker compose up -d db
sleep 5
echo "✅ Containers rodando"
echo ""

# 4. Aplicar migrações
echo "🗄️ Aplicando migrações de BD..."
docker compose run --rm api alembic upgrade head
echo "✅ BD criada"
echo ""

# 5. Importar dados
echo "📥 Importando dados dos CSVs..."
docker compose run --rm api python -c "
import sys
sys.path.insert(0, '/app')
from app.services.data_importer import DataImporter

print('Importando incentives...')
importer = DataImporter()
inc_count = importer.import_incentives('/data/incentives.csv')
print(f'✅ Importados {inc_count} incentivos')

print('Importando companies...')
comp_count = importer.import_companies('/data/companies.csv')
print(f'✅ Importadas {comp_count} empresas')

print(f'\n🎉 Total: {inc_count} incentivos + {comp_count} empresas')
importer.close()
"
echo ""

# 6. Processar com AI (opcional - pode ser caro)
echo "🤖 Deseja processar dados com AI? (pode ser caro ~$0.10-0.50)"
echo "   1 - Sim (recomendado para matching de qualidade)"
echo "   2 - Não (pula para matching diretamente)"
read -p "Escolha [1/2]: " process_ai

if [ "$process_ai" == "1" ]; then
    echo "🤖 Processando com AI (isto pode demorar alguns minutos)..."
    docker compose run --rm api python /app/scripts/test_ai_processing_visual.py --auto
    echo "✅ Processamento AI completo"
    echo ""
fi

# 7. Iniciar API completa
echo "🚀 Iniciando API completa..."
docker compose up -d
echo "✅ API rodando em http://localhost:8000"
echo ""

# 8. Gerar matches
echo "🎯 Gerando matches para o chatbot..."
docker compose run --rm api python /app/scripts/generate_matches_for_chatbot.py
echo "✅ Matches gerados"
echo ""

echo ""
echo "========================================"
echo "🎉 SISTEMA COMPLETO PRONTO!"
echo "========================================"
echo ""
echo "📊 URLs Disponíveis:"
echo "   • Interface Chatbot: http://localhost:8000/web/"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "🧪 Como Testar o Chatbot:"
echo "   1. Acesse: http://localhost:8000/web/"
echo "   2. Faça perguntas como:"
echo "      - 'Quantos incentivos temos?'"
echo "      - 'Mostra-me empresas do setor tecnológico'"
echo "      - 'Quais empresas são adequadas para o incentivo [UUID]?'"
echo ""
echo "📝 Notas:"
echo "   • Todos os incentivos têm matches calculados"
echo "   • Chatbot usa dados reais da base de dados"
echo "   • Sistema otimizado para baixos custos"
echo ""




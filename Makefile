.PHONY: up down logs api db test-sample test-sample-incremental setup-sample process-ai show-costs show-status clean-db

up:
	cp .env.sample .env || true
	docker compose up -d --build
	docker compose logs -f api

down:
	docker compose down -v

logs:
	docker compose logs -f

api:
	docker compose exec api bash

db:
	docker compose exec db psql -U app -d incentives

# ========================================
# TESTE COM SAMPLE (CUSTO BAIXO ~$0.005)
# ========================================

test-sample: clean-db setup-sample process-ai show-costs
	@echo ""
	@echo "✅ TESTE COMPLETO FINALIZADO (BD resetada)!"
	@echo "   Ver custos acima ☝️"
	@echo ""

# ========================================
# TESTE INCREMENTAL (SEM RESETAR BD)
# Processa APENAS incentivos pending
# Custo: $0 se todos já processados!
# ========================================

test-sample-incremental: show-status process-ai show-costs
	@echo ""
	@echo "✅ TESTE INCREMENTAL FINALIZADO!"
	@echo "   📊 Apenas incentivos 'pending' foram processados"
	@echo "   💰 Ver custos acima ☝️"
	@echo ""

setup-sample:
	@echo "🔧 Preparando base de dados com sample..."
	@echo ""
	docker compose up -d db
	@sleep 3
	docker compose run --rm api alembic upgrade head
	docker compose run --rm api python -c "import sys; sys.path.insert(0, '/app'); from app.services.data_importer import DataImporter; importer = DataImporter(); print('📥 Importando sample...'); inc = importer.import_incentives('/data/sample_incentives.csv'); comp = importer.import_companies('/data/sample_companies.csv'); print(f'✅ {inc} incentivos + {comp} empresas importados')"
	@echo ""

process-ai:
	@echo "🤖 Processando com AI (mostra custos em tempo real)..."
	@echo ""
	docker compose run --rm -e AUTO_RUN=true api python /app/scripts/test_ai_processing_visual.py --auto
	@echo ""

show-status:
	@echo "📊 STATUS DA BASE DE DADOS:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@docker compose exec -T db psql -U app -d incentives -c "SELECT ai_processing_status as status, COUNT(*) as quantidade FROM incentives_metadata GROUP BY ai_processing_status ORDER BY ai_processing_status;"
	@echo ""
	@docker compose exec -T db psql -U app -d incentives -c "SELECT COUNT(*) as total_incentivos, COUNT(CASE WHEN ai_description IS NOT NULL THEN 1 END) as com_ai_json, COUNT(CASE WHEN ai_description IS NULL THEN 1 END) as sem_ai_json FROM incentives;"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""

show-costs:
	@echo "💰 RESUMO DE CUSTOS:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@docker compose exec -T db psql -U app -d incentives -c "SELECT operation_type, COUNT(*) as calls, SUM(input_tokens) as total_input, SUM(output_tokens) as total_output, SUM(total_cost)::DECIMAL(10,6) as total_cost_usd, SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits FROM ai_cost_tracking GROUP BY operation_type ORDER BY total_cost_usd DESC;"
	@echo ""
	@docker compose exec -T db psql -U app -d incentives -c "SELECT 'TOTAL GERAL' as summary, COUNT(*) as total_calls, SUM(total_cost)::DECIMAL(10,6) as total_cost_usd FROM ai_cost_tracking;"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

clean-db:
	@echo "🧹 Limpando base de dados..."
	docker compose up -d db
	@sleep 2
	docker compose exec -T db psql -U app -d incentives -c "TRUNCATE TABLE incentives_metadata, incentives, companies, ai_cost_tracking RESTART IDENTITY CASCADE;" 2>/dev/null || true
	@echo "✅ Base de dados limpa!"
	@echo ""

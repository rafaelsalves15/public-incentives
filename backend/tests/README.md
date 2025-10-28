# Test Suite para Sistema de Incentivos Públicos

Esta suite de testes abrange todos os componentes do sistema, incluindo APIs, serviços e integrações.

## 📋 Estrutura de Testes

```
tests/
├── __init__.py                    # Inicialização do módulo
├── conftest.py                    # Fixtures e configuração pytest
├── test_api_incentives.py         # Testes dos endpoints de incentivos
├── test_api_companies.py          # Testes dos endpoints de empresas
├── test_api_chatbot.py             # Testes do chatbot
├── test_api_data_management.py     # Testes de gestão de dados
└── test_services.py                # Testes dos serviços
```

## 🧪 Tipos de Testes

### 1. **API Tests** (`@pytest.mark.api`)
- Testes de endpoints REST
- Validação de respostas HTTP
- Validação de paginação e filtros
- Testes de casos de erro

### 2. **Unit Tests** (`@pytest.mark.unit`)
- Testes de lógica de negócio
- Testes de serviços isolados
- Mocks de dependências externas (OpenAI, etc.)

### 3. **Integration Tests** (`@pytest.mark.integration`)
- Testes de fluxos completos
- Interação entre componentes
- Testes end-to-end

### 4. **Slow Tests** (`@pytest.mark.slow`)
- Testes que requerem processamento pesado
- Testes com dados reais
- Podem ser executados separadamente

## 🚀 Como Executar os Testes

### Requisitos

Instalar dependências de teste:
```bash
make install-test-deps
```

### Executar Todos os Testes

```bash
make test
```

### Executar por Categoria

```bash
# Apenas testes de API
make test-api

# Apenas testes unitários
make test-unit

# Apenas testes de integração
make test-integration

# Testes rápidos (sem testes lentos)
make test-fast
```

### Com Coverage

```bash
make test-cov
```

### Para CI/CD

```bash
make test-ci
```

## 📊 Cobertura de Testes

### Endpoints de API Testados

#### Incentivos (`/incentives/`)
- ✅ `GET /incentives/` - Listar incentivos
- ✅ `GET /incentives/{id}` - Obter incentivo específico
- ✅ `GET /incentives/{id}/matches` - Obter matches
- ✅ `GET /incentives/{id}/summary` - Obter resumo
- ✅ Filtros e paginação
- ✅ Casos de erro (404, 422)

#### Empresas (`/companies/`)
- ✅ `GET /companies/` - Listar empresas
- ✅ `GET /companies/{id}` - Obter empresa específica
- ✅ `GET /companies/{id}/incentives` - Obter incentivos da empresa
- ✅ `GET /companies/search/by-activity` - Buscar por atividade
- ✅ Filtros e paginação
- ✅ Casos de erro

#### Chatbot (`/chatbot/`)
- ✅ `POST /chatbot/message` - Enviar mensagem
- ✅ `GET /chatbot/history/{user_id}` - Obter histórico
- ✅ `POST /chatbot/search` - Busca rápida
- ✅ `DELETE /chatbot/history/{user_id}` - Limpar histórico
- ✅ `GET /chatbot/stats` - Estatísticas
- ✅ `GET /chatbot/help` - Ajuda
- ✅ `GET /chatbot/health` - Health check

#### Gestão de Dados (`/data/`)
- ✅ `GET /data/files/status` - Status de ficheiros
- ✅ `GET /data/processing-status` - Status de processamento
- ✅ `GET /data/costs/stats` - Estatísticas de custos
- ✅ `GET /data/costs/recent` - Custos recentes

### Serviços Testados

#### CostTracker
- ✅ Inicialização
- ✅ Cálculo de custos (input/output)
- ✅ Tracking de chamadas API
- ✅ Cache hits ($0)
- ✅ Estatísticas agregadas

#### DataImporter (Mocked)
- ✅ Importação de ficheiros CSV
- ✅ Validação de dados

#### Matching Services (Mocked)
- ✅ Inicialização de serviços
- ✅ Cálculo de similaridade
- ✅ Vector search

## 🔧 Fixtures Disponíveis

### Database
- `db_session`: Sessão de base de dados de teste
- `engine`: Engine de base de dados

### API Client
- `client`: TestClient FastAPI configurado

### Sample Data
- `sample_incentive_data`: Dados de exemplo para incentivos
- `sample_company_data`: Dados de exemplo para empresas
- `create_incentive`: Cria incentivo na BD
- `create_company`: Cria empresa na BD

### Mocks
- `mock_openai_response`: Resposta mockada do OpenAI
- `mock_ai_processor`: Mock do AIProcessor
- `mock_embedding_service`: Mock do EmbeddingService

## 📝 Marcadores de Teste

Use marcadores para organizar e executar testes específicos:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.api
def test_api_endpoint():
    pass

@pytest.mark.integration
def test_integration_flow():
    pass

@pytest.mark.slow
def test_heavy_processing():
    pass
```

## 🐛 Executar Testes Específicos

### Por ficheiro:
```bash
docker compose exec api pytest tests/test_api_incentives.py -v
```

### Por função:
```bash
docker compose exec api pytest tests/test_api_incentives.py::TestIncentivesAPI::test_list_incentives -v
```

### Com marcadores:
```bash
# Apenas testes de API sem testes lentos
docker compose exec api pytest tests/ -v -m "api and not slow"

# Apenas testes unitários
docker compose exec api pytest tests/ -v -m "unit"
```

## 📊 Relatórios de Coverage

Após executar `make test-cov`, ver relatórios em:
- Terminal: Coverage report inline
- HTML: `htmlcov/index.html` (gerado no container)
- XML: Para integração com CI/CD

## 🔍 Debugging

### Ver output detalhado:
```bash
docker compose exec api pytest tests/ -v -s
```

### Parar no primeiro erro:
```bash
docker compose exec api pytest tests/ -v -x
```

### Ver output de prints:
```bash
docker compose exec api pytest tests/ -v --capture=no
```

## 💡 Boas Práticas

1. **Testes Independentes**: Cada teste deve poder rodar isoladamente
2. **Fixtures para Setup**: Use fixtures para criar dados de teste
3. **Mocks para Dependências Externas**: Sempre mockar APIs externas (OpenAI, etc.)
4. **Cleanup Automático**: Fixtures cuidam da limpeza
5. **Nomes Descritivos**: Nomes de testes devem descrever o comportamento testado


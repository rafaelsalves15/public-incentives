# 🇵🇹 Sistema de Incentivos Públicos - Portugal

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

> **Sistema inteligente de matching entre incentivos públicos portugueses e empresas**, usando IA híbrida (determinística + LLM) para processar, estruturar e recomendar os incentivos mais adequados para cada empresa.

---

## 📋 Índice

- [🎯 Sobre o Projeto](#-sobre-o-projeto)
- [🏗️ Arquitetura e Tecnologias](#️-arquitetura-e-tecnologias)
- [⚡ Quick Start](#-quick-start)
- [🚀 FASE 0: Bootstrap](#-fase-0-bootstrap)
- [🗄️ FASE 1: Base de Dados](#️-fase-1-base-de-dados)
  - [Arquitetura de 3 Tabelas](#arquitetura-de-3-tabelas)
  - [Pipeline de Processamento](#pipeline-de-processamento)
  - [Sistema Híbrido (Determinístico + AI)](#sistema-híbrido-determinístico--ai)
  - [Otimizações de Custo](#otimizações-de-custo)
  - [Cost Tracking](#cost-tracking)
  - [Scripts de Teste](#scripts-de-teste)
- [💰 Custos e Performance](#-custos-e-performance)
- [📚 Estrutura do Projeto](#-estrutura-do-projeto)
- [🤝 Contribuir](#-contribuir)

---

## 🎯 Sobre o Projeto

Este sistema resolve o problema de **matching entre incentivos públicos portugueses e empresas** através de um pipeline inteligente que:

1. **Importa e estrutura** dados heterogéneos de incentivos 
2. **Processa com modelo híbrido (determinístico e IA)** para completar campos em falta e estruturar informação
3. **Faz matching inteligente** entre incentivos e empresas baseado em múltiplos critérios
4. **Fornece chatbot** para responder questões sobre incentivos



---

## 🏗️ Arquitetura e Tecnologias

### **Stack Tecnológico**

| Camada | Tecnologia | Propósito |
|--------|------------|-----------|
| **Backend** | FastAPI + Python 3.11 | API REST assíncrona e eficiente |
| **Base de Dados** | PostgreSQL 15 | Armazenamento relacional com suporte JSON |
| **ORM** | SQLAlchemy 2.0 | Gestão de modelos e queries |
| **Migrações** | Alembic | Versionamento de schema |
| **IA/LLM** | OpenAI GPT-4o-mini | Processamento inteligente (custo-eficiente) |
| **Containerização** | Docker + Docker Compose | Ambiente reproduzível |
| **Data Processing** | Pandas | Manipulação de CSVs e transformações |

### **Arquitetura de Alto Nível**

```
┌─────────────┐
│   CSV Data  │ (incentivos.csv, companies.csv)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│           DATA IMPORT PIPELINE                       │
│  • Parsing CSV (21 campos heterogéneos)             │
│  • Validação e limpeza                              │
│  • Separação: 10 campos principais + metadata      │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│         HYBRID PROCESSING SYSTEM                     │
│  1️⃣ Deterministic Extraction (all_data JSON)        │
│     → Extrai datas, orçamentos, estrutura          │
│  2️⃣ AI Processing (quando deterministic falha)     │
│     → GPT-4o-mini preenche campos em falta         │
│  3️⃣ Cost Optimization                              │
│     → Prompts adaptados, cache, token limits       │
└──────┬──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────┬──────────────────────┬───────────────────┐
│   INCENTIVES (10)    │  METADATA (unique)   │   COMPANIES (7)   │
│  • title             │  • raw_csv_data      │  • company_name   │
│  • description       │  • all_data          │  • cae_code       │
│  • ai_description    │  • ai_proc_status    │  • sector         │
│  • dates (3)         │  • fields_by_ai      │  • size           │
│  • total_budget      │  • processing_error  │  • region         │
│  • source_link       │  ...                 │  ...              │
│  • document_urls     │                      │                   │
└──────────────────────┴──────────────────────┴───────────────────┘
```

---

## ⚡ Quick Start

### **Pré-requisitos**
- Docker & Docker Compose
- OpenAI API Key

### **🚀 Testar o Projeto Completo**

   ```bash
# 1. Configurar API Key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 2. Testar TUDO (dataset completo: 538 incentivos + 21 empresas)
make test  # TODO: Implementar na Fase 2
```

**Custo estimado**: ~$0.15-0.20 (dataset completo)

---

### **🧪 Testar com Sample (Recomendado para Desenvolvimento)**

Para testes rápidos e económicos, usa o **sample de 13 incentivos**:

   ```bash
# Teste completo (reseta BD)
make test-sample
   ```



**Ou teste incremental** (mantém BD, só processa pending):
   ```bash
make test-sample-incremental
```



---

## 🚀 FASE 0: Bootstrap

### **Setup do Ambiente**

O projeto usa **Docker Compose** para garantir ambiente reproduzível e isolado.

#### **1. Estrutura de Containers**

```yaml
services:
  db:        # PostgreSQL 15
  api:       # FastAPI + Python 3.11
```

#### **2. Inicialização**

   ```bash
# Subir containers
docker compose up -d

# Aplicar migrações de BD
docker compose run --rm api alembic upgrade head

# Verificar status
docker compose ps
```

#### **3. Volumes e Persistência**

```
./data/              → CSVs (montado em /data no container)
./backend/           → Código da API
./infra/docker/      → Dockerfiles
```

#### **4. Variáveis de Ambiente**

Ficheiro `.env`:
```env
OPENAI_API_KEY=sk-...        # Chave OpenAI (obrigatório)
DATABASE_URL=postgresql://app:password@db:5432/incentives
```

#### **5. Comandos Úteis**

   ```bash
make up      # Subir containers
make down    # Parar e remover containers
make db      # Aceder à BD PostgreSQL
make api     # Shell dentro do container API
make logs    # Ver logs em tempo real
```

---

## 🗄️ FASE 1: Base de Dados

### **Objetivo da Fase**

Criar uma **base de dados estruturada e completa** de incentivos públicos portugueses, processando CSVs heterogéneos e usando IA (quando necessário) para:
- ✅ Completar campos em falta (datas, orçamentos)
- ✅ Estruturar descrições em JSON padronizado


---

### **Arquitetura de 3 Tabelas**

Optámos por uma arquitetura **normalizada em 3 tabelas** para maximizar eficiência e manutenibilidade.

#### **📋 Tabela 1: `incentives` (10 campos) - como pedido no enunciado**

**Propósito**: Dados principais e frequentemente acedidos.

```sql
CREATE TABLE incentives (
    incentive_id      UUID PRIMARY KEY,
    title             VARCHAR(500) NOT NULL,
    description       TEXT,
    ai_description    JSON,              -- ⭐ Estruturado pela AI
    document_urls     JSON,
    publication_date  TIMESTAMP,
    start_date        TIMESTAMP,
    end_date          TIMESTAMP,
    total_budget      NUMERIC,
    source_link       VARCHAR(500),
    cae_primary_code  VARCHAR(50)        -- ⭐ Inferido pela AI
);
```


#### **📋 Tabela 2: `incentives_metadata` (dados únicos + AI)**

**Propósito**: Guardar dados originais do CSV + metadados de processamento AI.

**Por que esta tabela?** 
Para seguir a indicação do enunciado onde a tabela `incentives` tem **10 campos**, mas o CSV tem **21 campos**, esta tabela serve para preservar todos os dados originais que podem ser relevantes para **matching futuro** (Fase 2), como:
- `all_data` (estrutura completa, calendário, dotações)
- `eligibility_criteria` (critérios de elegibilidade)
- `incentive_program` (programa a que pertence)
- `status` (estado do incentivo)

```sql
CREATE TABLE incentives_metadata (
    metadata_id             UUID PRIMARY KEY,
    incentive_id            UUID UNIQUE REFERENCES incentives(incentive_id),
    raw_csv_data            JSON NOT NULL,      -- 13 campos: 9 únicos + ai_description texto + 3 datas raw
    ai_processing_status    VARCHAR(50),        -- pending/processing/completed/failed
    ai_processing_date      TIMESTAMP,
    fields_completed_by_ai  JSON,              -- ['ai_description', 'dates', ...]
    ai_processing_error     TEXT,
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
);
```

**Detalhe dos 13 campos em `raw_csv_data`**:
- **9 campos únicos** (não existem em `incentives`): `all_data`, `form_info`, `eligibility_criteria`, `regions`, `sectors`, `cae_codes`, `objective`, `scraped_url`, `incentive_id_original`
- **1 campo para AI**: `ai_description` original do CSV em **texto puro** (usado pela AI para converter para JSON estruturado ou como contexto para gerar do zero)
- **3 campos de data/orçamento em formato raw** (antes de parsing): `submission_deadline`, `announcement_date`, `total_budget`

**Vantagens**:
- ✅ **Respeita restrição** do enunciado (10 campos em `incentives`)
- ✅ **Sem duplicação**: `raw_csv_data` guarda campos únicos (não repetidos em `incentives`)
- ✅ **Rastreabilidade**: Sabemos exatamente quais campos foram completados por IA
- ✅ **Controlo de processamento**: Flag `ai_processing_status` evita reprocessamento
- ✅ **Dados para matching**: Campos como `eligibility_criteria` e `all_data` serão usados na Fase 2
- ✅ **Debugging**: `ai_processing_error` guarda erros para análise

#### **📋 Tabela 3: `companies` (7 campos derivados)**

**Propósito**: Empresas do CSV original (4 campos disponíveis).

```sql
CREATE TABLE companies (
    company_id               UUID PRIMARY KEY,
    company_name             VARCHAR(500) NOT NULL,
    cae_primary_label        VARCHAR(500),      -- Ex: "Software development"
    trade_description_native TEXT,              -- Descrição em PT
    website                  VARCHAR(500),
    cae_primary_code         VARCHAR(50),       -- ⭐ Inferido pela AI
    company_size             VARCHAR(50),       -- ⭐ Inferido pela AI
    region                   VARCHAR(100),      -- ⭐ Inferido pela AI
    is_active                BOOLEAN DEFAULT TRUE
);
```

**Campos do CSV**: `company_name`, `cae_primary_label`, `trade_description_native`, `website`

**Campos inferidos pela AI**:
- `cae_primary_code`: Código CAE numérico inferido da descrição textual
- `company_size`: Tamanho da empresa (micro/small/medium/large) inferido dos dados disponíveis
- `region`: Região geográfica inferida do nome e dados da empresa

---

### **Pipeline de Processamento**

#### **Fluxo Completo**

```
CSV → Import → Deterministic → AI (fallback) → Structured DB
```

#### **1️⃣ Fase 1: Import (sem custos)**

O `DataImporter` processa 2 CSVs:

**CSV de Incentivos** → dividido em 2 tabelas

**CSV de Companies** → importado diretamente para tabela `companies`

Após o import, o sistema analisa cada incentivo e marca como `ai_processing_status = 'pending'` se estiver em falta:
- `ai_description` em JSON estruturado
- Datas (`publication_date`, `start_date`, `end_date`)
- Orçamento (`total_budget`)

**Custo desta fase: $0** (só parsing e base de dados)

#### **2️⃣ Fase 2: AI Processing (com custos otimizados)**

O `AIProcessor` processa apenas os incentivos marcados como `pending`, usando uma **abordagem híbrida** (determinístico primeiro, AI só quando necessário):

**Para cada incentivo pendente:**

1. **Extração de Datas** (híbrido):
   - **Determinístico**: Procura em `all_data->calendario` por `dataPublicacao`, `dataInicio`, `dataFim`
   - **AI Fallback**: Se faltar alguma data, usa LLM para extrair do texto (prompt pequeno, ~300 tokens)
  
2. **Extração de Orçamento** (híbrido):
   - **Determinístico**: Procura em `all_data->estrutura->dotacoes->valor`
   - **AI Fallback**: Se não encontrar, usa LLM (prompt pequeno, ~200 tokens)

3. **Geração de `ai_description`** (sempre AI, mas otimizado):
   - **Conversão** (se campo `ai_description` no CSV tinha texto): Prompt curto pedindo apenas conversão de texto para JSON (800 tokens max)
   - **Geração do zero** (se `ai_description` no CSV estava vazio): Prompt completo analisando `all_data` + `eligibility_criteria` (1500 tokens max)
   - **Economia**: Conversões custam ~43% menos que gerações

#### **3️⃣ Fase 3: Enriquecimento de Dados (inferência automática)**

Para maximizar a qualidade do matching, o sistema infere automaticamente campos em falta:

**Para Incentivos:**
- **CAE Code**: Inferido da descrição do incentivo usando LLM para identificar setores específicos

**Para Empresas:**
- **CAE Code**: Conversão de descrições textuais (`cae_primary_label`) para códigos numéricos usando LLM
- **Região**: Inferência da localização baseada no nome da empresa e dados disponíveis
- **Tamanho**: Classificação automática do porte da empresa (micro/small/medium/large)

**Estratégias de Otimização:**
- **Intelligent Fallback**: Mapeamento manual para casos comuns, LLM apenas quando necessário
- **Intelligent Caching**: Reutilização de respostas para inputs similares
- **Batch Processing**: Processamento em lotes para reduzir custos

---

### **Sistema Híbrido: Quando usa Determinístico vs AI**

| Campo | Método Determinístico | Quando usa AI | 
|-------|----------------------|---------------|
| **Datas** | Extrai de `all_data->calendario` (chaves fixas) | Só se faltar após extração | 
| **Orçamento** | Extrai de `all_data->estrutura->dotacoes` | Só se faltar após extração | 
| **ai_description** | ❌ Não aplicável (precisa LLM para estruturar) | **Sempre**, mas com 2 prompts diferentes |
| **CAE Codes** | ❌ Não aplicável (precisa LLM para inferir) | **Sempre** para incentivos e empresas |
| **Região** | ❌ Não aplicável (precisa LLM para inferir) | **Sempre** para empresas |
| **Tamanho** | ❌ Não aplicável (precisa LLM para inferir) | **Sempre** para empresas | 

**Vantagens do Híbrido:**
- ✅ **Grátis quando possível**
- ✅ **Robusto**: Cobre casos onde dados estruturados estão incompletos
- ✅ **Previsível**: Determinístico dá sempre o mesmo resultado

---

### **6 Otimizações de Custo Implementadas**

#### **1️⃣ Flag de Processamento (`ai_processing_status`)**

A **otimização mais fundamental**: Cada incentivo tem um status na tabela `incentives_metadata`:
- `pending`: Precisa ser processado
- `completed`: Já foi processado com sucesso → **nunca reprocessa** (**custo = $0**)
- `failed`: Falhou (pode ser reprocessado manualmente)

**Proteção**: Scripts de processamento só buscam incentivos com status `pending`. Se executares `make test-sample-incremental` duas vezes seguidas, a 2ª execução custa **$0** porque todos já estão `completed`.

**Impacto**: Sem esta flag, reprocessar 538 incentivos por engano custaria ~$0.14 cada vez. Com a flag, **custo = $0** em re-execuções.

#### **2️⃣ Prompts Adaptados**

O sistema **detecta automaticamente** se o CSV já tinha texto em `ai_description`:
- **Se tinha texto**: Usa prompt curto só para converter texto→JSON (800 tokens máx)
- **Se estava vazio**: Usa prompt completo para gerar do zero (1500 tokens máx)

**Economia**: Conversões custam ~43% menos que gerações

#### **3️⃣ Limites de Tokens Calibrados**

Cada operação tem um limite `max_tokens` ajustado ao mínimo necessário (com margem de segurança):
- `ai_description` (conversão): 800 tokens
- `ai_description` (geração): 1500 tokens
- Extração de datas: 300 tokens (só 3 datas em JSON)
- Extração de orçamento: 200 tokens (só 1 número)

#### **4️⃣ Memory Cache**

Antes de chamar a API OpenAI, o sistema calcula um **hash MD5 do prompt completo**:
- **Cache HIT**: Se o prompt já foi usado antes nesta sessão, retorna o resultado guardado em memória (**custo = $0**)
- **Cache MISS**: Se é novo, chama a API e guarda o resultado no cache

**Características**:
- **100% preciso**: Só reutiliza se o prompt for **exatamente** igual (hash MD5)
- **Não expira**: Cache dura toda a sessão de processamento
- **Transparente**: Aparece no cost tracker como "Cache HIT" ($0)

**Quando ajuda**: Datasets com incentivos duplicados/similares



#### **5️⃣ Enriquecimento Inteligente de Dados**

O sistema infere automaticamente campos em falta usando estratégias otimizadas:

**Intelligent Fallback**: Mapeamento manual para casos comuns (ex: "Software development" → CAE 62010)
**Intelligent Caching**: Reutilização de respostas para inputs similares
**Batch Processing**: Processamento em lotes para reduzir custos de API

**Impacto**: Campos como CAE codes, região e tamanho são essenciais para matching de qualidade, mas não estão nos CSVs originais. O sistema os infere automaticamente com custos mínimos.

---

### **Cost Tracking em Tempo Real**

O sistema implementa **tracking completo de custos** para garantir transparência e controlo do orçamento.



#### **📊 O que é tracked**

**Nível de detalhe**: Cada chamada à API OpenAI é gravada na base de dados com:
- Tipo de operação (`ai_description_convert`, `extract_dates`, `extract_budget`)
- Modelo usado 
- Tokens consumidos (input, output, total)
- Custo calculado ($0.15/M input, $0.60/M output para gpt-4o-mini)
- Se foi cache HIT ($0) ou MISS (custo real)
- Sucesso/erro

**Visualização em tempo real**: Durante o processamento, o terminal mostra:
- **Por incentivo**: Custo de cada operação (descrição, datas, orçamento)
- **Acumulado**: Total gasto até agora
- **Resumo final**: Total de chamadas, cache hits/misses, custo médio por incentivo

---

### **Scripts de Teste**

Implementámos **2 comandos principais** para testar o sistema com custos mínimos (sample de 13 incentivos e 20 empresas):

#### **🧪 `make test-sample` (Teste Completo)**

**O que faz**:
1. Limpa a base de dados (TRUNCATE em todas as tabelas)
2. Aplica migrações (Alembic upgrade head)
3. Importa sample de teste (13 incentivos + 20 empresas)
4. Processa com AI (conversões, gerações, extração híbrida)
5. Mostra custos detalhados

**Quando usar**: Primeira vez, após corrigir bugs, ou quando queres começar do zero.

**Custo**: ~$0.003-0.005 (processa todos os 13 incentivos)

#### **🧪 `make test-sample-incremental` (Teste Incremental)**

**O que faz**:
1. Mostra status atual (pending/completed/failed)
2. Processa **APENAS** incentivos marcados como `pending`
3. Mostra custos


**Quando usar**: Reprocessar incentivos que falharam, ou verificar se algo novo precisa processamento.

**Custo**: $0 se tudo já está processado, ou só o custo dos incentivos `pending`

#### **📋 Comandos Auxiliares**

- `make show-status`: Ver quantos pending/completed/failed
- `make show-costs`: Ver custos totais guardados na BD
- `make clean-db`: Limpar BD (TRUNCATE)
- `make setup-sample`: Só importar (sem processar AI)
- `make process-ai`: Só processar incentivos pending

---


---

## 🎯 FASE 2: Sistema de Matching Inteligente

### **Objetivo da Fase**

Implementar um sistema híbrido que identifica automaticamente as 5 empresas mais adequadas para cada incentivo, combinando análise determinística com inteligência artificial para maximizar precisão e minimizar custos.

---

### **Arquitetura do Sistema**

O sistema implementa uma **abordagem unificada** que combina scoring determinístico com refinamento por LLM:

```
TODAS AS EMPRESAS
│
├─ UNIFIED SCORER (Determinístico)
│   ├─ Analisa CAE codes, setores, região, tamanho
│   ├─ Atribui scores positivos/negativos
│   ├─ Ordena por relevância
│   └─ Seleciona Top 15 candidatas
│
└─ LLM REFINEMENT (Inteligência Artificial)
    ├─ Recebe Top 15 candidatas + critérios do incentivo
    ├─ Seleciona as 5 melhores com justificações
    ├─ Valida factualmente as razões
    └─ Retorna ranking final otimizado
```



---

### **Unified Scorer: Análise Determinística**

#### **Sistema de Pontuação Unificado**

O sistema substitui filtros binários por um **sistema de pontuação contínuo** que avalia múltiplos critérios:

**Critérios Positivos:**
- **CAE Code Match**: Pontuação alta para códigos CAE exatos ou relacionados
- **Setor Match**: Alinhamento entre atividade da empresa e setores elegíveis
- **Região Match**: Compatibilidade geográfica com regiões elegíveis
- **Tamanho Match**: Adequação do tamanho da empresa aos requisitos

**Critérios Negativos:**
- **Penalties**: Redução de pontos para incompatibilidades óbvias
- **Validação**: Verificação automática de dados inconsistentes

#### **Vantagens da Abordagem Unificada**

- **Flexibilidade**: Não elimina empresas prematuramente
- **Granularidade**: Scores permitem ranking preciso
- **Eficiência**: Processamento instantâneo sem custos de API
- **Robustez**: Funciona mesmo com dados incompletos





---

### **LLM Refinement: Seleção Inteligente**

#### **Processo de Refinamento**

O LLM recebe as 15 melhores candidatas do Unified Scorer e:

1. **Avalia Contextualmente**: Considera nuances que algoritmos determinísticos não captam
2. **Seleciona Top 5**: Escolhe as empresas mais adequadas com justificações


#### **Otimizações de Custo**

**Batch Processing:**
- Uma única chamada API por incentivo (vs múltiplas chamadas individuais)
- Processamento de 15 empresas simultaneamente
- Redução drástica de custos comparado com abordagens tradicionais

**Prompt Engineering:**
- Informação essencial apenas (título, setores, CAE codes, requisitos)
- Exclusão de campos redundantes ou de baixo impacto
- Estrutura otimizada para respostas JSON consistentes

**Configuração Otimizada:**
- `max_tokens=2000`: Suficiente para respostas completas sem truncamento
- Validação pós-LLM para garantir qualidade

#### **Validação e Correção Automática**

O sistema implementa **validação pós-LLM** que:
- Verifica factualmente as alegações do LLM (ex: elegibilidade de CAE codes)
- Corrige scores quando detecta informações incorretas
- Ajusta razões para refletir a realidade dos dados
- Garante que rankings finais são baseados em factos


---


### **Escalabilidade e Performance**

#### **Índices de Base de Dados**

O sistema utiliza índices estratégicos para garantir performance com datasets grandes:

```sql
CREATE INDEX idx_companies_cae ON companies(cae_primary_label);
CREATE INDEX idx_companies_name ON companies(company_name);
CREATE INDEX idx_matches_incentive ON incentive_company_matches(incentive_id);
```

#### **Arquitetura de Caching**

- **Memory Cache**: Reutilização de respostas LLM idênticas
- **Intelligent Caching**: Cache baseado em similaridade para inputs parecidos
- **Fallback Mechanisms**: Redução de chamadas LLM desnecessárias

---

### **Output e Resultados**

#### **Estrutura de Resposta**

Para cada incentivo, o sistema retorna:

```json
{
  "incentive_id": "uuid",
  "incentive_title": "Título do Incentivo",
  "top_5_matches": [
    {
      "company_name": "Nome da Empresa",
      "match_score": 0.85,
      "unified_score": 150,
      "reasons": ["Razão 1", "Razão 2"],
      "ranking_position": 1
    }
  ]
}
```

#### **Métricas de Qualidade**

- **Scores Positivos**: Empresas com boa correspondência
- **Scores Negativos**: Empresas com correspondência fraca
- **Validação Automática**: Verificação de consistência dos resultados
- **Ranking Ordenado**: Empresas ordenadas por relevância decrescente

---
### **Scripts de Teste**

#### **🧪 Teste Rápido (1 incentivo)**

```bash
# Teste com 1 incentivo sample
docker compose run --rm api python -c "
from app.db.database import SessionLocal
from app.services.ai_processor import AIProcessor
from app.services.company_matcher import CompanyMatcher
from app.db.models import Incentive
import os

session = SessionLocal()
ai_processor = AIProcessor(os.getenv('OPENAI_API_KEY'), session)
matcher = CompanyMatcher(ai_processor)

# Pegar primeiro incentivo
incentive = session.query(Incentive).first()
matches = matcher.find_top_matches(session, str(incentive.incentive_id))

print(f'Found {len(matches)} matches')
for i, m in enumerate(matches, 1):
    print(f'{i}. {m[\"company\"].company_name}: {m[\"match_score\"]:.2f}')
"
```

#### **🧪 Teste Completo (todos incentivos)**

```bash
# TODO: Criar script test_matching_visual.py
make test-matching
```

---

### **Comandos Make (TODO)**

```bash
make test-matching              # Testar matching com sample
make test-matching-full         # Processar 538 incentivos
make export-matches-csv         # Exportar resultados para CSV
make compare-optimized-legacy   # Comparar custos otimizado vs legado
```

---

#
---

## 📚 Estrutura do Projeto

```
public-incentives/
├── backend/
│   ├── alembic/                 # Migrações de BD
│   │   └── versions/            # Histórico de migrações
│   ├── app/
│   │   ├── api/                 # Endpoints FastAPI
│   │   │   └── data_management.py  # POST /import, /process-ai, etc
│   │   ├── db/
│   │   │   ├── models.py        # SQLAlchemy models (3 tabelas)
│   │   │   └── database.py      # Conexão e sessão
│   │   └── services/
│   │       ├── data_importer.py          # CSV → BD
│   │       ├── ai_processor.py           # Hybrid AI processing
│   │       ├── cost_tracker.py           # Cost tracking
│   │       ├── eligibility_filter.py     # FASE 2: Hard constraints
│   │       ├── deterministic_scorer.py   # FASE 2: Scoring gratuito
│   │       └── company_matcher.py        # FASE 2: Matching otimizado
│   └── scripts/
│       ├── test_ai_processing_visual.py  # Teste com visual tracking
│       ├── create_sample_csvs.py         # Gera samples de teste
│       └── validate_import.py            # Valida importação
├── data/
│   ├── incentives.csv           # Dataset completo (538 linhas)
│   ├── companies.csv            # Dataset completo (21 linhas)
│   ├── sample_incentives.csv    # Sample de teste (13 linhas)
│   └── sample_companies.csv     # Sample de teste (20 linhas)
├── infra/
│   └── docker/
│       ├── api.Dockerfile       # Imagem da API
│       └── init-db.sh           # Inicialização BD
├── docker-compose.yml           # Orquestração de containers
├── Makefile                     # Comandos úteis
└── README.md                    # Este ficheiro
```

---


---

## 🤖 **FASE 3: Chatbot de Incentivos**

### **Sistema Completo Implementado**

O chatbot permite aos utilizadores interagir naturalmente com o sistema através de uma interface web moderna:

**Funcionalidades:**
- ✅ **Consultas sobre incentivos**: "Quais incentivos existem para empresas de software?"
- ✅ **Exploração de empresas**: "Mostra-me empresas do setor tecnológico"
- ✅ **Análise de correspondências**: "Que empresas são adequadas para o incentivo X?"
- ✅ **Estatísticas e análises**: "Quantos incentivos temos na base de dados?"
- ✅ **Interface web integrada**: Funciona dentro do container Docker

**Arquitetura:**
- **RAG (Retrieval-Augmented Generation)**: Usa dados estruturados como contexto
- **Query Router inteligente**: Analisa intenções e roteia para handlers específicos
- **Sistema de contexto**: Mantém memória da conversa
- **Cache inteligente**: Reduz custos LLM reutilizando respostas similares

### **Como Usar o Chatbot**

```bash
# Iniciar sistema completo
make start-chatbot

# Acessar interface web
# http://localhost:8000/web/

# Testar chatbot
make test-chatbot

# Teste completo do sistema
make test-complete
```

**Exemplos de Perguntas:**
- "Quais incentivos existem para empresas de software?"
- "Mostra-me empresas do setor tecnológico"
- "Que empresas são adequadas para o incentivo X?"
- "Quantos incentivos temos na base de dados?"
- "Qual o orçamento total disponível?"

---

### **Roadmap**

- [x] **FASE 0**: Bootstrap (Docker, BD, Migrações) ✅
- [x] **FASE 1**: Base de Dados com AI Processing ✅
- [x] **FASE 2**: Sistema de Matching Otimizado ✅
  - [x] Eligibility Pre-Filtering
  - [x] Deterministic Scoring  
  - [x] LLM Refinement
  - [x] CSV Export ✅
- [x] **FASE 3**: Chatbot para responder questões ✅
  - [x] ChatbotService com RAG
  - [x] Query Router inteligente
  - [x] Sistema de contexto
  - [x] Interface web integrada
- [x] **FASE 4**: Frontend Web Interface ✅
  - [x] Interface de chat moderna
  - [x] Integração com API
  - [x] Funciona dentro do container

---


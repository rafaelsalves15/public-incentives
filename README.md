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
- [🎯 FASE 2: Sistema de Matching](#-fase-2-sistema-de-matching-inteligente)
- [🤖 FASE 3: Chatbot de Incentivos](#-fase-3-chatbot-de-incentivos)
- [🧪 Testes](#-testes)
  
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
| **Base de Dados Vetorial** | ChromaDB | Busca semântica com embeddings |
| **ORM** | SQLAlchemy 2.0 | Gestão de modelos e queries |
| **Migrações** | Alembic | Versionamento de schema |
| **IA/LLM** | OpenAI GPT-4o-mini | Processamento inteligente (custo-eficiente) |
| **Embeddings** | text-embedding-3-small | Vetorização semântica (OpenAI) |
| **Containerização** | Docker + Docker Compose | Ambiente reproduzível |
| **Data Processing** | Pandas | Manipulação de CSVs e transformações |
| **Interface Web** | HTML/CSS/JavaScript | Chatbot web integrado |


---

## ⚡ Quick Start

### **Pré-requisitos**
- Docker & Docker Compose
- OpenAI API Key

### **🚀 Setup Completo para Avaliador (Recomendado)**

Para um setup completo do sistema com dados realistas:

```bash
# 1. Configurar API Key
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# 2. Setup padrão: 20 incentivos + 1000 empresas (~25-35 min)
make setup-evaluator

# 3. Acessar interface web
# http://localhost:8000/web/
```

**O que faz:**
- Importa e processa 20 incentivos com inferência de dados por AI
- Cria 1000 empresas simuladas com dados completos
- Gera matches para todos os incentivos
- Inicia chatbot com interface web

**Alternativas:**
```bash
# Setup rápido: 10 incentivos + 100 empresas (~3-5 min)
make setup-evaluator-quick

# Setup customizado
make setup-evaluator-custom NUM_INC=30 NUM_COMP=500
```

---



**Comandos úteis:**
```bash
# Ver status do sistema
make show-status

# Ver custos de AI
make show-costs

# Ver logs
make logs
```

---

### **📋 Comandos Principais do Sistema**

O sistema inclui comandos abrangentes para todas as fases de desenvolvimento e teste:


```bash
# Após setup, acessar interfaces:
# - Chatbot Web: http://localhost:8000/web/
# - API Docs: http://localhost:8000/docs
# - API Chatbot: http://localhost:8000/chatbot/
```

#### **🔧 Comandos de Gestão**

```bash
# Iniciar/Parar sistema
make up              # Iniciar containers
make down            # Parar containers
make logs            # Ver logs em tempo real

# Acesso a serviços
make db              # Aceder à base de dados PostgreSQL
make api             # Shell dentro do container API
```



#### **📊 Comandos Auxiliares**

```bash
# Importação de dados
make import-full                  # Dataset completo
make import-sample                # Sample pequeno

# Gestão de dados
make clean-db                     # Limpar BD
make show-status                  # Ver status
make show-costs                   # Ver custos
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

## 🎯 FASE 2: Sistema de Matching Inteligente

### **Objetivo da Fase**

Implementar um sistema híbrido que identifica automaticamente as 5 empresas mais adequadas para cada incentivo, combinando busca semântica, análise determinística e inteligência artificial para maximizar precisão e minimizar custos.

---

### **Arquitetura do Sistema: Pipeline de 3 Fases**

O sistema implementa um **pipeline híbrido de 3 fases** que combina embeddings semânticos, scoring determinístico e refinamento por LLM:

```
TODAS AS EMPRESAS
│
├─ FASE 1: VECTOR SEARCH (Embeddings Semânticos) 🧠
│   ├─ Gera embeddings para incentivo e empresas
│   ├─ Busca por similaridade coseno
│   ├─ Seleciona Top 50 candidatas semânticas
│   └─ Custo: ~$0.00002 por embedding (text-embedding-3-small)
│
├─ FASE 2: UNIFIED SCORER (Determinístico) 📊
│   ├─ Analisa CAE codes, setores, região, tamanho
│   ├─ Atribui scores positivos/negativos
│   ├─ Ordena por relevância
│   └─ Seleciona Top 15 candidatas
│
└─ FASE 3: LLM REFINEMENT (Inteligência Artificial) 🤖
    ├─ Recebe Top 15 candidatas + critérios do incentivo
    ├─ Análise contextual das nuances
    ├─ Seleciona as 5 melhores com justificações detalhadas
    ├─ Valida factualmente as razões
    └─ Retorna ranking final otimizado

RESULTADO: Top 5 empresas mais adequadas ordenadas por match_score
```

**Vantagens do pipeline de 3 fases:**
- ✅ **Busca semântica**: Descobre matches não óbvios baseados em significado
- ✅ **Scoring determinístico**: Mantém precisão com critérios específicos
- ✅ **Refinamento LLM**: Análise contextual para qualidade superior
- ✅ **Custo otimizado**: Redução de ~70% em custos LLM vs abordagem tradicional

---

### **Fase 1: Vector Search com Embeddings Semânticos**



O sistema usa **OpenAI text-embedding-3-small**

#### **Busca por Similaridade**

**Similaridade Coseno:**
- Calcula distância entre embeddings de incentivo e empresa
- Score de 0.0 (sem similaridade) a 1.0 (idêntico)
- Retorna Top 50 empresas mais similares

**Threshold mínimo:** 0.2 (Similaridade mínima aceitável) 

#### **Vantagens dos Embeddings**

✅ **Descoberta não óbvia**: Encontra matches que filtros exatos perdem
✅ **Compreensão semântica**: Entende sinónimos e variações linguísticas
✅ **Redução de custos**: Filtra de milhares para 50 candidatas antes do LLM
✅ **Cache inteligente**: Reutiliza embeddings calculados anteriormente
✅ **Escalabilidade**: Funciona com milhões de empresas (otimizado com ChromaDB)

#### **Otimizações Implementadas**

- **Memory Cache**: Evita recalcular embeddings idênticos
- **Similaridade Coseno**: Cálculo eficiente usando NumPy
- **Batch Processing**: Processa múltiplas empresas de uma vez
- **Vector Database**: Armazena embeddings em ChromaDB para busca rápida

---

### **Fase 2: Unified Scorer (Análise Determinística)**

#### **Sistema de Pontuação Unificado**

O sistema substitui filtros binários por um **sistema de pontuação contínuo** que avalia múltiplos critérios:

**Critérios Positivos:**
- **CAE Code Match**: Pontuação alta para códigos CAE exatos ou relacionados
- **Setor Match**: Alinhamento entre atividade da empresa e setores elegíveis
- **Região Match**: Compatibilidade geográfica com regiões elegíveis
- **Tamanho Match**: Adequação do tamanho da empresa aos requisitos


---

### **Fase 3: LLM Refinement - Escolha Final**

#### **Como o LLM Escolhe as 5 Melhores**

O LLM analisa as 15 candidatas e retorna apenas as 5 melhores (com llm_score). Depois o sistema calcula o total_score combinando llm_score + unified_score + semantic_similarity e reordena por esse total_score (podendo alterar a ordem final).

Quando LLM recebe as 15 candidatas:

1. **Avalia Contextualmente**: Analisa não apenas dados estruturados, mas também contexto e nuances
2. **Aplica Critérios Inteligentes**: 
   - Verifica correspondência de CAE codes elegíveis
   - Avalia alinhamento de setor e atividade
   - Considera requisitos específicos (tamanho, região, tipo de financiamento)
3. **Seleciona Top 5**: Escolhe as 5 empresas mais adequadas entre as 15 candidatas
4. **Gera Justificações**: Explica porquê cada empresa é adequada

#### **Sistema de Análise Batch**

**Uma única chamada LLM** processa todas as 15 candidatas simultaneamente:

```python
# O LLM recebe todas as 15 empresas e critérios do incentivo
# Em UMA só chamada API, analisa todas e retorna top 5

Input:
- Incentivo: "Apoio à digitalização de PMEs"
- Candidatas: 15 empresas (já filtradas por Vector Search + Unified Scoring)
- Tarefa: Escolher top 5 com maior fit

Output:
- Top 5 empresas
- Razões detalhadas para cada escolha
```

**Por que 15 candidatas?**
- Dá escolha real ao LLM (não apenas validação)
- Permite comparação direta entre empresas
- Mantém contexto suficiente para análise inteligente
- Otimiza custos (1 chamada vs 15 chamadas individuais)

#### **Otimizações de Custo**

**Batch Processing:**
- Uma única chamada API por incentivo (vs múltiplas chamadas individuais)
- Processamento de 15 empresas simultaneamente
- Redução de custos vs análise individual

**Prompt Engineering:**
- Apenas informação essencial (título, setores, CAE codes, requisitos)
- Exclusão de campos redundantes
- Estrutura otimizada para respostas JSON consistentes

**Configuração Otimizada:**
- `max_tokens=2000`: Suficiente para respostas completas sem truncamento
- Análise contextual sem custos desnecessários

#### **Validação e Correção Automática**

O sistema implementa **validação pós-LLM** que:
- Verifica factualmente as alegações do LLM (ex: elegibilidade de CAE codes)
- Corrige scores quando detecta informações incorretas
- Ajusta razões para refletir a realidade dos dados
- Garante que rankings finais são baseados em factos



#### **Métricas de Qualidade**

- **Scores Positivos**: Empresas com boa correspondência
- **Validação Automática**: Verificação de consistência dos resultados
- **Ranking Ordenado**: Empresas ordenadas por relevância decrescente

---

### **Output e Resultados - Depois de todas as fases concluídas**

#### **Estrutura de Resposta do Hybrid Matching**

Para cada incentivo, o sistema retorna uma **lista** com as top 5 empresas:

```json
[
  {
    "company_name": "Empresa A",
    "company_size": "medium",
    "region": "Lisboa",
    "cae_primary_code": ["62010", "62020"],
    
    // Scores combinados
    "semantic_similarity": 0.85,    // Similaridade semântica (0.0-1.0)
    "unified_score": 150,            // Score determinístico (pontos)
    "llm_score": 0.92,              // Score do LLM (0.0-1.0)
    "match_score": 0.89,            // Total score combinado
    
    // Razões detalhadas
    "semantic_reasons": ["Similaridade semântica: 0.850"],
    "unified_reasons": ["CAE code match", "Setor compatível"],
    "llm_reasons": ["Empresa desenvolve software para PMEs"],
    
    // Posição
    "ranking_position": 1
  }
  // ... até 5 empresas
]
```

#### **Match Score**

O `match_score` final combina 3 scores com pesos específicos:

```python
total_score = (
    semantic_similarity × 0.3 +        # 30% - Busca semântica
    normalized(unified_score) × 0.4 +  # 40% - Score determinístico  
    llm_score × 0.3                    # 30% - Análise LLM
)

# Onde normalized = min(unified_score / 200.0, 1.0)


```

*

## 🤖 **FASE 3: Chatbot de Incentivos**

### **Sistema Completo Implementado**

O chatbot permite aos utilizadores interagir naturalmente com o sistema através de uma interface web moderna, fornecendo respostas inteligentes e contextualizadas sobre incentivos, empresas e correspondências.

### **Funcionalidades do Chatbot**

**Tipos de Consultas Suportadas:**
- ✅ **Incentivos**: Listar, pesquisar e detalhar incentivos disponíveis
- ✅ **Empresas**: Explorar empresas por setor, região ou tipo
- ✅ **Correspondências**: Obter top 5 matches para cada incentivo
- ✅ **Estatísticas**: Análise agregada (orçamentos, contagens, médias)
- ✅ **Consultas Contextuais**: Respostas inteligentes mantendo contexto da conversa

**Características Principais:**
- Interface web moderna integrada no container
- Respostas em português natural e fluido
- Mantém memória da conversa (contexto de sessão)
- Geração inteligente de respostas usando RAG (Retrieval-Augmented Generation)
- Cache automático para reduzir custos

---

### **Arquitetura do Chatbot**

O chatbot implementa uma **arquitetura de 3 camadas** para otimizar custos e qualidade:

```
┌─────────────────────────────────────────┐
│  1. Query Router Inteligente            │
│     • Analisa intenção da mensagem      │
│     • Extrai entidades (UUIDs, setores) │
│     • Roteia para handler apropriado    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  2. Database Queries Especializados     │
│     • Consultas diretas à BD            │
│     • Filtros otimizados (SQLAlchemy)   │
│     • Retorna dados estruturados        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  3. LLM Generation (Opcional)           │
│     • Apenas quando necessário          │
│     • Contexto otimizado (<500 tokens) │
│     • Respostas naturais em português    │
└─────────────────────────────────────────┘
```

**Otimizações:**
- **Zero chamadas LLM** para queries simples (listas, contagens)
- **Cache inteligente** para prompts similares
- **Batch processing** para múltiplas entidades

---

### **Query Router: Análise Inteligente**

O sistema implementa um **Query Router** que analisa automaticamente a intenção da mensagem:

**Tipos de Intent Suportados:**
- `incentive_query`: Consultas sobre incentivos
- `company_query`: Consultas sobre empresas
- `match_query`: Análise de correspondências
- `analytics_query`: Estatísticas e agregações
- `specific_query`: Detalhes por ID específico

**Extração de Entidades:**
- **UUIDs**: IDs de incentivos ou empresas
- **Setores**: Setor/atividade mencionado
- **Regiões**: Localização geográfica
- **Números**: Orçamentos, contagens, datas

---

### **Como Usar o Chatbot**

#### **Setup Inicial**

```bash
# Setup padrão (recomendado para demonstrar): 20 incentivos + 1000 empresas
make setup-evaluator

# Setup rápido (10+100 empresas, ~3-5 min)
make setup-evaluator-quick

# Setup customizado
make setup-evaluator-custom NUM_INC=30 NUM_COMP=500
```

#### **Acesso ao Sistema**

Depois do setup, acede às seguintes interfaces:

**Interface Web (Chatbot)**:
```
http://localhost:8000/web/
```

**API REST (Swagger)**:
```
http://localhost:8000/docs
```

**Chatbot API**:
```
http://localhost:8000/chatbot/
```

#### **Comandos de Teste**

```bash
# Testar chatbot
make test-chatbot

# Teste completo do sistema
make test-complete

# Ver logs
make logs

# Ver custos de AI
make show-costs
```

---

### **Exemplos de Perguntas**

**Consultas sobre Incentivos:**
- "Quais incentivos existem para empresas de software?"
- "Mostra-me incentivos para o setor turístico"
- "Quantos incentivos temos na base de dados?"
- "Qual o orçamento total disponível?"

**Consultas sobre Empresas:**
- "Mostra-me empresas do setor tecnológico"
- "Quais empresas existem na região de Lisboa?"
- "Empresas de agricultura"

**Análise de Correspondências:**
- "Que empresas são adequadas para o incentivo de infraestrutura portuária?"
- "Mostra-me os matches do incentivo X"
- "Empresas adequadas para o incentivo de cuidados de saúde"

**Estatísticas:**
- "Quantos incentivos e empresas temos?"
- "Qual o orçamento total?"
- "Média de orçamento por incentivo?"

---

# 🧪 Suite de Testes - Resumo Final


### **Estrutura:**
```
backend/tests/
├── __init__.py
├── conftest.py              # Fixtures e configuração
├── test_api_basic.py        # 12 testes básicos
└── README.md               # Documentação técnica
```


#### API Basic (6 testes)
- ✅ `test_api_health` - Health check
- ✅ `test_api_root` - Root endpoint
- ✅ `test_chatbot_health` - Chatbot health
- ✅ `test_get_chatbot_help` - Help endpoint
- ✅ `test_check_data_files` - Data files status
- ✅ `test_get_import_status` - Import status

#### Input Validation (6 testes)
- ✅ `test_invalid_pagination_incentives` - Paginação inválida
- ✅ `test_invalid_pagination_companies` - Paginação inválida
- ✅ `test_missing_required_parameter` - Parâmetro obrigatório
- ✅ `test_list_companies_search_no_results` - Busca sem resultados
- ✅ `test_list_incentives_returns_valid_structure` - Estrutura valida
- ✅ `test_list_companies_returns_valid_structure` - Estrutura valida

## 🚀 **Como Executar**

### **Todos os Testes:**
```bash
make test
```

### **Apenas Testes Básicos:**
```bash
docker compose exec api bash -c "cd /app && pytest tests -v"
```

### **Com Coverage:**
```bash
make test-cov
```


## 🎯 **O Que É Testado**

- ✅ Health checks (API e chatbot)
- ✅ Root endpoints
- ✅ Help e documentação
- ✅ Status de ficheiros
- ✅ Validação de input (pagination, parâmetros)
- ✅ Estrutura de respostas da API
- ✅ Buscas sem resultados
- ✅ Validação de erros 422

## 🔒 **Segurança**

- ✅ **Totalmente isolado** - SQLite in-memory
- ✅ **Sem custos** - Nenhuma chamada OpenAI real
- ✅ **Rápido** - 0.21s para todos os testes
- ✅ **Não afeta sistema** - BD de produção separada

## 📚 **Documentação**

- `backend/tests/README.md` - Documentação técnica



---

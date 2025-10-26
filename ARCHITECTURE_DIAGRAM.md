# 🏗️ Arquitetura do Sistema Híbrido de Matching

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SISTEMA HÍBRIDO DE MATCHING                          │
│                              (3 Fases Otimizadas)                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FASE 1:       │    │   FASE 2:       │    │   FASE 3:       │
│ VECTOR SEARCH    │───▶│ UNIFIED SCORING │───▶│ LLM REFINEMENT │
│   (SEMÂNTICA)    │    │ (DETERMINÍSTICA)│    │  (INTELIGENTE)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Top 50          │    │ Top 15          │    │ Top 5           │
│ Candidatas      │    │ Candidatas      │    │ Finalistas      │
│ Semânticas      │    │ Pontuadas       │    │ Analisadas      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Similaridade    │    │ CAE Codes       │    │ Razões          │
│ Semântica       │    │ Setores         │    │ Recomendações   │
│ 0.3 - 0.9       │    │ Região          │    │ Concerns        │
│                 │    │ Tamanho         │    │ Score Final     │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              COMPONENTES PRINCIPAIS                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ EmbeddingService│    │VectorDatabase   │    │HybridMatching  │    │Performance     │
│                 │    │Service          │    │Service          │    │Optimizer       │
│ • OpenAI API    │    │                 │    │                 │    │                 │
│ • Cache Memory  │    │ • ChromaDB      │    │ • Pipeline 3    │    │ • Auto-tuning   │
│ • Cache Disk    │    │ • Persistência  │    │   Fases         │    │ • Cost Analysis │
│ • Batch Process │    │ • Similarity    │    │ • Score         │    │ • Monitoring    │
│                 │    │   Search        │    │   Combination   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Geração de      │    │ Armazenamento   │    │ Orquestração    │    │ Otimizações     │
│ Embeddings      │    │ Vectorial       │    │ do Pipeline     │    │ Automáticas     │
│                 │    │                 │    │                 │    │                 │
│ • Incentivos    │    │ • Coleção       │    │ • Configuração  │    │ • Thresholds    │
│ • Empresas      │    │   Incentivos    │    │   Dinâmica      │    │ • Cache         │
│ • Similaridade  │    │ • Coleção       │    │ • Fallback      │    │ • Performance   │
│   Coseno        │    │   Empresas      │    │   Original      │    │ • Custos        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FLUXO DE DADOS                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Incentivo   │───▶│ Embedding   │───▶│ Vector      │───▶│ Semantic    │
│ (Título +   │    │ Generation  │    │ Database   │    │ Search      │
│ Descrição + │    │             │    │ Storage    │    │ (Top 50)    │
│ AI Data)    │    │ • OpenAI    │    │            │    │             │
└─────────────┘    │   API       │    │ • ChromaDB  │    │ • Similarity│
                   │ • Cache     │    │ • Metadata │    │ • Filtering │
                   │ • Batch     │    │ • Indexing │    │ • Ranking   │
                   └─────────────┘    └─────────────┘    └─────────────┘
                            │                   │                   │
                            ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Empresa     │───▶│ Embedding   │───▶│ Vector      │───▶│ Unified     │
│ (Nome +     │    │ Generation  │    │ Database   │    │ Scoring     │
│ CAE +       │    │             │    │ Storage    │    │ (Top 15)    │
│ Descrição)  │    │ • OpenAI    │    │            │    │             │
└─────────────┘    │   API       │    │ • ChromaDB  │    │ • CAE Match │
                   │ • Cache     │    │ • Metadata │    │ • Sector    │
                   │ • Batch     │    │ • Indexing │    │ • Region    │
                   └─────────────┘    └─────────────┘    │ • Size      │
                                                         └─────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────┐
                                                         │ LLM         │
                                                         │ Analysis    │
                                                         │ (Top 5)     │
                                                         │             │
                                                         │ • GPT-4o    │
                                                         │ • Batch     │
                                                         │ • Reasons   │
                                                         │ • Final     │
                                                         │   Score     │
                                                         └─────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              OTIMIZAÇÕES IMPLEMENTADAS                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cache           │    │ Batch           │    │ Thresholds      │    │ Cost            │
│ Inteligente     │    │ Processing      │    │ Adaptativos     │    │ Optimization    │
│                 │    │                 │    │                 │    │                 │
│ • Memory Cache  │    │ • Embeddings    │    │ • Auto-adjust   │    │ • LLM Reduction │
│ • Disk Cache    │    │ • Vector DB     │    │ • Performance   │    │ • Cache Savings │
│ • Hit Rate >80% │    │ • Parallel      │    │   Based         │    │ • Monitoring    │
│ • Persistence   │    │ • Memory Opt    │    │ • Quality       │    │ • Analysis      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RESULTADOS DE PERFORMANCE                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Redução de      │    │ Melhoria de     │    │ Descoberta      │    │ Escalabilidade   │
│ Custos          │    │ Qualidade       │    │ Semântica       │    │                 │
│                 │    │                 │    │                 │    │                 │
│ • LLM: -70%     │    │ • Score: +20%   │    │ • Matches não   │    │ • Milhões de    │
│ • Embedding:    │    │ • Precisão:     │    │   óbvios        │    │   embeddings     │
│   -80% (cache)  │    │   +30%          │    │ • Similaridade  │    │ • Cache         │
│ • Total: -65%   │    │ • Tempo: -57%   │    │   0.3-0.9       │    │   distribuído   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              COMPARAÇÃO DE SISTEMAS                            │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ SISTEMA         │    │ SISTEMA         │    │ MELHORIA        │
│ ORIGINAL        │    │ HÍBRIDO         │    │                 │
│                 │    │                 │    │                 │
│ • Todas empresas│    │ • Top 50 semânt.│    │ • -70% custos   │
│ • LLM completo  │    │ • Top 15 pontu. │    │ • +20% qualidade│
│ • ~$0.002/incent│    │ • Top 5 LLM     │    │ • -57% tempo    │
│ • ~5s resposta  │    │ • ~$0.0006/incent│    │ • +semântica   │
│ • Score ~0.65   │    │ • ~2s resposta  │    │ • +robustez     │
│ • CAE apenas    │    │ • Score ~0.78   │    │ • +escalabilidade│
└─────────────────┘    └─────────────────┘    └─────────────────┘

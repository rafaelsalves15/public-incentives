# Guia do Avaliador

Este documento explica como configurar e testar o sistema completo de incentivos públicos com chatbot.

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Setup Rápido](#setup-rápido)
3. [Acessar o Sistema](#acessar-o-sistema)
4. [Funcionalidades do Chatbot](#funcionalidades-do-chatbot)
5. [Exemplos de Perguntas](#exemplos-de-perguntas)

## 🎯 Visão Geral

O sistema inclui:

- **Inferência automática de dados por AI** para incentivos e empresas
- **Matching híbrido** entre incentivos e empresas
- **Chatbot inteligente** para consultar informações
- **Interface web** para interação com o sistema

## 🚀 Setup Rápido

### Opção 1: Setup com 20 incentivos + 1000 empresas (Recomendado)

```bash
make setup-evaluator
```

Esta é a configuração padrão ideal para demonstração.

### Opção 2: Setup rápido com 10 incentivos + 100 empresas

```bash
make setup-evaluator-quick
```

Para testes mais rápidos.

### Opção 3: Setup customizado

```bash
make setup-evaluator-custom NUM_INC=20 NUM_COMP=150
```

Substitua os números conforme necessário.

## ⏱️ Tempo de Setup

- **Setup rápido** (10+100): ~3-5 minutos
- **Setup padrão** (20+1000): ~25-35 minutos
- **Setup grande** (100+500): ~30-45 minutos

*O tempo varia conforme a chamadas à API da OpenAI para inferência de dados.*

## 🌐 Acessar o Sistema

Depois do setup, o sistema estará disponível em:

### 1. Interface Web (Chatbot)
```
http://localhost:8000/web/
```
Interface web interativa com o chatbot.

### 2. API REST
```
http://localhost:8000/docs
```
Documentação interativa da API (Swagger).

### 3. Endpoints do Chatbot
```
http://localhost:8000/chatbot/
```
API específica do chatbot.

## 💬 Funcionalidades do Chatbot

O chatbot permite:

### 1. Obter Informação sobre Incentivos
- Listar todos os incentivos disponíveis
- Detalhes específicos de um incentivo
- Pesquisar incentivos por setor, região, orçamento, etc.

### 2. Consultar Dados sobre Empresas
- Listar empresas disponíveis
- Informações detalhadas de uma empresa
- Empresas por setor, região, tamanho, etc.

### 3. Explorar Correspondências
- Ver matches entre incentivos e empresas
- Empresas adequadas para um incentivo específico
- Incentivos adequados para uma empresa específica

### 4. Estatísticas e Análises
- Total de incentivos na base de dados
- Total de empresas na base de dados
- Orçamento total disponível
- Número de matches gerados

## 📝 Exemplos de Perguntas

### Sobre Incentivos

```
"Quais incentiv os existem?"
```
Lista todos os incentivos disponíveis.

```
"Mostra-me os incentiv os de tecnologia"
```
Pesquisa incentiv os relacionados com tecnologia.

```
"Qual é o incentivo com maior orçamento?"
```
Encontra o incentivo com maior total_budget.

```
"Quais incentiv os estão disponíveis para empresas pequenas?"
```
Pesquisa incentiv os adequados para empresas pequenas.

### Sobre Empresas

```
"Mostra-me as empresas de software"
```
Lista empresas no setor de software.

```
"Quantas empresas temos na base de dados?"
```
Conta total de empresas.

```
"Empresas na região de Lisboa"
```
Filtra empresas por região.

### Sobre Correspondências (Matches)

```
"Que empresas são adequadas para o incentivo X?"
```
Mostra matches para um incentivo específico.

```
"Que incentiv os são adequados para uma empresa de tecnologia?"
```
Encontra incentiv os relevantes para empresas de TI.

```
"Mostra-me os top matches"
```
Lista os melhores matches gerados.

### Estatísticas

```
"Quantos incentiv os temos?"
```
Conta total de incentiv os.

```
"Qual é o orçamento total disponível?"
```
Soma todos os orçamentos de incentiv os.

```
"Dá-me um resumo do sistema"
```
Estatísticas gerais do sistema.

## 🔍 Estrutura dos Dados

### Dados Inferidos por AI

#### Para Incentivos:
- **ai_description**: Descrição estruturada em JSON gerada por AI
- **setor**: Setor industrial alvo
- **tipo_empresa**: Tipo de empresa elegível
- **região**: Regiões elegíveis

#### Para Empresas:
- **cae_primary_code**: Códigos CAE múltiplos inferidos
- **region**: Região NUTS II de Portugal
- **company_size**: Tamanho da empresa (micro/small/medium/large)

## 🛠️ Comandos Adicionais Úteis

### Ver logs do sistema
```bash
make logs
```

### Parar o sistema
```bash
make down
```

### Reiniciar do zero
```bash
make down
make setup-evaluator
```

### Ver custos do AI
```bash
make show-costs
```

### Acessar base de dados
```bash
make db
```

## 📊 Custos de API

O sistema usa a OpenAI API para:
- Inferência de dados de empresas
- Geração de AI descriptions para incentiv os

**Custo estimado por setup:**
- Setup rápido (10+100): ~$0.05
- Setup padrão (20+1000): ~$0.40
- Setup grande (100+500): ~$0.50

## ❓ Problemas Comuns

### "OpenAI API key not found"
Certifique-se que o ficheiro `.env` existe com `OPENAI_API_KEY` configurada.

### "Database connection failed"
Certifique-se que os serviços estão a correr:
```bash
make up
```

### "Chatbot não responde"
Verifique se o setup completou com sucesso:
```bash
make logs
```

## 📞 Suporte

Para problemas ou questões:
1. Verifique os logs: `make logs`
2. Consulte a documentação da API: http://localhost:8000/docs
3. Verifique o estado do sistema: http://localhost:8000/health

## ✅ Checklist de Teste

Antes da avaliação, teste:

- [ ] Setup completou sem erros
- [ ] Interface web acessível em http://localhost:8000/web/
- [ ] API docs acessível em http://localhost:8000/docs
- [ ] Chatbot responde a perguntas básicas
- [ ] Lista de incentiv os funciona
- [ ] Lista de empresas funciona
- [ ] Matches são gerados e visíveis

## 🎉 Boa Avaliação!

O sistema está pronto para uso. Boa sorte com a avaliação!

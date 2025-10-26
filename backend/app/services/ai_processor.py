import openai
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.db.models import Incentive, IncentiveMetadata, Company
from app.services.cost_tracker import CostTracker
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIProcessor:
    def __init__(self, api_key: str, session: Session):
        self.client = openai.OpenAI(api_key=api_key)
        self.session = session
        self.cost_tracker = CostTracker(session)
        self._prompt_cache = {}  # Memory cache for identical prompts
        self._cache_hits = 0
        self._cache_misses = 0
    
    def generate_ai_description(self, incentive: Incentive, raw_csv_data: Dict) -> Optional[Dict[str, Any]]:
        """
        Generate structured AI description from text description and raw data.
        This is called when ai_description is missing or needs to be converted to JSON.
        
        Uses memory cache to avoid duplicate API calls for identical prompts.
        
        OPTIMIZATION: Uses different prompts based on whether ai_description already exists:
        - If ai_description exists (text) → Short conversion prompt (~50% fewer tokens)
        - If ai_description is empty → Full generation prompt
        
        This reduces costs for incentives with existing text descriptions.
        """
        csv_data = raw_csv_data or {}
        
        # Get the original ai_description if it exists (might be text)
        original_ai_desc = csv_data.get('ai_description', '').strip()
        
        # OPTIMIZATION 1: Detect if we're converting existing text or generating from scratch
        has_existing_description = bool(original_ai_desc and len(original_ai_desc) > 20)
        
        if has_existing_description:
            # OPTIMIZED PROMPT: Convert existing text to JSON (much shorter, cheaper)
            prompt = f"""
Converte esta descrição de incentivo para JSON estruturado.

TEXTO ORIGINAL:
{original_ai_desc}

CONTEXTO ADICIONAL:
Título: {incentive.title}
Programa: {csv_data.get('incentive_program', '')}

Estrutura o texto em JSON:
{{
  "summary": "Resumo de 2-3 frases",
  "objective": "Objetivo principal",
  "target_audience": ["PMEs", "Startups", etc],
  "eligible_sectors": ["Tecnologia", etc],
  "eligible_cae_codes": ["Códigos CAE elegíveis - ex: 62010", "62020", "63110"],
  "eligible_regions": ["Norte", "Centro", etc],
  "company_sizes": ["micro", "small", "medium", "large"],
  "key_requirements": ["Requisito 1", etc],
  "funding_details": {{
    "max_funding_percentage": 75,
    "max_amount": 500000,
    "min_amount": 10000,
    "funding_type": "grant/loan/tax_benefit/mixed"
  }},
  "supported_activities": ["Atividade 1", etc],
  "application_process": "Breve descrição",
  "important_notes": ["Nota 1", etc]
}}

INSTRUÇÕES:
- Usa [] ou null se faltar informação
- OBRIGATÓRIO: INFERE códigos CAE específicos baseados nos setores elegíveis
- Exemplos: "Educação" → ["85520", "85530"], "Tecnologia" → ["62010", "62020"], "Construção" → ["41200", "41100"], "Mobilidade/Transporte" → ["49410", "49420", "49390"]
- Se não conseguir inferir códigos específicos, usa códigos relacionados ao setor
- OBRIGATÓRIO: INFERE tamanhos de empresa compatíveis (ex: ["small", "medium", "large"])
- Responde SÓ com JSON:
"""
            max_tokens = 800  # Shorter response expected
            operation_tag = "convert_text"
            
        else:
            # FULL PROMPT: Generate from scratch (more expensive)
            eligibility = csv_data.get('eligibility_criteria', {})
            all_data_content = csv_data.get('all_data', {})
            
            prompt = f"""
Analisa este incentivo público português e gera uma descrição estruturada em JSON.

INFORMAÇÃO DISPONÍVEL:
Título: {incentive.title}
Descrição: {incentive.description}
Programa: {csv_data.get('incentive_program', 'Desconhecido')}
Estado: {csv_data.get('status', 'Desconhecido')}
Orçamento Total: €{incentive.total_budget if incentive.total_budget else 'Não especificado'}
Critérios de Elegibilidade: {json.dumps(eligibility, ensure_ascii=False)}
Dados Completos: {json.dumps(all_data_content, ensure_ascii=False)}

TAREFA:
Extrai e estrutura a informação em JSON com o seguinte formato:

{{
  "summary": "Resumo executivo de 2-3 frases explicando o incentivo",
  "objective": "Objetivo principal do incentivo",
  "target_audience": ["Tipo de beneficiários - ex: PMEs", "Startups", "Grandes empresas"],
  "eligible_sectors": ["Setores específicos compatíveis com CAE - ex: Computer programming", "Software development", "Information technology"],
  "eligible_cae_codes": ["Códigos CAE elegíveis - ex: 62010", "62020", "63110"],
  "eligible_regions": ["Regiões geográficas elegíveis - ex: Norte", "Centro", "Todo o país"],
  "company_sizes": ["micro", "small", "medium", "large"],
  "key_requirements": ["Requisito 1", "Requisito 2"],
  "funding_details": {{
    "max_funding_percentage": 75,
    "max_amount": 500000,
    "min_amount": 10000,
    "funding_type": "grant/loan/tax_benefit/mixed"
  }},
  "supported_activities": ["Atividade 1", "Atividade 2"],
  "application_process": "Descrição breve do processo de candidatura",
  "important_notes": ["Nota importante 1", "Nota importante 2"]
}}

INSTRUÇÕES:
- Se alguma informação não estiver disponível, usa [] para arrays ou null para valores
- Sê específico e preciso
- Mantém termos técnicos em português
- INFERE setores elegíveis mesmo com descrições vagas (ex: "educação" → ["Educação", "Formação"])
- Se não há setores explícitos, infere do título/objetivo
- OBRIGATÓRIO: INFERE códigos CAE específicos baseados nos setores elegíveis
- Exemplos: "Educação" → ["85520", "85530"], "Tecnologia" → ["62010", "62020"], "Construção" → ["41200", "41100"]
- Se não conseguir inferir códigos específicos, usa códigos relacionados ao setor
- Responde APENAS com o JSON, sem texto adicional

JSON:
"""
            max_tokens = 1500  # Full response
            operation_tag = "generate_full"
        
        # Memory cache: Check if we've seen this exact prompt before
        cache_key = hashlib.md5(prompt.encode('utf-8')).hexdigest()
        
        if cache_key in self._prompt_cache:
            self._cache_hits += 1
            logger.info(f"💾 Cache HIT for '{incentive.title[:50]}...' (hits: {self._cache_hits}, misses: {self._cache_misses})")
            
            # Track cache hit (custo = 0)
            self.cost_tracker.track_api_call(
                operation_type=f"ai_description_{operation_tag}",
                model_name="gpt-4o-mini",
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=str(incentive.incentive_id),
                cache_hit=True,
                success=True
            )
            
            return self._prompt_cache[cache_key]
        
        # Cache miss - need to call OpenAI API
        self._cache_misses += 1
        logger.info(f"🔍 Cache MISS for '{incentive.title[:50]}...' - calling OpenAI API (hits: {self._cache_hits}, misses: {self._cache_misses})")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Track API call cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type=f"ai_description_{operation_tag}",
                model_name="gpt-4o-mini",
                usage_data=usage_data,
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=True
            )
            
            # Store in cache for future use
            self._prompt_cache[cache_key] = result
            logger.info(f"✅ Cached result for '{incentive.title[:50]}...' (cache size: {len(self._prompt_cache)})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating AI description for incentive {incentive.incentive_id}: {e}")
            
            # Track failed API call
            self.cost_tracker.track_api_call(
                operation_type=f"ai_description_{operation_tag}",
                model_name="gpt-4o-mini",
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            
            return None
    
    def extract_missing_dates(self, incentive: Incentive, raw_csv_data: Dict) -> Dict[str, Optional[datetime]]:
        """
        Extract missing dates from description or all_data using AI.
        Returns dict with publication_date, start_date, end_date.
        """
        csv_data = raw_csv_data or {}
        all_data = csv_data.get('all_data', {})
        
        # First try to extract from all_data (deterministic)
        dates = {}
        
        # Try calendario field in all_data
        if 'calendario' in all_data:
            calendario = all_data['calendario']
            if 'dataPublicacao' in calendario:
                dates['publication_date'] = self._parse_datetime(calendario['dataPublicacao'])
            if 'dataInicio' in calendario:
                dates['start_date'] = self._parse_datetime(calendario['dataInicio'])
            if 'dataFim' in calendario:
                dates['end_date'] = self._parse_datetime(calendario['dataFim'])
        
        # If still missing dates, use AI
        missing_dates = []
        if 'publication_date' not in dates and not incentive.publication_date:
            missing_dates.append('publication_date')
        if 'start_date' not in dates and not incentive.start_date:
            missing_dates.append('start_date')
        if 'end_date' not in dates and not incentive.end_date:
            missing_dates.append('end_date')
        
        if missing_dates:
            ai_dates = self._extract_dates_with_ai(incentive, missing_dates)
            dates.update(ai_dates)
        
        return dates
    
    def _extract_dates_with_ai(self, incentive: Incentive, missing_fields: List[str]) -> Dict[str, Optional[datetime]]:
        """Use AI to extract dates from text"""
        csv_data = incentive.incentive_metadata.raw_csv_data if incentive.incentive_metadata else {}
        
        prompt = f"""
Analisa este incentivo português e extrai as datas em falta.

INFORMAÇÃO:
Título: {incentive.title}
Descrição: {incentive.description}
Dados: {json.dumps(csv_data.get('all_data', {}), ensure_ascii=False)}

DATAS EM FALTA: {', '.join(missing_fields)}

Responde em JSON com formato ISO (YYYY-MM-DD):
{{
  "publication_date": "2025-01-15",
  "start_date": "2025-02-01",
  "end_date": "2025-12-31"
}}

Se não conseguires determinar uma data, usa null.
Responde APENAS com JSON, sem texto adicional.

JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            dates_json = json.loads(content)
            
            # Track API call cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type="extract_dates",
                model_name="gpt-4o-mini",
                usage_data=usage_data,
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=True
            )
            
            # Convert to datetime objects
            result = {}
            for field in missing_fields:
                if field in dates_json and dates_json[field]:
                    result[field] = self._parse_datetime(dates_json[field])
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting dates with AI for incentive {incentive.incentive_id}: {e}")
            
            # Track failed API call
            self.cost_tracker.track_api_call(
                operation_type="extract_dates",
                model_name="gpt-4o-mini",
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            
            return {}
    
    def extract_missing_budget(self, incentive: Incentive, raw_csv_data: Dict) -> Optional[float]:
        """
        Extract missing budget from description or all_data.
        """
        csv_data = raw_csv_data or {}
        all_data = csv_data.get('all_data', {})
        
        # First try to extract from all_data (deterministic)
        # Check for dotacao in estrutura
        if 'estrutura' in all_data and isinstance(all_data['estrutura'], list):
            total_dotacao = 0
            for item in all_data['estrutura']:
                if 'dotacao' in item:
                    try:
                        total_dotacao += float(item['dotacao'])
                    except (ValueError, TypeError):
                        pass
            if total_dotacao > 0:
                return total_dotacao
        
        # If not found, try AI extraction
        return self._extract_budget_with_ai(incentive)
    
    def _extract_budget_with_ai(self, incentive: Incentive) -> Optional[float]:
        """Use AI to extract budget from text"""
        csv_data = incentive.incentive_metadata.raw_csv_data if incentive.incentive_metadata else {}
        
        prompt = f"""
Analisa este incentivo português e extrai o orçamento total disponível.

INFORMAÇÃO:
Título: {incentive.title}
Descrição: {incentive.description}
Dados: {json.dumps(csv_data.get('all_data', {}), ensure_ascii=False)}

Extrai o ORÇAMENTO TOTAL (dotação total disponível) em euros.

Responde em JSON:
{{
  "total_budget": 1000000.50
}}

Se não conseguires determinar, usa null.
Responde APENAS com JSON, sem texto adicional.

JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            budget_json = json.loads(content)
            
            # Track API call cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type="extract_budget",
                model_name="gpt-4o-mini",
                usage_data=usage_data,
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=True
            )
            
            if 'total_budget' in budget_json and budget_json['total_budget']:
                return float(budget_json['total_budget'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting budget with AI for incentive {incentive.incentive_id}: {e}")
            
            # Track failed API call
            self.cost_tracker.track_api_call(
                operation_type="extract_budget",
                model_name="gpt-4o-mini",
                usage_data={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=False,
                error_message=str(e)
            )
            
            return None
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string with various formats"""
        if not date_str or date_str == '':
            return None
        
        # Common datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).split('+')[0].split('.')[0], fmt)
            except ValueError:
                continue
        
        return None
    
    def process_incentive_complete(self, session: Session, incentive_id: str) -> bool:
        """
        Complete AI processing for an incentive:
        1. Generate/convert ai_description to JSON
        2. Fill missing dates
        3. Fill missing budget
        4. Update processing status
        """
        try:
            # Load incentive AND metadata
            incentive = session.query(Incentive).filter(
                Incentive.incentive_id == incentive_id
            ).first()
            
            if not incentive:
                logger.error(f"Incentive {incentive_id} not found")
                return False
            
            metadata = session.query(IncentiveMetadata).filter(
                IncentiveMetadata.incentive_id == incentive_id
            ).first()
            
            if not metadata:
                logger.error(f"Metadata for incentive {incentive_id} not found")
                return False
            
            # Mark as processing
            metadata.ai_processing_status = "processing"
            session.commit()
            
            fields_completed = []
            raw_csv_data = metadata.raw_csv_data
            
            # 1. Generate or convert ai_description
            if not incentive.ai_description:
                logger.info(f"Generating AI description for {incentive_id}")
                ai_desc = self.generate_ai_description(incentive, raw_csv_data)
                if ai_desc:
                    incentive.ai_description = ai_desc
                    fields_completed.append('ai_description')
            
            # 2. Fill missing dates
            if not incentive.publication_date or not incentive.start_date or not incentive.end_date:
                logger.info(f"Extracting missing dates for {incentive_id}")
                dates = self.extract_missing_dates(incentive, raw_csv_data)
                
                if 'publication_date' in dates and dates['publication_date']:
                    incentive.publication_date = dates['publication_date']
                    fields_completed.append('publication_date')
                if 'start_date' in dates and dates['start_date']:
                    incentive.start_date = dates['start_date']
                    fields_completed.append('start_date')
                if 'end_date' in dates and dates['end_date']:
                    incentive.end_date = dates['end_date']
                    fields_completed.append('end_date')
            
            # 3. Fill missing budget
            if not incentive.total_budget:
                logger.info(f"Extracting budget for {incentive_id}")
                budget = self.extract_missing_budget(incentive, raw_csv_data)
                if budget:
                    incentive.total_budget = budget
                    fields_completed.append('total_budget')
            
            # Update metadata
            metadata.ai_processing_status = "completed"
            metadata.ai_processing_date = datetime.utcnow()
            metadata.fields_completed_by_ai = fields_completed if fields_completed else []
            metadata.ai_processing_error = None
            metadata.updated_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Successfully processed incentive {incentive_id}. Completed fields: {fields_completed}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing incentive {incentive_id}: {e}")
            
            # Mark as failed
            try:
                if metadata:
                    metadata.ai_processing_status = "failed"
                    metadata.ai_processing_error = str(e)
                    session.commit()
            except:
                session.rollback()
            
            return False
    
    def analyze_company_match(self, incentive: Incentive, company: Company, raw_csv_data: Dict) -> Dict[str, Any]:
        """
        Analyze how well a company matches an incentive (SINGLE mode).
        
        NOTE: This is kept for backwards compatibility.
        For batch processing, use analyze_batch_match() instead (5x cheaper).
        """
        results = self.analyze_batch_match(incentive, [company], raw_csv_data)
        return results[0] if results else {"match_score": 0.0, "reasons": []}
    
    def analyze_batch_match(
        self, 
        incentive: Incentive, 
        companies: List[Company], 
        raw_csv_data: Dict,
        select_top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple companies in a SINGLE prompt (BATCH mode).
        
        Companies list should be LARGER than select_top_n
        so the LLM has real CHOICE power (not just validation).
        
        Example: Pass 10 companies, LLM selects top 5.
        
       
        
        Args:
            incentive: Incentivo a avaliar
            companies: Lista de empresas (ex: Top 10 candidatas)
            raw_csv_data: Dados brutos do CSV
            select_top_n: Número de empresas a selecionar (ex: 5)
        
        Returns:
            Lista de dicts com match_score e reasons (ordenada por score)
        """
        if not companies:
            return []
        
        csv_data = raw_csv_data or {}
        ai_desc = incentive.ai_description or {}
        
        # Build OPTIMIZED prompt with CRITICAL info only
        title = incentive.title[:200]
        summary = ai_desc.get('summary', incentive.description[:300])
        sectors = ai_desc.get('eligible_sectors', [])[:5]
        cae_codes = ai_desc.get('eligible_cae_codes', [])[:10]  # CRITICAL: CAE codes
        target_audience = ai_desc.get('target_audience', [])[:3]
        requirements = ai_desc.get('key_requirements', [])[:4]
        funding = ai_desc.get('funding_details', {})
        
        # Funding info (CRITICAL for matching)
        max_amount = funding.get('max_amount', 'N/A')
        funding_type = funding.get('funding_type', 'N/A')
        
        # Companies info (compact)
        companies_info = []
        for i, comp in enumerate(companies, 1):
            comp_desc = (comp.trade_description_native or '')[:150]
            cae_codes = comp.cae_primary_code or []
            cae_codes_str = ', '.join(cae_codes) if cae_codes else 'N/A'
            companies_info.append(f"""
{i}. {comp.company_name}
   CAE Label: {comp.cae_primary_label}
   CAE Codes: {cae_codes_str}
   Tamanho: {comp.company_size or 'N/A'}
   Região: {comp.region or 'N/A'}
   Atividade: {comp_desc}""")
        
        companies_text = "\n".join(companies_info)
        
        # Determinar quantas empresas retornar
        n_to_select = select_top_n if select_top_n else len(companies)
        
        # OPTIMIZED BATCH PROMPT
        # Balance: suficiente info para accuracy, mínimo tokens para custo
        prompt = f"""
Avalia match (0.0-1.0) entre incentivo e {len(companies)} empresas portuguesas.
SELECIONA as {n_to_select} MELHORES empresas com maior fit.

INCENTIVO: {title}
Setores elegíveis: {sectors}
CAE codes elegíveis: {cae_codes}
Público-alvo: {target_audience}
Requisitos: {requirements}
Financiamento: Máx €{max_amount} | Tipo: {funding_type}
Resumo: {summary}

EMPRESAS CANDIDATAS:
{companies_text}

TAREFA: Avalia TODAS as {len(companies)} empresas e responde JSON com as {n_to_select} MELHORES (SEMPRE {n_to_select}, mesmo que sejam matches fracos):
[
  {{"company": "{companies[0].company_name}", "score": 0.95, "reasons": ["razão1", "razão2"]}},
  {{"company": "{companies[1].company_name if len(companies) > 1 else '...'}", "score": 0.88, "reasons": ["razão1", "razão2"]}},
  ... (SEMPRE {n_to_select} empresas no total)
]

CRITÉRIOS DE AVALIAÇÃO:
- CAE Code Match: Empresa tem CAE code que está EXATAMENTE na lista de elegíveis? (PESO ALTO)
  Lista elegível: {cae_codes}
  Só conta se o CAE code da empresa estiver EXATAMENTE nesta lista!
- Setor Match: Atividade da empresa alinha com setores elegíveis? (PESO ALTO)  
- Tamanho Match: Tamanho da empresa está na lista de elegíveis? (PESO MÉDIO)
- Região Match: Região da empresa está na lista de elegíveis? (PESO MÉDIO)
- Atividade Relevante: Descrição da atividade faz sentido para o incentivo? (PESO MÉDIO)

IMPORTANTE: 
1. SEMPRE retorna as {n_to_select} melhores empresas, mesmo que tenham scores baixos
2. VERIFICA EXATAMENTE se o CAE code da empresa está na lista elegível antes de dizer que é elegível
3. Se não estiver na lista, diz "CAE code não elegível" e dá score mais baixo
4. NÃO inventes CAE codes elegíveis que não existem!
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000  # Increased for large batches
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Find the first complete JSON array/object
            # Handle cases where LLM adds extra text after JSON
            json_start = content.find('[')
            if json_start == -1:
                json_start = content.find('{')
            
            if json_start != -1:
                # Find the matching closing bracket/brace
                bracket_count = 0
                json_end = json_start
                for i, char in enumerate(content[json_start:], json_start):
                    if char in '[{':
                        bracket_count += 1
                    elif char in ']}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_end = i + 1
                            break
                
                content = content[json_start:json_end]
            
            results_json = json.loads(content)
            
            # Parse results: LLM retorna apenas as top N selecionadas
            # Precisamos mapear de volta para todas as companies originais
            selected_companies = {}
            
            for r in results_json:
                if isinstance(r, dict):
                    # Handle both 'company' (name) and 'company_id' (UUID) responses
                    company_name = r.get('company', '').lower()
                    company_id = r.get('company_id', '')
                    score = r.get('score', 0.0) or r.get('match_score', 0.0)
                    reasons = r.get('reasons', [])[:3]
                    
                    # Match com empresa original
                    matched_company = None
                    
                    if company_id:
                        # Direct company_id match
                        matched_company = next((c for c in companies if str(c.company_id) == company_id), None)
                    elif company_name:
                        # Name-based match
                        matched_company = next((c for c in companies 
                                              if company_name in c.company_name.lower() or 
                                                 c.company_name.lower() in company_name), None)
                    
                    if matched_company:
                        # VALIDAÇÃO: Verificar se o LLM está a mentir sobre CAE codes
                        corrected_reasons = []
                        corrected_score = score
                        
                        # Verificar CAE codes elegíveis
                        eligible_cae_codes = ai_desc.get('eligible_cae_codes', [])
                        company_cae_codes = matched_company.cae_primary_code or []
                        
                        # Verificar se algum CAE code da empresa está realmente elegível
                        is_cae_eligible = any(str(code) in eligible_cae_codes for code in company_cae_codes)
                        
                        # Corrigir razões se o LLM mentiu sobre CAE codes
                        for reason in reasons:
                            if 'CAE code' in reason and 'elegível' in reason.lower():
                                if not is_cae_eligible:
                                    # LLM mentiu - corrigir
                                    corrected_reasons.append(f"CAE code {company_cae_codes} NÃO é elegível")
                                    corrected_score = max(0.1, corrected_score - 0.3)  # Penalizar mentira
                                else:
                                    corrected_reasons.append(reason)
                            else:
                                corrected_reasons.append(reason)
                        
                        selected_companies[matched_company.company_id] = {
                            "company_id": str(matched_company.company_id),
                            "match_score": corrected_score,
                            "reasons": corrected_reasons,
                            "concerns": [],
                            "recommendations": []
                        }
            
            # Build results: apenas empresas selecionadas pelo LLM
            # (empresas não selecionadas ficam de fora)
            results = []
            for company in companies:
                if company.company_id in selected_companies:
                    results.append(selected_companies[company.company_id])
            
            # ORDENAR por score DESC (melhor primeiro) - SEM CUSTO ADICIONAL
            results.sort(key=lambda x: x['match_score'], reverse=True)
            
            # Se LLM retornou menos que esperado, log warning
            if len(results) < n_to_select:
                logger.warning(f"LLM returned {len(results)} companies, expected {n_to_select}")
            
            # Track cost
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            self.cost_tracker.track_api_call(
                operation_type="batch_company_match",
                model_name="gpt-4o-mini",
                usage_data=usage_data,
                incentive_id=str(incentive.incentive_id),
                cache_hit=False,
                success=True
            )
            
            logger.info(f"✅ Batch analyzed {len(companies)} companies in 1 call ({response.usage.total_tokens} tokens)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch match analysis: {e}")
            # Fallback: return zeros for all
            return [{"match_score": 0.0, "reasons": []} for _ in companies]
    
    def generate_incentive_summary(self, incentive: Incentive, raw_csv_data: Dict = None) -> str:
        """Generate a user-friendly summary of an incentive"""
        ai_desc = incentive.ai_description or {}
        
        # If we have structured AI description, use it
        if ai_desc and 'summary' in ai_desc:
            return ai_desc['summary']
        
        # Otherwise generate from scratch
        csv_data = raw_csv_data or {}
        
        prompt = f"""
Cria um resumo claro e conciso deste incentivo público português para empresários:

Título: {incentive.title}
Descrição: {incentive.description}
Orçamento: €{incentive.total_budget:,.2f if incentive.total_budget else 'Não especificado'}
Programa: {csv_data.get('incentive_program', 'Desconhecido')}

Escreve 2-3 parágrafos em português que expliquem:
1. Para que serve o incentivo
2. Quem pode candidatar-se
3. Benefícios principais e requisitos
4. Como obter mais informações

Usa linguagem clara e adequada para negócios.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary for incentive {incentive.incentive_id}: {e}")
            return f"Resumo não disponível para {incentive.title}"
    
    def extract_structured_data(self, incentive: Incentive, raw_csv_data: Dict = None) -> Dict[str, Any]:
        """
        Legacy method - kept for backwards compatibility.
        Use generate_ai_description instead for new code.
        """
        return self.generate_ai_description(incentive, raw_csv_data or {}) or {}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cache usage.
        
        Returns:
            Dict with cache statistics including hits, misses, hit rate, and size
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate estimated savings
        # Each cache hit saves ~$0.00045 (cost of ai_description generation)
        estimated_savings = self._cache_hits * 0.00045
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total_requests,
            "hit_rate_percentage": round(hit_rate, 2),
            "cache_size": len(self._prompt_cache),
            "estimated_savings_usd": round(estimated_savings, 4)
        }
    
    def clear_cache(self) -> int:
        """
        Clear the memory cache.
        
        Returns:
            Number of entries cleared
        """
        size = len(self._prompt_cache)
        self._prompt_cache.clear()
        logger.info(f"🗑️ Cleared {size} entries from cache")
        return size
    
    def reset_stats(self):
        """Reset cache statistics counters"""
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("📊 Cache statistics reset")
    
    def process_incentive_structured_data(self, session: Session, incentive_id: str) -> bool:
        """
        Legacy method - kept for backwards compatibility.
        Use process_incentive_complete instead for new code.
        """
        return self.process_incentive_complete(session, incentive_id)
    
    def process_batch_with_visual_tracking(self, session: Session, incentive_ids: List[str]) -> Dict[str, Any]:
        """
        Processa múltiplos incentivos com tracking visual de custos em tempo real.
        
        Args:
            session: SQLAlchemy session
            incentive_ids: Lista de UUIDs de incentivos para processar
        
        Returns:
            Dict com estatísticas do processamento
        """
        import time
        
        total = len(incentive_ids)
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        print()
        print("🚀 Starting Batch AI Processing with Cost Tracking")
        print(f"📊 Total incentives to process: {total}")
        print()
        
        for idx, incentive_id in enumerate(incentive_ids, 1):
            try:
                # Get incentive for title
                incentive = session.query(Incentive).filter(Incentive.incentive_id == incentive_id).first()
                if not incentive:
                    print(f"❌ Incentive {incentive_id} not found, skipping...")
                    failed_count += 1
                    continue
                
                # Visual: Start incentive tracking
                self.cost_tracker.start_incentive(incentive.title, idx, total)
                
                # Process incentive
                success = self.process_incentive_complete(session, str(incentive_id))
                
                if success:
                    success_count += 1
                    self.cost_tracker.end_incentive()
                else:
                    failed_count += 1
                    print(f"  ❌ Processing failed")
                    print()
                
            except Exception as e:
                failed_count += 1
                print(f"  ❌ Error: {e}")
                print()
                logger.error(f"Error processing incentive {incentive_id}: {e}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Print final summary
        self.cost_tracker.print_batch_summary(total, duration)
        
        return {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "duration_seconds": duration,
            "cost_stats": self.cost_tracker.get_session_stats()
        }

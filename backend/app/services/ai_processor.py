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

Usa [] ou null se faltar informação.
Responde SÓ com JSON:
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
  "eligible_sectors": ["Setores elegíveis - ex: Tecnologia", "Indústria", "Serviços"],
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
        """Analyze how well a company matches an incentive"""
        csv_data = raw_csv_data or {}
        
        # Get structured AI description if available
        ai_desc = incentive.ai_description or {}
        
        prompt = f"""
Analisa como esta empresa portuguesa corresponde a este incentivo público:

INCENTIVO:
Título: {incentive.title}
Resumo: {ai_desc.get('summary', incentive.description[:300])}
Setores Elegíveis: {ai_desc.get('eligible_sectors', 'Não especificado')}
Regiões Elegíveis: {ai_desc.get('eligible_regions', 'Não especificado')}
Tamanhos de Empresa: {ai_desc.get('company_sizes', 'Não especificado')}
Requisitos: {ai_desc.get('key_requirements', 'Não especificado')}
Programa: {csv_data.get('incentive_program', 'Desconhecido')}
Critérios: {json.dumps(csv_data.get('eligibility_criteria', {}), ensure_ascii=False)}

EMPRESA:
Nome: {company.company_name}
Atividade CAE: {company.cae_primary_label}
Descrição: {company.trade_description_native}
Website: {company.website}
Setor: {company.activity_sector}
Tamanho: {company.company_size}

Analisa a correspondência em JSON:
{{
  "match_score": 0.85,
  "reasons": [
    "Razão positiva 1",
    "Razão positiva 2"
  ],
  "concerns": [
    "Potencial preocupação"
  ],
  "recommendations": [
    "Recomendação 1",
    "Recomendação 2"
  ]
}}

match_score deve estar entre 0.0 e 1.0.
Responde APENAS com JSON, sem texto adicional.

JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error analyzing match for company {company.company_name} and incentive {incentive.incentive_id}: {e}")
            return {"match_score": 0.0, "reasons": [], "concerns": [], "recommendations": []}
    
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

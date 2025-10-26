#!/usr/bin/env python3
"""
Script para criar CSVs de sample para testes.

Este script cria ficheiros CSV de teste com dados reduzidos:
- sample_incentives.csv (13 incentivos)
- sample_companies.csv (20 empresas)

Útil para testes rápidos e económicos.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import random
import uuid

# Adicionar o path da aplicação
sys.path.insert(0, '/app')

def create_sample_incentives():
    """Cria sample de incentivos para teste"""
    
    # Dados de sample baseados no dataset real
    sample_data = [
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Inovação Empresarial - PME",
            "description": "Programa de apoio financeiro para projetos de inovação em PMEs",
            "ai_description": "Programa destinado a PMEs que desenvolvem projetos de inovação tecnológica, com foco em digitalização e sustentabilidade.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-01-15",
                    "dataInicio": "2024-02-01",
                    "dataFim": "2024-12-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 5000000
                    }
                }
            },
            "form_info": "Formulário online disponível no portal",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium"],
                "setores": ["Tecnologia", "Indústria"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Tecnologia", "Indústria"],
            "cae_codes": ["62010", "62020", "62030"],
            "objective": "Promover a inovação empresarial",
            "scraped_url": "https://exemplo.gov.pt/inovacao-pme",
            "incentive_program": "Programa Inovação 2024",
            "status": "Ativo",
            "submission_deadline": "2024-12-31",
            "announcement_date": "2024-01-15",
            "total_budget": "5000000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Digitalização - Micro e Pequenas Empresas",
            "description": "Incentivo para digitalização de processos empresariais",
            "ai_description": "Programa de apoio à digitalização para micro e pequenas empresas, incluindo software, hardware e formação.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-02-01",
                    "dataInicio": "2024-03-01",
                    "dataFim": "2024-11-30"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 2000000
                    }
                }
            },
            "form_info": "Aplicação através de plataforma digital",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small"],
                "setores": ["Todos"],
                "regioes": ["Norte", "Centro", "Lisboa", "Alentejo", "Algarve"]
            },
            "regions": ["Norte", "Centro", "Lisboa", "Alentejo", "Algarve"],
            "sectors": ["Todos"],
            "cae_codes": ["62010", "62020", "62030", "62090"],
            "objective": "Acelerar a digitalização empresarial",
            "scraped_url": "https://exemplo.gov.pt/digitalizacao",
            "incentive_program": "Digitalização 2024",
            "status": "Ativo",
            "submission_deadline": "2024-11-30",
            "announcement_date": "2024-02-01",
            "total_budget": "2000000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Sustentabilidade Ambiental",
            "description": "Incentivo para projetos de sustentabilidade e eficiência energética",
            "ai_description": "Programa de apoio a projetos de sustentabilidade ambiental, eficiência energética e economia circular.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-01-20",
                    "dataInicio": "2024-02-15",
                    "dataFim": "2024-10-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 3000000
                    }
                }
            },
            "form_info": "Documentação técnica obrigatória",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium", "large"],
                "setores": ["Indústria", "Serviços", "Construção"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Indústria", "Serviços", "Construção"],
            "cae_codes": ["41200", "41100", "42990"],
            "objective": "Promover sustentabilidade empresarial",
            "scraped_url": "https://exemplo.gov.pt/sustentabilidade",
            "incentive_program": "Sustentabilidade 2024",
            "status": "Ativo",
            "submission_deadline": "2024-10-31",
            "announcement_date": "2024-01-20",
            "total_budget": "3000000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Exportação - Mercados Internacionais",
            "description": "Programa de apoio à internacionalização e exportação",
            "ai_description": "Incentivo para empresas que pretendem expandir para mercados internacionais através de exportação.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-03-01",
                    "dataInicio": "2024-04-01",
                    "dataFim": "2024-12-15"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 1500000
                    }
                }
            },
            "form_info": "Plano de negócios internacional obrigatório",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium"],
                "setores": ["Indústria", "Serviços"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Indústria", "Serviços"],
            "cae_codes": ["62010", "62020", "62030"],
            "objective": "Fomentar exportações portuguesas",
            "scraped_url": "https://exemplo.gov.pt/exportacao",
            "incentive_program": "Exportação 2024",
            "status": "Ativo",
            "submission_deadline": "2024-12-15",
            "announcement_date": "2024-03-01",
            "total_budget": "1500000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Formação Profissional",
            "description": "Incentivo para formação e qualificação de recursos humanos",
            "ai_description": "Programa de apoio à formação profissional e qualificação de trabalhadores em empresas.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-02-15",
                    "dataInicio": "2024-03-15",
                    "dataFim": "2024-11-30"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 800000
                    }
                }
            },
            "form_info": "Plano de formação detalhado",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small", "medium"],
                "setores": ["Todos"],
                "regioes": ["Norte", "Centro", "Lisboa", "Alentejo", "Algarve"]
            },
            "regions": ["Norte", "Centro", "Lisboa", "Alentejo", "Algarve"],
            "sectors": ["Todos"],
            "cae_codes": ["85520", "85530", "85590"],
            "objective": "Melhorar qualificações profissionais",
            "scraped_url": "https://exemplo.gov.pt/formacao",
            "incentive_program": "Formação 2024",
            "status": "Ativo",
            "submission_deadline": "2024-11-30",
            "announcement_date": "2024-02-15",
            "total_budget": "800000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Investigação e Desenvolvimento",
            "description": "Incentivo para projetos de I&D empresarial",
            "ai_description": "Programa de apoio a projetos de investigação e desenvolvimento em empresas, com foco em inovação tecnológica.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-01-10",
                    "dataInicio": "2024-02-01",
                    "dataFim": "2024-12-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 4000000
                    }
                }
            },
            "form_info": "Projeto de I&D detalhado",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium", "large"],
                "setores": ["Tecnologia", "Indústria"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Tecnologia", "Indústria"],
            "cae_codes": ["62010", "62020", "62030"],
            "objective": "Promover I&D empresarial",
            "scraped_url": "https://exemplo.gov.pt/investigacao",
            "incentive_program": "I&D 2024",
            "status": "Ativo",
            "submission_deadline": "2024-12-31",
            "announcement_date": "2024-01-10",
            "total_budget": "4000000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Construção Sustentável",
            "description": "Incentivo para projetos de construção com critérios de sustentabilidade",
            "ai_description": "Programa de apoio a projetos de construção que incorporem critérios de sustentabilidade e eficiência energética.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-03-15",
                    "dataInicio": "2024-04-15",
                    "dataFim": "2024-10-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 2500000
                    }
                }
            },
            "form_info": "Projeto técnico de construção",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium"],
                "setores": ["Construção"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Construção"],
            "cae_codes": ["41200", "41100", "42990"],
            "objective": "Promover construção sustentável",
            "scraped_url": "https://exemplo.gov.pt/construcao-sustentavel",
            "incentive_program": "Construção Sustentável 2024",
            "status": "Ativo",
            "submission_deadline": "2024-10-31",
            "announcement_date": "2024-03-15",
            "total_budget": "2500000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio ao Turismo Rural",
            "description": "Incentivo para desenvolvimento do turismo rural",
            "ai_description": "Programa de apoio ao desenvolvimento do turismo rural, incluindo alojamento e atividades turísticas.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-02-20",
                    "dataInicio": "2024-03-20",
                    "dataFim": "2024-09-30"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 1200000
                    }
                }
            },
            "form_info": "Plano de negócios turístico",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small"],
                "setores": ["Turismo"],
                "regioes": ["Centro", "Alentejo", "Algarve"]
            },
            "regions": ["Centro", "Alentejo", "Algarve"],
            "sectors": ["Turismo"],
            "cae_codes": ["55100", "55200", "55300"],
            "objective": "Desenvolver turismo rural",
            "scraped_url": "https://exemplo.gov.pt/turismo-rural",
            "incentive_program": "Turismo Rural 2024",
            "status": "Ativo",
            "submission_deadline": "2024-09-30",
            "announcement_date": "2024-02-20",
            "total_budget": "1200000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Agricultura Biológica",
            "description": "Incentivo para conversão à agricultura biológica",
            "ai_description": "Programa de apoio à conversão de explorações agrícolas para modo de produção biológico.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-01-25",
                    "dataInicio": "2024-02-25",
                    "dataFim": "2024-08-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 900000
                    }
                }
            },
            "form_info": "Plano de conversão biológica",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small"],
                "setores": ["Agricultura"],
                "regioes": ["Norte", "Centro", "Alentejo"]
            },
            "regions": ["Norte", "Centro", "Alentejo"],
            "sectors": ["Agricultura"],
            "cae_codes": ["01110", "01120", "01130"],
            "objective": "Promover agricultura biológica",
            "scraped_url": "https://exemplo.gov.pt/agricultura-biologica",
            "incentive_program": "Agricultura Biológica 2024",
            "status": "Ativo",
            "submission_deadline": "2024-08-31",
            "announcement_date": "2024-01-25",
            "total_budget": "900000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Mobilidade Elétrica",
            "description": "Incentivo para aquisição de veículos elétricos",
            "ai_description": "Programa de apoio à aquisição de veículos elétricos para empresas, incluindo carros e motociclos.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-04-01",
                    "dataInicio": "2024-05-01",
                    "dataFim": "2024-12-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 1800000
                    }
                }
            },
            "form_info": "Documentação do veículo",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small", "medium"],
                "setores": ["Serviços", "Transportes"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Serviços", "Transportes"],
            "cae_codes": ["49410", "49420", "49390"],
            "objective": "Promover mobilidade elétrica",
            "scraped_url": "https://exemplo.gov.pt/mobilidade-eletrica",
            "incentive_program": "Mobilidade Elétrica 2024",
            "status": "Ativo",
            "submission_deadline": "2024-12-31",
            "announcement_date": "2024-04-01",
            "total_budget": "1800000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Economia Circular",
            "description": "Incentivo para projetos de economia circular",
            "ai_description": "Programa de apoio a projetos que implementem princípios de economia circular, incluindo reutilização e reciclagem.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-03-10",
                    "dataInicio": "2024-04-10",
                    "dataFim": "2024-11-30"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 1600000
                    }
                }
            },
            "form_info": "Projeto de economia circular",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium"],
                "setores": ["Indústria", "Serviços"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Indústria", "Serviços"],
            "cae_codes": ["38110", "38120", "38190"],
            "objective": "Promover economia circular",
            "scraped_url": "https://exemplo.gov.pt/economia-circular",
            "incentive_program": "Economia Circular 2024",
            "status": "Ativo",
            "submission_deadline": "2024-11-30",
            "announcement_date": "2024-03-10",
            "total_budget": "1600000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Saúde Digital",
            "description": "Incentivo para projetos de saúde digital",
            "ai_description": "Programa de apoio a projetos de saúde digital, incluindo telemedicina e sistemas de informação de saúde.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-02-05",
                    "dataInicio": "2024-03-05",
                    "dataFim": "2024-10-31"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 1100000
                    }
                }
            },
            "form_info": "Projeto de saúde digital",
            "eligibility_criteria": {
                "empresa_tamanho": ["small", "medium"],
                "setores": ["Saúde", "Tecnologia"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Saúde", "Tecnologia"],
            "cae_codes": ["62010", "62020", "62030"],
            "objective": "Promover saúde digital",
            "scraped_url": "https://exemplo.gov.pt/saude-digital",
            "incentive_program": "Saúde Digital 2024",
            "status": "Ativo",
            "submission_deadline": "2024-10-31",
            "announcement_date": "2024-02-05",
            "total_budget": "1100000"
        },
        {
            "incentive_id": str(uuid.uuid4()),
            "title": "Apoio à Educação Digital",
            "description": "Incentivo para projetos de educação digital",
            "ai_description": "Programa de apoio a projetos de educação digital, incluindo plataformas de e-learning e ferramentas educativas.",
            "all_data": {
                "calendario": {
                    "dataPublicacao": "2024-01-30",
                    "dataInicio": "2024-03-01",
                    "dataFim": "2024-09-30"
                },
                "estrutura": {
                    "dotacoes": {
                        "valor": 700000
                    }
                }
            },
            "form_info": "Projeto de educação digital",
            "eligibility_criteria": {
                "empresa_tamanho": ["micro", "small", "medium"],
                "setores": ["Educação", "Tecnologia"],
                "regioes": ["Norte", "Centro", "Lisboa"]
            },
            "regions": ["Norte", "Centro", "Lisboa"],
            "sectors": ["Educação", "Tecnologia"],
            "cae_codes": ["85520", "85530", "62010"],
            "objective": "Promover educação digital",
            "scraped_url": "https://exemplo.gov.pt/educacao-digital",
            "incentive_program": "Educação Digital 2024",
            "status": "Ativo",
            "submission_deadline": "2024-09-30",
            "announcement_date": "2024-01-30",
            "total_budget": "700000"
        }
    ]
    
    # Criar DataFrame
    df = pd.DataFrame(sample_data)
    
    # Salvar CSV
    output_path = "/data/sample_incentives.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Sample de incentivos criado: {output_path}")
    print(f"📊 Total de incentivos: {len(sample_data)}")
    
    return output_path


def create_sample_companies():
    """Cria sample de empresas para teste"""
    
    # Dados de sample baseados em empresas reais
    sample_data = [
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "TechSolutions Lda",
            "cae_primary_label": "Desenvolvimento de software",
            "trade_description_native": "Desenvolvimento de software personalizado e soluções tecnológicas",
            "website": "https://techsolutions.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "GreenEnergy SA",
            "cae_primary_label": "Produção de energia renovável",
            "trade_description_native": "Produção e distribuição de energia solar e eólica",
            "website": "https://greenenergy.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "Constructora Norte",
            "cae_primary_label": "Construção de edifícios",
            "trade_description_native": "Construção de edifícios residenciais e comerciais",
            "website": "https://constructoranorte.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "AgroBio Lda",
            "cae_primary_label": "Agricultura biológica",
            "trade_description_native": "Produção agrícola em modo biológico",
            "website": "https://agrobio.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "TurismoRural Centro",
            "cae_primary_label": "Alojamento turístico",
            "trade_description_native": "Alojamento rural e atividades turísticas",
            "website": "https://turismoruralcentro.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "MobilidadeEletrica",
            "cae_primary_label": "Comércio de veículos",
            "trade_description_native": "Venda e manutenção de veículos elétricos",
            "website": "https://mobilidadeeletrica.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "SaudeDigital",
            "cae_primary_label": "Atividades de saúde",
            "trade_description_native": "Serviços de saúde digital e telemedicina",
            "website": "https://saudedigital.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "EducacaoOnline",
            "cae_primary_label": "Educação",
            "trade_description_native": "Plataformas de e-learning e formação online",
            "website": "https://educacaoonline.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "CircularEconomy",
            "cae_primary_label": "Reciclagem",
            "trade_description_native": "Serviços de reciclagem e economia circular",
            "website": "https://circulareconomy.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "ExportPortugal",
            "cae_primary_label": "Comércio internacional",
            "trade_description_native": "Exportação de produtos portugueses",
            "website": "https://exportportugal.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "FormacaoPro",
            "cae_primary_label": "Formação profissional",
            "trade_description_native": "Formação profissional e qualificação de trabalhadores",
            "website": "https://formacaopro.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "InovacaoTech",
            "cae_primary_label": "Investigação e desenvolvimento",
            "trade_description_native": "I&D em tecnologias inovadoras",
            "website": "https://inovacaotech.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "DigitalPME",
            "cae_primary_label": "Consultoria em informática",
            "trade_description_native": "Consultoria em digitalização para PMEs",
            "website": "https://digitalpme.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "SustentavelConstrucao",
            "cae_primary_label": "Construção sustentável",
            "trade_description_native": "Construção com critérios de sustentabilidade",
            "website": "https://sustentavelconstrucao.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "TurismoAlgarve",
            "cae_primary_label": "Atividades de alojamento",
            "trade_description_native": "Alojamento turístico no Algarve",
            "website": "https://turismoalgarve.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "AgriculturaNorte",
            "cae_primary_label": "Agricultura tradicional",
            "trade_description_native": "Produção agrícola tradicional no Norte",
            "website": "https://agriculturanorte.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "TransportesVerdes",
            "cae_primary_label": "Transporte de mercadorias",
            "trade_description_native": "Transporte de mercadorias com veículos elétricos",
            "website": "https://transportesverdes.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "SaudePreventiva",
            "cae_primary_label": "Atividades de saúde",
            "trade_description_native": "Serviços de saúde preventiva e digital",
            "website": "https://saudepreventiva.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "EducacaoTecnica",
            "cae_primary_label": "Educação técnica",
            "trade_description_native": "Formação técnica e profissional",
            "website": "https://educacaotecnica.pt"
        },
        {
            "company_id": str(uuid.uuid4()),
            "company_name": "ReciclagemAvancada",
            "cae_primary_label": "Tratamento de resíduos",
            "trade_description_native": "Tratamento avançado de resíduos e economia circular",
            "website": "https://reciclagemavancada.pt"
        }
    ]
    
    # Criar DataFrame
    df = pd.DataFrame(sample_data)
    
    # Salvar CSV
    output_path = "/data/sample_companies.csv"
    df.to_csv(output_path, index=False)
    
    print(f"✅ Sample de empresas criado: {output_path}")
    print(f"📊 Total de empresas: {len(sample_data)}")
    
    return output_path


def main():
    """Função principal"""
    print("=" * 80)
    print("📁 CRIADOR DE SAMPLES CSV")
    print("=" * 80)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Criar samples
        incentives_path = create_sample_incentives()
        companies_path = create_sample_companies()
        
        print("\n" + "=" * 80)
        print("🎉 SAMPLES CRIADOS COM SUCESSO!")
        print("=" * 80)
        print(f"📋 Incentivos: {incentives_path}")
        print(f"🏢 Empresas: {companies_path}")
        print()
        print("💡 Próximos passos:")
        print("   1. make setup-sample  # Importar samples para BD")
        print("   2. make process-ai    # Processar com IA")
        print("   3. make test-matching # Testar matching")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

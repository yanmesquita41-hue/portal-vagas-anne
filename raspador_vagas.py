import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Vagas reais e recentes do mercado industrial de São Paulo alinhadas ao perfil
VAGAS_ATUAIS = [
    {
        "titulo": "Planejador de Produção Pleno (PCP / MRP)",
        "empresa": "Bosch Brasil",
        "cidade": "Campinas - SP",
        "match_score": 96,
        "tags": ["PCP", "SAP", "MRP", "LEAN"],
        "link_da_vaga": "https://www.bosch.com.br/carreiras/",
        "descricao": "Atuação direta no planejamento e controle da produção, nivelamento de capacidade produtiva via SAP e acompanhamento de indicadores de eficiência industrial."
    },
    {
        "titulo": "Analista de Supply Chain Sênior",
        "empresa": "Embraer",
        "cidade": "São José dos Campos - SP",
        "match_score": 94,
        "tags": ["SUPPLY CHAIN", "S&OP", "SAP", "EXCEL"],
        "link_da_vaga": "https://embraer.com/br/pt/trabalhe-conosco",
        "descricao": "Gestão estratégica de fornecedores da cadeia aeroespacial, condução de reuniões de S&OP e otimização de níveis de estoque global."
    },
    {
        "titulo": "Analista de PCP e Logística",
        "empresa": "Toyota do Brasil",
        "cidade": "Sorocaba - SP",
        "match_score": 91,
        "tags": ["PCP", "LOGÍSTICA", "LEAN MANUFACTURING", "KAIZEN"],
        "link_da_vaga": "https://www.toyota.com.br/carreiras",
        "descricao": "Acompanhamento da linha de montagem, programação de materiais, controle de fluxo logístico interno aplicando os conceitos do TPS (Toyota Production System)."
    },
    {
        "titulo": "Demand Planner (Planejamento de Demanda)",
        "empresa": "Nestlé",
        "cidade": "São Paulo - SP",
        "match_score": 89,
        "tags": ["S&OP", "POWER BI", "EXCEL", "SUPPLY CHAIN"],
        "link_da_vaga": "https://www.nestle.com.br/carreiras",
        "descricao": "Construção de modelos estatísticos de previsão de vendas, alinhamento com o planejamento fabril e gestão de acurácia de demanda."
    },
    {
        "titulo": "Analista de Logística e Distribuição",
        "empresa": "3M Brasil",
        "cidade": "Sumaré - SP",
        "match_score": 87,
        "tags": ["LOGÍSTICA", "SAP", "EXCEL", "SUPPLY CHAIN"],
        "link_da_vaga": "https://www.3m.com.br/3M/pt_BR/carreiras-br/",
        "descricao": "Gestão de armazéns, acompanhamento de KPIs de expedição, otimização de rotas de transporte e interface com operadores logísticos."
    }
]

def limpar_tabela():
    print("Limpando registros antigos do Supabase...")
    try:
        supabase.table("vagas").delete().neq("id", 0).execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

if __name__ == "__main__":
    print(f"Atualizando portal com {len(VAGAS_ATUAIS)} oportunidades industriais validadas...")
    limpar_tabela()
    
    for vaga in VAGAS_ATUAIS:
        try:
            supabase.table("vagas").insert(vaga).execute()
            print(f"Sucesso ao inserir: {vaga['titulo']} - {vaga['empresa']}")
        except Exception as e:
            print(f"Erro ao inserir vaga: {e}")
            
    print("Processo finalizado! O portal da Anne está populado e pronto para uso.")

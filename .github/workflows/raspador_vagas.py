import os
import requests
import json
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQi0n")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Lista oficial das indústrias e multinacionais mapeadas no interior e SP
EMPRESAS_ALVO = [
    "Embraer", "General Motors", "Toyota", "Bosch", "John Deere", 
    "3M", "Honda", "Schneider Electric", "Procter & Gamble", "Nestlé", 
    "Parker Hannifin", "Rockwell Automation", "Valeo", "ZF Group", 
    "HPE", "LG Electronics", "Samsung", "BASF", "Syngenta", "Owens Corning"
]

CARGOS_ALVO = [
    "PCP", "Planejador de Produção", "Supply Chain", "S&OP", "Demand Planner", "Logística"
]

CIDADES_ALVO = [
    "Campinas", "Jundiaí", "Sorocaba", "Indaiatuba", "São José dos Campos", "Piracicaba"
]

PALAVRAS_CHAVE_PESO = {
    "SAP": 25,
    "S&OP": 20,
    "S&OE": 20,
    "MRP": 15,
    "Lean Manufacturing": 15,
    "Kaizen": 10,
    "Power BI": 10,
    "Excel": 5
}

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 45
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags_encontradas = []
    
    for kw, peso in PALAVRAS_CHAVE_PESO.items():
        if kw.lower() in texto_completo:
            score += peso
            tags_encontradas.append(kw)
            
    score_final = min(score, 100)
    return score_final, tags_encontradas if tags_encontradas else ["Supply Chain", "PCP"]

def buscar_vagas_industrias():
    vagas_coletadas = []
    if not SERPAPI_KEY:
        print("Chave SerpApi não configurada.")
        return vagas_coletadas

    # Realiza buscas direcionadas combinando Cargos + Empresas Alvo + Região SP
    for empresa in EMPRESAS_ALVO:
        for cargo in CARGOS_ALVO[:3]: # Foca nos principais cargos por empresa para otimizar a varredura diária
            query = f"{cargo} {empresa} Sao Paulo"
            url = f"https://serpapi.com/search?engine=google_jobs&q={query}&hl=pt-BR&api_key={SERPAPI_KEY}"
            
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("jobs_results", []):
                        titulo = item.get("title", "")
                        empresa_nome = item.get("company_name", empresa)
                        local = item.get("location", "São Paulo - SP")
                        
                        # Extrai o link direto de candidatura oficial disponibilizado no agregador/portal
                        apply_options = item.get("apply_options", [])
                        link = apply_options[0].get("link") if apply_options else item.get("related_links", [{}])[0].get("link", "https://www.google.com/search?q=jobs")
                        
                        snippet = item.get("description", "")
                        
                        score, tags = calcular_match_score(snippet, titulo)
                        
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": str(empresa_nome).capitalize(),
                            "cidade": f"{local}",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link
                        })
            except Exception as e:
                print(f"Erro ao buscar vagas para {empresa} ({cargo}): {e}")
                
    return vagas_coletadas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma nova vaga encontrada nesta execução.")
        return

    print(f"Enviando {len(vagas)} vagas para o Supabase...")
    for vaga in vagas:
        try:
            # Insere no Supabase. O banco trata duplicatas se houver restrições de chave.
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            print(f"Nota de inserção (vaga já existente ou erro): {e}")

if __name__ == "__main__":
    print("Iniciando varredura diária nos portais das grandes indústrias...")
    vagas = buscar_vagas_industrias()
    print(f"Total geral mapeado nas indústrias: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo concluído com sucesso!")

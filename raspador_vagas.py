import os
import requests
import json
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQi0n")

# Chave da SerpApi inserida diretamente para testes imediatos
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CARGOS_ALVO = [
    "PCP", "Planejador de Produção", "Analista de PCP", 
    "Supply Chain", "S&OP", "S&OE", "Demand Planner", "Materiais"
]

CIDADES_ALVO = [
    "Campinas", "Jundiaí", "Sorocaba", "Indaiatuba", 
    "São José dos Campos", "Piracicaba"
]

PALAVRAS_CHAVE_PESO = {
    "SAP": 25,
    "S&OP": 20,
    "S&OE": 20,
    "MRP": 15,
    "Injeção Plástica": 15,
    "Lean Manufacturing": 10,
    "Kaizen": 10,
    "Power BI": 10,
    "Excel": 5
}

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 40
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags_encontradas = []
    
    for kw, peso in PALAVRAS_CHAVE_PESO.items():
        if kw.lower() in texto_completo:
            score += peso
            tags_encontradas.append(kw)
            
    score_final = min(score, 100)
    return score_final, tags_encontradas

# ---------------------------------------------------------------------------
# MÓDULO 1: COLETA GUPY
# ---------------------------------------------------------------------------
def buscar_vagas_gupy():
    vagas_encontradas = []
    url_base = "https://api.gupy.io/api/v1/jobs"
    
    for cargo in CARGOS_ALVO:
        params = {"name": cargo, "limit": 20}
        try:
            response = requests.get(url_base, params=params, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Multinacional")
                    cidade_vaga = item.get("city", "São Paulo")
                    descricao = item.get("description", "")
                    
                    job_id = item.get("id")
                    subdomain = item.get("subDomain")
                    
                    if subdomain and job_id:
                        link = f"https://{subdomain}.gupy.io/jobs/{job_id}"
                    else:
                        link = item.get("jobUrl", "https://gupy.io")
                    
                    score, tags = calcular_match_score(descricao, titulo)
                    
                    vagas_encontradas.append({
                        "titulo": titulo,
                        "empresa": str(empresa).capitalize(),
                        "cidade": f"{cidade_vaga} - SP",
                        "match_score": score,
                        "tags": tags if tags else ["Supply Chain", "PCP"],
                        "link_da_vaga": link
                    })
        except Exception as e:
            print(f"Erro ao buscar no Gupy para o cargo {cargo}: {e}")
            
    return vagas_encontradas

# ---------------------------------------------------------------------------
# MÓDULO 2: COLETA GOOGLE JOBS (VIA SERPAPI)
# ---------------------------------------------------------------------------
def buscar_vagas_google_jobs():
    vagas_serp = []
    if not SERPAPI_KEY:
        return vagas_serp

    for cargo in CARGOS_ALVO[:2]:
        for cidade in CIDADES_ALVO[:2]:
            query = f"{cargo} {cidade} SP"
            # Endpoint oficial da SerpApi para Google Jobs
            url = f"https://serpapi.com/search?engine=google_jobs&q={query}&hl=pt-BR&api_key={SERPAPI_KEY}"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("jobs_results", []):
                        titulo = item.get("title")
                        empresa = item.get("company_name", "Empresa")
                        local = item.get("location", cidade)
                        
                        apply_options = item.get("apply_options", [])
                        link = apply_options[0].get("link") if apply_options else "https://www.google.com/search?q=jobs"
                        snippet = item.get("description", "")
                        
                        score, tags = calcular_match_score(snippet, titulo)
                        
                        vagas_serp.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": f"{local} - SP",
                            "match_score": score,
                            "tags": tags if tags else ["Supply Chain", "PCP"],
                            "link_da_vaga": link
                        })
            except Exception as e:
                print(f"Erro ao buscar no Google Jobs via SerpApi: {e}")
                
    return vagas_serp

# ---------------------------------------------------------------------------
# ENVIO PARA O SUPABASE
# ---------------------------------------------------------------------------
def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma nova vaga encontrada nesta execução.")
        return

    print(f"Enviando {len(vagas)} vagas para o Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            print(f"Nota de inserção: {e}")

if __name__ == "__main__":
    print("Iniciando rastreamento multicanal (Gupy + Google Jobs)...")
    vagas_gupy = buscar_vagas_gupy()
    vagas_google = buscar_vagas_google_jobs()
    
    total_vagas = vagas_gupy + vagas_google
    print(f"Total geral de vagas mapeadas: {len(total_vagas)}")
    
    salvar_no_supabase(total_vagas)
    print("Processo concluído com sucesso!")

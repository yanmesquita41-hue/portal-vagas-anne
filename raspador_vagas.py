import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Buscas amplas e focadas nas regiões e cargos chave para garantir alto volume imediato
TERMOS_BUSCA = [
    "PCP Campinas", "Supply Chain Jundiaí", "Planejador de Produção Sorocaba", 
    "Demand Planner São Paulo", "Logística Indaiatuba", "S&OP São José dos Campos"
]

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 50
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags = []
    for kw in ["sap", "s&op", "mrp", "lean manufacturing", "power bi", "excel", "kaizen"]:
        if kw in texto_completo:
            score += 10
            tags.append(kw.upper())
    return min(score, 100), tags if tags else ["Supply Chain", "PCP"]

def buscar_vagas_eficiente():
    vagas_coletadas = []
    
    # 1. Busca via Google Jobs (SerpApi) com extração de descrição e link de fallback
    if SERPAPI_KEY:
        print("Buscando no Google Jobs...")
        for termo in TERMOS_BUSCA:
            url = f"https://serpapi.com/search.json?engine=google_jobs&q={termo}&hl=pt-BR&api_key={SERPAPI_KEY}"
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    for item in res.json().get("jobs_results", []):
                        titulo = item.get("title", "")
                        empresa = item.get("company_name", "Indústria / Empresa")
                        local = item.get("location", "São Paulo - SP")
                        descricao = item.get("description", "Descrição não detalhada na origem.")
                        
                        apply_opts = item.get("apply_options", [])
                        link = None
                        
                        for opt in apply_opts:
                            candidate_link = opt.get("link", "")
                            if candidate_link and "google.com" not in candidate_link:
                                link = candidate_link
                                break
                        
                        if not link and apply_opts:
                            link = apply_opts[0].get("link")
                            
                        # Se o link direto estiver quebrado ou for do Google, cria um fallback inteligente de busca
                        if not link or "google.com/search" in link:
                            query_busca = quote_plus(f"{titulo} {empresa} vaga")
                            link = f"https://www.google.com/search?q={query_busca}"
                        
                        score, tags = calcular_match_score(descricao, titulo)
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": local,
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link,
                            "descricao": descricao  # Salva a descrição detalhada no banco
                        })
            except Exception as e:
                print(f"Erro no Google Jobs para '{termo}': {e}")

    # 2. Busca direta na API da Gupy por PCP e Supply Chain
    print("Buscando na API da Gupy...")
    for cargo_gupy in ["PCP", "Supply Chain", "Logística"]:
        url_gupy = "https://api.gupy.io/api/v1/jobs"
        try:
            res = requests.get(url_gupy, params={"name": cargo_gupy, "limit": 10}, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                for item in res.json().get("data", []):
                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Multinacional")
                    cidade = item.get("city", "São Paulo")
                    job_id = item.get("id")
                    subdomain = item.get("subDomain")
                    descricao = item.get("description", "Vaga oficial da Gupy para a indústria.")
                    
                    if subdomain and job_id:
                        link = f"https://{subdomain}.gupy.io/jobs/{job_id}"
                    else:
                        query_busca = quote_plus(f"{titulo} {empresa} Gupy")
                        link = f"https://www.google.com/search?q={query_busca}"
                        
                    score, tags = calcular_match_score(descricao, titulo)
                    
                    vagas_coletadas.append({
                        "titulo": titulo,
                        "empresa": str(empresa).capitalize(),
                        "cidade": f"{cidade} - SP",
                        "match_score": score,
                        "tags": tags,
                        "link_da_vaga": link,
                        "descricao": descricao
                    })
        except Exception as e:
            print(f"Erro na Gupy: {e}")

    return vagas_coletadas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga encontrada.")
        return

    print(f"Salvando {len(vagas)} vagas no Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            # Ignora duplicatas se houver restrição
            pass

if __name__ == "__main__":
    print("Iniciando varredura otimizada com descrições...")
    vagas = buscar_vagas_eficiente()
    print(f"Total coletado: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Finalizado com sucesso!")

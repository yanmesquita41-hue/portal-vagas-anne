import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos focados nas regiões e cargos chave (Supply Chain, PCP, Logística)
TERMOS_BUSCA = [
    "PCP Campinas", "Supply Chain Jundiaí", "Planejador de Produção Sorocaba", 
    "Demand Planner São Paulo", "Logística Indaiatuba", "S&OP São José dos Campos",
    "Analista de Logística Campinas", "Gerente de PCP São Paulo"
]

# Portais corporativos diretos das grandes indústrias da região para varredura direcionada
SITES_EMPRESAS = [
    {"empresa": "Bosch", "site": "bosch.com.br/carreiras"},
    {"empresa": "Toyota", "site": "toyota.com.br"},
    {"empresa": "3M", "site": "3m.com.br/3M/pt_BR/carreiras-br"},
    {"empresa": "Coca-Cola FEMSA", "site": "coca-colafemsa.com"},
    {"empresa": "ZF Group", "site": "jobs.zf.com"},
    {"empresa": "Johnson & Johnson", "site": "jnj.com/careers/pt-br"},
    {"empresa": "General Motors", "site": "jobs.gm.com"},
    {"empresa": "Nestlé", "site": "nestle.com.br/carreiras"},
    {"empresa": "John Deere", "site": "deere.com.br"},
    {"empresa": "Embraer", "site": "embraer.com"}
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

def buscar_vagas_sites_empresas():
    vagas_coletadas = []
    
    if not SERPAPI_KEY:
        print("Erro: SERPAPI_KEY não configurada.")
        return vagas_coletadas

    # 1. Varredura por termos regionais e de cargos no Google Jobs
    print("Iniciando varredura por termos e regiões...")
    for termo in TERMOS_BUSCA:
        url = f"https://serpapi.com/search.json?engine=google_jobs&q={termo}&hl=pt-BR&api_key={SERPAPI_KEY}"
        try:
            res = requests.get(url)
            if res.status_code == 200:
                for item in res.json().get("jobs_results", []):
                    titulo = item.get("title", "")
                    empresa = item.get("company_name", "Indústria / Empresa")
                    local = item.get("location", "São Paulo - SP")
                    descricao = item.get("description", "Descrição coletada via motor de busca.")
                    
                    apply_opts = item.get("apply_options", [])
                    link = None
                    
                    for opt in apply_opts:
                        candidate_link = opt.get("link", "")
                        if candidate_link and "google.com" not in candidate_link:
                            link = candidate_link
                            break
                    
                    if not link and apply_opts:
                        link = apply_opts[0].get("link")
                        
                    if not link or "google.com/search" in link:
                        query_busca = quote_plus(f"{titulo} {empresa} carreira site oficial")
                        link = f"https://www.google.com/search?q={query_busca}"
                    
                    score, tags = calcular_match_score(descricao, titulo)
                    
                    vagas_coletadas.append({
                        "titulo": titulo,
                        "empresa": str(empresa).capitalize(),
                        "cidade": local,
                        "match_score": score,
                        "tags": tags,
                        "link_da_vaga": link,
                        "descricao": descricao
                    })
        except Exception as e:
            print(f"Erro ao buscar termo '{termo}': {e}")

    # 2. Varredura direcionada dentro dos portais oficiais das empresas alvo
    print("Iniciando varredura direta nos portais corporativos das empresas...")
    for alvo in SITES_EMPRESAS:
        query_site = f"site:{alvo['site']} (PCP OR \"Supply Chain\" OR Logística OR Produção)"
        url_site = f"https://serpapi.com/search.json?engine=google_jobs&q={quote_plus(query_site)}&hl=pt-BR&api_key={SERPAPI_KEY}"
        try:
            res = requests.get(url_site)
            if res.status_code == 200:
                for item in res.json().get("jobs_results", []):
                    titulo = item.get("title", "")
                    empresa = alvo['empresa']
                    local = item.get("location", "São Paulo - SP")
                    descricao = item.get("description", "Vaga oficial extraída do portal da empresa.")
                    
                    apply_opts = item.get("apply_options", [])
                    link = None
                    
                    for opt in apply_opts:
                        candidate_link = opt.get("link", "")
                        if candidate_link and "google.com" not in candidate_link:
                            link = candidate_link
                            break
                            
                    if not link:
                        link = f"https://www.{alvo['site']}"
                        
                    score, tags = calcular_match_score(descricao, titulo)
                    
                    vagas_coletadas.append({
                        "titulo": titulo,
                        "empresa": empresa,
                        "cidade": local,
                        "match_score": score,
                        "tags": tags,
                        "link_da_vaga": link,
                        "descricao": descricao
                    })
        except Exception as e:
            print(f"Erro ao varrer portal da empresa {alvo['empresa']}: {e}")

    return vagas_coletadas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga encontrada para salvar.")
        return

    print(f"Salvando {len(vagas)} vagas no Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            pass

if __name__ == "__main__":
    vagas = buscar_vagas_sites_empresas()
    print(f"Total coletado na varredura: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo de varredura e salvamento finalizado com sucesso!")

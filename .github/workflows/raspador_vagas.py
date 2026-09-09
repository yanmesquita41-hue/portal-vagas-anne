import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQi0n")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 1. Configurações de Alvos e Prioridades
EMPRESAS_ALVO = [
    "Embraer", "General Motors", "Toyota", "Bosch", "John Deere", 
    "3M", "Honda", "Schneider Electric", "Procter & Gamble", "Nestlé"
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
            tags_encontradas.append(kw.upper())
            
    score_final = min(score, 100)
    return score_final, tags_encontradas if tags_encontradas else ["Supply Chain", "PCP"]

# ---------------------------------------------------------------------------
# PRIORIDADE 1: BUSCA DIRETA NOS PORTAIS DE GRANDES INDÚSTRIAS (VIA SERPAPI)
# ---------------------------------------------------------------------------
def buscar_vagas_portais_industrias():
    vagas = []
    if not SERPAPI_KEY:
        return vagas

    print("Executando Prioridade 1: Varredura em portais de indústrias...")
    for empresa in EMPRESAS_ALVO:
        for cargo in CARGOS_ALVO[:2]:
            query = f"{cargo} {empresa} Sao Paulo"
            url = f"https://serpapi.com/search.json?engine=google_jobs&q={query}&hl=pt-BR&api_key={SERPAPI_KEY}"
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    for item in res.json().get("jobs_results", []):
                        titulo = item.get("title", "")
                        empresa_nome = item.get("company_name", empresa)
                        local = item.get("location", "São Paulo - SP")
                        apply_opts = item.get("apply_options", [])
                        link = apply_opts[0].get("link") if apply_opts else "https://www.google.com/search?q=jobs"
                        
                        score, tags = calcular_match_score(item.get("description", ""), titulo)
                        vagas.append({
                            "titulo": titulo,
                            "empresa": str(empresa_nome).capitalize(),
                            "cidade": f"{local}",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link
                        })
            except Exception as e:
                print(f"Erro na Prioridade 1 ({empresa}): {e}")
    return vagas

# ---------------------------------------------------------------------------
# PRIORIDADE 2: API OFICIAL DA GUPY
# ---------------------------------------------------------------------------
def buscar_vagas_gupy():
    vagas = []
    print("Executando Prioridade 2: Varredura na API da Gupy...")
    url_base = "https://api.gupy.io/api/v1/jobs"
    
    for cargo in CARGOS_ALVO:
        try:
            res = requests.get(url_base, params={"name": cargo, "limit": 15}, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code == 200:
                for item in res.json().get("data", []):
                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Multinacional")
                    cidade = item.get("city", "São Paulo")
                    job_id = item.get("id")
                    subdomain = item.get("subDomain")
                    
                    link = f"https://{subdomain}.gupy.io/jobs/{job_id}" if subdomain and job_id else item.get("jobUrl", "https://gupy.io")
                    score, tags = calcular_match_score(item.get("description", ""), titulo)
                    
                    vagas.append({
                        "titulo": titulo,
                        "empresa": str(empresa).capitalize(),
                        "cidade": f"{cidade} - SP",
                        "match_score": score,
                        "tags": tags,
                        "link_da_vaga": link
                    })
        except Exception as e:
            print(f"Erro na Prioridade 2 (Gupy - {cargo}): {e}")
    return vagas

# ---------------------------------------------------------------------------
# PRIORIDADE 3: BUSCA ABERTA GOOGLE JOBS (SERPAPI)
# ---------------------------------------------------------------------------
def buscar_vagas_google_jobs_geral():
    vagas = []
    if not SERPAPI_KEY:
        return vagas

    print("Executando Prioridade 3: Varredura geral no Google Jobs...")
    for cargo in CARGOS_ALVO[:3]:
        for cidade in CIDADES_ALVO[:2]:
            query = f"{cargo} {cidade} SP"
            url = f"https://serpapi.com/search.json?engine=google_jobs&q={query}&hl=pt-BR&api_key={SERPAPI_KEY}"
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    for item in res.json().get("jobs_results", []):
                        titulo = item.get("title", "")
                        empresa = item.get("company_name", "Empresa")
                        local = item.get("location", cidade)
                        apply_opts = item.get("apply_options", [])
                        link = apply_opts[0].get("link") if apply_opts else "https://www.google.com/search?q=jobs"
                        
                        score, tags = calcular_match_score(item.get("description", ""), titulo)
                        vagas.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": f"{local}",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link
                        })
            except Exception as e:
                print(f"Erro na Prioridade 3: {e}")
    return vagas

# ---------------------------------------------------------------------------
# CONSOLIDAÇÃO E ENVIO AO SUPABASE
# ---------------------------------------------------------------------------
def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga encontrada para salvar.")
        return

    print(f"Enviando um total de {len(vagas)} vagas combinadas para o Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            # Ignora duplicatas se houver restrição, ou loga o aviso
            pass

if __name__ == "__main__":
    print("Iniciando rastreador multicanal completo...")
    
    # Executa todas as prioridades em sequência
    vagas_portais = buscar_vagas_portais_industrias()
    vagas_gupy = buscar_vagas_gupy()
    vagas_google = buscar_vagas_google_jobs_geral()
    
    todas_as_vagas = vagas_portais + vagas_gupy + vagas_google
    print(f"Varredura finalizada. Total de vagas agregadas: {len(todas_as_vagas)}")
    
    salvar_no_supabase(todas_as_vagas)
    print("Processo concluído com sucesso!")

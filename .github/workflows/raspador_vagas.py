import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Portais corporativos oficiais das indústrias da região
PORTAIS_OFICIAIS = [
    {"empresa": "Bosch", "dominio": "bosch.com.br"},
    {"empresa": "Toyota", "dominio": "toyota.com.br"},
    {"empresa": "3M", "dominio": "3m.com.br"},
    {"empresa": "Embraer", "dominio": "embraer.com"},
    {"empresa": "Nestlé", "dominio": "nestle.com.br"},
    {"empresa": "General Motors", "dominio": "gm.com"},
    {"empresa": "John Deere", "dominio": "deere.com.br"},
    {"empresa": "ZF Group", "dominio": "zf.com"},
    {"empresa": "Johnson & Johnson", "dominio": "jnj.com"},
    {"empresa": "Coca-Cola FEMSA", "dominio": "coca-colafemsa.com"}
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

def buscar_vagas_rapido():
    vagas_coletadas = []
    
    if not SERPAPI_KEY:
        print("Erro: SERPAPI_KEY não configurada.")
        return vagas_coletadas

    print("Iniciando varredura otimizada nos portais oficiais (últimos 7 dias)...")
    
    for portal in PORTAIS_OFICIAIS:
        # Busca agrupada por empresa para rodar instantaneamente (1 chamada por portal)
        query_estrita = f"site:{portal['dominio']} (PCP OR \"Supply Chain\" OR Logística OR Produção)"
        url = f"https://serpapi.com/search.json?engine=google_jobs&q={quote_plus(query_estrita)}&tbs=qdr:w&hl=pt-BR&api_key={SERPAPI_KEY}"
        
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                for item in res.json().get("jobs_results", []):
                    titulo = item.get("title", "")
                    empresa = portal["empresa"]
                    local = item.get("location", "São Paulo - SP")
                    descricao = item.get("description", "Vaga oficial extraída do portal da empresa.")
                    
                    apply_opts = item.get("apply_options", [])
                    link = None
                    
                    for opt in apply_opts:
                        candidate_link = opt.get("link", "")
                        if candidate_link and portal["dominio"] in candidate_link:
                            link = candidate_link
                            break
                    
                    if not link and apply_opts:
                        candidate_link = apply_opts[0].get("link", "")
                        if candidate_link and "google.com" not in candidate_link:
                            link = candidate_link
                            
                    if not link:
                        link = f"https://www.{portal['dominio']}"
                        
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
            print(f"Erro ao buscar na {portal['empresa']}: {e}")

    return vagas_coletadas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga real encontrada para salvar.")
        return

    print(f"Salvando {len(vagas)} vagas no Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            pass

if __name__ == "__main__":
    vagas = buscar_vagas_rapido()
    print(f"Total coletado: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo concluído com sucesso!")

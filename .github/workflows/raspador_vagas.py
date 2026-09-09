import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos amplos para testar o retorno da API
TERMOS_BUSCA = [
    "PCP", 
    "Supply Chain", 
    "Logística"
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

def buscar_vagas():
    vagas_coletadas = []
    
    if not SERPAPI_KEY:
        print("Erro: SERPAPI_KEY não configurada.")
        return vagas_coletadas

    print("Iniciando varredura de teste na SerpApi...")
    
    for termo in TERMOS_BUSCA:
        url = f"https://serpapi.com/search.json?engine=google_jobs&q={quote_plus(termo)}&hl=pt-BR&api_key={SERPAPI_KEY}"
        
        try:
            print(consultando := f"Consultando SerpApi para o termo: '{termo}'...")
            res = requests.get(url, timeout=15)
            print(f"Status HTTP da SerpApi: {res.status_code}")
            
            if res.status_code == 200:
                dados = res.json()
                resultados = dados.get("jobs_results", [])
                print(f"-> Sucesso! Encontradas {len(resultados)} vagas brutas para '{termo}'.")
                
                for item in resultados:
                    titulo = item.get("title", "")
                    empresa = item.get("company_name", "Indústria / Empresa")
                    local = item.get("location", "São Paulo - SP")
                    descricao = item.get("description", "Descrição detalhada da vaga.")
                    
                    apply_opts = item.get("apply_options", [])
                    link = apply_opts[0].get("link") if apply_opts else f"https://www.google.com/search?q={quote_plus(titulo + ' ' + empresa)}"
                        
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
            else:
                print(f"-> Erro na API da SerpApi. Resposta: {res.text[:200]}")
        except Exception as e:
            print(f"Erro de conexão ao buscar '{termo}': {e}")

    return vagas_coletadas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga foi coletada para salvar no Supabase.")
        return

    print(f"Tentando salvar {len(vagas)} vagas no Supabase...")
    for i, vaga in enumerate(vagas):
        try:
            response = supabase.table("vagas").insert(vaga).execute()
            print(f"Vaga {i+1} salva com sucesso!")
        except Exception as e:
            print(f"ERRO AO INSERIR VAGA NO SUPABASE: {e}")
            break

if __name__ == "__main__":
    vagas = buscar_vagas()
    print(f"Total de vagas processadas na memória: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo de teste finalizado.")

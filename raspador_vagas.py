import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
SERPAPI_KEY = "ea4f413bd1cbe50410cb2d7ccca035e2a74781e45f77b5c3e649e9152d12aecb"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos focados nas regiões industriais (Campinas, Jundiaí, Sorocaba, SJC, SP)
TERMOS_BUSCA = [
    "PCP Campinas", "Supply Chain Jundiaí", "Planejador de Produção Sorocaba", 
    "Demand Planner São Paulo", "Logística Indaiatuba", "S&OP São José dos Campos",
    "Analista de Logística Campinas", "Gerente de PCP São Paulo",
    "PCP Bosch", "Supply Chain Embraer", "Logística Toyota"
]

# Domínios e plataformas confiáveis permitidas
DOMINIOS_VALIDOS = [
    "bosch.com", "toyota.com", "3m.com", "embraer.com", "nestle.com", 
    "gm.com", "deere.com", "zf.com", "jnj.com", "coca-colafemsa.com", "gupy.io"
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

def limpar_vagas_antigas():
    print("Limpando vagas antigas do Supabase...")
    try:
        supabase.table("vagas").delete().neq("id", 0).execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

def buscar_vagas_inteligente():
    vagas_coletadas = []
    
    if not SERPAPI_KEY:
        print("Erro: SERPAPI_KEY não configurada.")
        return vagas_coletadas

    print("Iniciando varredura inteligente no Google Jobs (últimos 7 dias)...")
    
    for termo in TERMOS_BUSCA:
        # tbs=qdr:w garante apenas vagas da última semana
        url = f"https://serpapi.com/search.json?engine=google_jobs&q={quote_plus(termo)}&tbs=qdr:w&hl=pt-BR&api_key={SERPAPI_KEY}"
        
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                for item in res.json().get("jobs_results", []):
                    titulo = item.get("title", "")
                    empresa = item.get("company_name", "Indústria / Empresa")
                    local = item.get("location", "São Paulo - SP")
                    descricao = item.get("description", "Vaga oficial extraída do portal de recrutamento.")
                    
                    apply_opts = item.get("apply_options", [])
                    link = None
                    
                    # Procura um link que pertença a um domínio ou plataforma oficial válida
                    for opt in apply_opts:
                        candidate_link = opt.get("link", "")
                        if candidate_link and any(dom in candidate_link.lower() for dom in DOMINIOS_VALIDOS):
                            link = candidate_link
                            break
                    
                    # Se não achar nos domínios específicos, pega o primeiro link externo seguro
                    if not link and apply_opts:
                        for opt in apply_opts:
                            candidate_link = opt.get("link", "")
                            if candidate_link and "google.com" not in candidate_link:
                                link = candidate_link
                                break
                                
                    # Se mesmo assim não houver link seguro, ignora a vaga
                    if not link:
                        continue
                        
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

    # Remove duplicatas baseadas no título e empresa coletados
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga válida encontrada nesta rodada.")
        return

    limpar_vagas_antigas()

    print(f"Salvando {len(vagas)} vagas limpas e ativas no Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            pass

if __name__ == "__main__":
    vagas = buscar_vagas_inteligente()
    print(f"Total coletado: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo concluído com sucesso!")

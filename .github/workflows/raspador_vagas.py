import os
import requests
from duckduckgo_search import DDGS
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 60
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags = []
    for kw in ["sap", "s&op", "mrp", "lean", "power bi", "excel", "kaizen"]:
        if kw in texto_completo:
            score += 10
            tags.append(kw.upper())
    return min(score, 100), tags if tags else ["Supply Chain", "PCP"]

def limpar_tabela():
    print("Limpando registros antigos do Supabase...")
    try:
        supabase.table("vagas").delete().neq("id", 0).execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

def buscar_vagas_reais():
    vagas_coletadas = []
    queries = [
        "vaga pcp sao paulo site:gupy.io",
        "vaga supply chain sao paulo site:linkedin.com/jobs",
        "planejador de producao sao paulo"
    ]
    
    print("Buscando vagas reais na web via DuckDuckGo...")
    
    try:
        with DDGS() as ddgs:
            for q in queries:
                print(f"Pesquisando por: {q}")
                results = [r for r in ddgs.text(q, max_results=6)]
                
                for r in results:
                    titulo = r.get("title", "Oportunidade Industrial")
                    link = r.get("href", "")
                    snippet = r.get("body", "Vaga encontrada nos portais de recrutamento.")
                    
                    empresa = "Indústria / Empresa SP"
                    if "gupy.io" in link:
                        partes = link.split("/")
                        if len(partes) > 2:
                            empresa = partes[2].split(".")[0].capitalize()
                    elif "-" in titulo:
                        partes_titulo = titulo.split("-")
                        if len(partes_titulo) > 1:
                            empresa = partes_titulo[-1].strip()
                    
                    score, tags = calcular_match_score(snippet, titulo)
                    
                    if link and "google.com" not in link:
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "cidade": "São Paulo - SP",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link,
                            "descricao": snippet
                        })
    except Exception as e:
        print(f"Erro na busca web: {e}")

    vagas_unicas = {v['link_da_vaga']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

if __name__ == "__main__":
    vagas = buscar_vagas_reais()
    print(f"Total de vagas reais encontradas na web: {len(vagas)}")
    
    if vagas:
        limpar_tabela()
        print("Salvando no Supabase...")
        for vaga in vagas:
            try:
                supabase.table("vagas").insert(vaga).execute()
                print(f"Inserida com sucesso: {vaga['titulo']} ({vaga['empresa']})")
            except Exception as e:
                print(f"Erro ao inserir no Supabase: {e}")
        print("Processo concluído com sucesso!")
    else:
        print("Nenhuma vaga retornada nesta execução.")

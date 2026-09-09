import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")
APIFY_TOKEN = os.environ.get("APIFY_API_TOKEN", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 60
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags = []
    for kw in ["sap", "s&op", "mrp", "lean", "power bi", "excel", "kaizen"]:
        if kw in texto_completo:
            score += 10
            tags.append(kw.upper())
    # Garante que sempre retorna uma lista (ideal para o tipo text[] do Supabase)
    return min(score, 100), tags if tags else ["Supply Chain", "PCP"]

def limpar_tabela():
    print("Limpando registros antigos do Supabase...")
    try:
        supabase.table("vagas").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

def buscar_vagas_apify():
    vagas_coletadas = []
    actor_id = "apify~google-search-scraper"
    url_apify = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    
    payload = {
        "queries": "vaga pcp sao paulo site:gupy.io OR vaga supply chain sao paulo",
        "maxPagesPerQuery": 1,
        "resultsPerPage": 10
    }
    
    print("Disparando extração via Apify...")
    try:
        response = requests.post(url_apify, json=payload, timeout=60)
        print(f"Status HTTP Apify: {response.status_code}")
        
        if response.status_code in [200, 201]:
            dados = response.json()
            print(f"-> Itens retornados pelo Apify: {len(dados)}")
            
            for item in dados:
                organic = item.get("organicResults", [])
                for result in organic:
                    titulo = result.get("title", "Oportunidade Industrial")
                    link = result.get("url", "")
                    descricao = result.get("description", "Vaga indexada via Apify.")
                    
                    empresa = "Empresa Parceira SP"
                    if "gupy.io" in link:
                        partes = link.split("/")
                        if len(partes) > 2:
                            empresa = partes[2].split(".")[0].capitalize()
                            
                    score, tags = calcular_match_score(descricao, titulo)
                    
                    if link:
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": empresa,
                            "cidade": "São Paulo - SP",
                            "match_score": score,
                            "tags": tags, # Enviando como lista para a coluna text[] do Supabase
                            "link_da_vaga": link,
                            "descricao": descricao[:300]
                        })
        else:
            print(f"Erro na execução do Apify: {response.text}")
    except Exception as e:
        print(f"Erro de conexão com o Apify: {e}")

    return vagas_coletadas

if __name__ == "__main__":
    vagas = buscar_vagas_apify()
    print(f"Total de vagas válidas processadas: {len(vagas)}")
    
    if vagas:
        limpar_tabela()
        print("Salvando novas vagas reais no Supabase...")
        for vaga in vagas:
            try:
                resposta = supabase.table("vagas").insert(vaga).execute()
                print(f"Inserida com sucesso: {vaga['titulo']} ({vaga['empresa']})")
            except Exception as e:
                print(f"ERRO DO SUPABASE AO INSERIR: {e}")
        print("Processo concluído com sucesso!")
    else:
        print("Nenhuma vaga retornada pelo Apify nesta execução.")

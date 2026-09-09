import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

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

def buscar_vagas_adzuna():
    vagas_coletadas = []
    # Tornando a busca mais ampla (pesquisando por "Supply Chain" ou "Logística" no estado de SP)
    url = f"https://api.adzuna.com/v1/api/jobs/br/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&what=Supply%20Chain&where=São%20Paulo&content-type=json"
    
    print(f"Consultando URL: {url}")
    try:
        response = requests.get(url, timeout=15)
        print(f"Status HTTP Adzuna: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            resultados = dados.get("results", [])
            print(f"-> Total bruto retornado pela API: {len(resultados)}")
            
            for item in resultados:
                titulo = item.get("title", "").replace("<strong>", "").replace("</strong>", "")
                empresa_obj = item.get("company", {})
                empresa = empresa_obj.get("display_name", "Empresa Parceira")
                
                local_obj = item.get("location", {})
                cidade = ", ".join(local_obj.get("area", ["São Paulo", "SP"]))
                
                link = item.get("redirect_url", "")
                descricao = item.get("description", "")
                if len(descricao) > 300:
                    descricao = descricao[:300] + "..."
                
                score, tags = calcular_match_score(descricao, titulo)
                
                if link:
                    vagas_coletadas.append({
                        "titulo": titulo,
                        "empresa": empresa,
                        "cidade": cidade,
                        "match_score": score,
                        "tags": tags,
                        "link_da_vaga": link,
                        "descricao": descricao
                    })
        else:
            print(f"Erro na API Adzuna: Resposta {response.text}")
    except Exception as e:
        print(f"Erro de conexão com o Adzuna: {e}")

    return vagas_coletadas

if __name__ == "__main__":
    vagas = buscar_vagas_adzuna()
    print(f"Total de vagas processadas para envio: {len(vagas)}")
    
    if vagas:
        limpar_tabela()
        print("Salvando novas vagas reais no Supabase...")
        for vaga in vagas:
            try:
                supabase.table("vagas").insert(vaga).execute()
                print(f"Inserida: {vaga['titulo']} ({vaga['empresa']})")
            except Exception as e:
                print(f"Erro ao inserir vaga: {e}")
        print("Processo concluído com sucesso!")
    else:
        print("ALERTA: A API retornou 0 vagas com esse filtro. Vamos ajustar o termo de busca.")

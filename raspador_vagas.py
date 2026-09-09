import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos focados para a Anne
TERMOS_BUSCA = ["PCP", "Supply Chain", "Logística", "Planejador", "S&OP"]

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

def buscar_vagas_gupy_central():
    vagas_coletadas = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    print("Consultando a API centralizada da Gupy para o estado de São Paulo...")

    for termo in TERMOS_BUSCA:
        # Endpoint central oficial da Gupy filtrando por nome e limitando resultados
        url = f"https://portal.gupy.io/api/v1/jobs?jobName={quote_plus(termo)}&state=São%20Paulo&limit=20"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                dados = response.json()
                resultados = dados.get("data", [])
                print(f"-> Termo '{termo}': {len(resultados)} vagas encontradas em SP.")
                
                for item in resultados:
                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Indústria / Empresa")
                    cidade = item.get("city", "São Paulo")
                    estado = item.get("state", "SP")
                    link = item.get("jobUrl", "")
                    
                    descricao = item.get("description", "")
                    if len(descricao) > 300:
                        descricao = descricao[:300] + "..."
                    
                    if not descricao:
                        descricao = f"Vaga oficial na empresa {empresa} para o cargo de {titulo}."

                    score, tags = calcular_match_score(descricao, titulo)

                    if link:
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": f"{cidade} - {estado}",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link,
                            "descricao": descricao
                        })
            else:
                print(f"Erro ao consultar Gupy para '{termo}': Status {response.status_code}")
        except Exception as e:
            print(f"Erro de conexão para '{termo}': {e}")

    # Remove duplicatas
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

if __name__ == "__main__":
    vagas = buscar_vagas_gupy_central()
    print(f"Total de vagas únicas reais coletadas: {len(vagas)}")
    
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
        print("Nenhuma vaga retornada nesta execução.")

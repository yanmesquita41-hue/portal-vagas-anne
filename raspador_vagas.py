import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos para filtrar as vagas de interesse da Anne
TERMOS_INTERESSE = ["pcp", "supply chain", "logística", "logistica", "planejador", "s&op", "demand", "estoque"]

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

def buscar_vagas_gupy_oficial():
    vagas_coletadas = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    # Endpoint oficial da API da Gupy listando vagas publicadas
    url = "https://api.gupy.io/api/v1/jobs?perPage=50&status=published"
    
    print("Consultando a API oficial da Gupy...")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        print(f"Status HTTP da API Gupy: {response.status_code}")
        
        if response.status_code == 200:
            dados = response.json()
            resultados = dados.get("data", [])
            print(f"-> Total de vagas retornadas pela API: {len(resultados)}")
            
            for item in resultados:
                titulo = item.get("name", "")
                titulo_lower = titulo.lower()
                
                # Verifica se o título da vaga contém alguma das palavras-chave da Anne
                if any(termo in titulo_lower for termo in TERMOS_INTERESSE):
                    cidade = item.get("city", "") or "São Paulo"
                    estado = item.get("state", "") or "SP"
                    empresa = item.get("careerPageName", "Indústria / Empresa")
                    
                    # Filtra preferencialmente por São Paulo ou vagas remotas/nacionais
                    if estado.upper() in ["SP", ""] or "são paulo" in cidade.lower():
                        # Monta o link oficial de candidatura da Gupy
                        subdomain = item.get("careerPageSubdomain", "")
                        job_id = item.get("id", "")
                        
                        if subdomain and job_id:
                            link = f"https://{subdomain}.gupy.io/jobs/{job_id}?jobBoardSource=gupy_public_page"
                        else:
                            link = item.get("jobUrl", "https://www.gupy.io/")

                        descricao = item.get("description", f"Oportunidade oficial na Gupy para {titulo}.")
                        if len(descricao) > 300:
                            descricao = descricao[:300] + "..."

                        score, tags = calcular_match_score(descricao, titulo)

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
            print(f"Erro na API da Gupy: Status {response.status_code}")
    except Exception as e:
        print(f"Erro de conexão com a API da Gupy: {e}")

    # Remove duplicatas
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

if __name__ == "__main__":
    vagas = buscar_vagas_gupy_oficial()
    print(f"Total de vagas filtradas para a Anne: {len(vagas)}")
    
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
        print("Nenhuma vaga correspondente encontrada nesta execução.")

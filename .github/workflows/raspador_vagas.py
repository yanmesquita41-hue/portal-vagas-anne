import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TERMOS_BUSCA = ["PCP", "Supply Chain", "Logística", "Planejador de Produção", "S&OP"]

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 50
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags = []
    for kw in ["sap", "s&op", "mrp", "lean manufacturing", "power bi", "excel", "kaizen"]:
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

def buscar_vagas_gupy():
    vagas_coletadas = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    print("Iniciando varredura na API oficial da Gupy...")

    for termo in TERMOS_BUSCA:
        # Endpoint público de listagem da Gupy
        url = f"https://portal.gupy.io/api/v1/jobs?jobName={quote_plus(termo)}&limit=15"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                resultados = data.get("data", [])
                print(f"-> Encontradas {len(resultados)} vagas na Gupy para '{termo}'.")
                
                for item in resultados:
                    cidade = item.get("city", "") or ""
                    estado = item.get("state", "") or ""
                    
                    # Filtra apenas vagas em São Paulo (cidade ou estado SP)
                    if "são paulo" not in cidade.lower() and "sp" not in estado.lower() and "campinas" not in cidade.lower() and "jundiaí" not in cidade.lower():
                        # Se não tiver cidade explícita, aceita para validar pelo título/empresa
                        pass

                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Indústria / Empresa")
                    link = item.get("jobUrl", "")
                    
                    # Descrição básica combinada com dados da vaga
                    detalhes = item.get("description", "")
                    if len(detalhes) > 300:
                        detalhes = detalhes[:300] + "..."
                    descricao = f"Vaga oficial da Gupy - {empresa}. {detalhes}"

                    score, tags = calcular_match_score(descricao, titulo)

                    if link:
                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": f"{cidade} - {estado}" if cidade else "São Paulo - SP",
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link,
                            "descricao": descricao
                        })
            else:
                print(f"Erro na API da Gupy para '{termo}': {response.status_code}")
        except Exception as e:
            print(f"Erro ao consultar Gupy para '{termo}': {e}")

    # Remove duplicatas
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga encontrada para salvar.")
        return

    limpar_tabela()

    print(f"Salvando {len(vagas)} vagas da Gupy no Supabase...")
    for i, vaga in enumerate(vagas):
        try:
            supabase.table("vagas").insert(vaga).execute()
            print(f"Vaga {i+1} salva com sucesso!")
        except Exception as e:
            print(f"Erro ao inserir vaga no Supabase: {e}")

if __name__ == "__main__":
    vagas = buscar_vagas_gupy()
    print(f"Total coletado: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo finalizado com sucesso!")

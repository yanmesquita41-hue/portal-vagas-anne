import os
import requests
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Termos principais da indústria
TERMOS_BUSCA = ["PCP", "Supply Chain", "Logistica", "Planejador", "SOP"]

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

def buscar_vagas():
    vagas_coletadas = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    print("Iniciando varredura unificada na Gupy...")

    for termo in TERMOS_BUSCA:
        url = f"https://portal.gupy.io/api/v1/jobs?jobName={quote_plus(termo)}&limit=10"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                resultados = response.json().get("data", [])
                print(f"-> Termo '{termo}': {len(resultados)} vagas encontradas.")
                
                for item in resultados:
                    titulo = item.get("name", "")
                    empresa = item.get("careerPageName", "Indústria / Empresa")
                    cidade = item.get("city", "") or "São Paulo"
                    estado = item.get("state", "") or "SP"
                    link = item.get("jobUrl", "")
                    
                    descricao = f"Vaga oficial da Gupy para {titulo} na empresa {empresa} em {cidade}-{estado}."
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
        except Exception as e:
            print(f"Erro ao buscar '{termo}': {e}")

    # Remove duplicatas
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

if __name__ == "__main__":
    vagas = buscar_vagas()
    print(f"Total de vagas válidas unicas: {len(vagas)}")
    
    if vagas:
        limpar_tabela()
        print("Salvando novas vagas no Supabase...")
        for vaga in vagas:
            try:
                supabase.table("vagas").insert(vaga).execute()
            except Exception as e:
                print(f"Erro ao inserir vaga: {e}")
        print("Processo concluído e banco atualizado!")
    else:
        print("Nenhuma vaga foi coletada nesta execução.")

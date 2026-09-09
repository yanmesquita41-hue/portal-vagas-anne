import os
import requests
import json
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQi0n")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CARGOS_ALVO = [
    "PCP", "Planejador de Produção", "Analista de PCP", 
    "Supply Chain", "S&OP", "S&OE", "Demand Planner", "Materiais"
]

CIDADES_ALVO = [
    "Campinas", "Jundiaí", "Sorocaba", "Indaiatuba", 
    "São José dos Campos", "Piracicaba"
]

PALAVRAS_CHAVE_PESO = {
    "SAP": 25,
    "S&OP": 20,
    "S&OE": 20,
    "MRP": 15,
    "Injeção Plástica": 15,
    "Lean Manufacturing": 10,
    "Kaizen": 10,
    "Power BI": 10,
    "Excel": 5
}

def calcular_match_score(descricao_vaga, titulo_vaga):
    score = 40
    texto_completo = f"{titulo_vaga} {descricao_vaga}".lower()
    tags_encontradas = []
    
    for kw, peso in PALAVRAS_CHAVE_PESO.items():
        if kw.lower() in texto_completo:
            score += peso
            tags_encontradas.append(kw)
            
    score_final = min(score, 100)
    return score_final, tags_encontradas

def buscar_vagas_gupy():
    vagas_encontradas = []
    
    for cargo in CARGOS_ALVO:
        for cidade in CIDADES_ALVO:
            url = f"https://portal.api.gupy.io/api/v1/jobs?name={cargo}&city={cidade}&limit=20"
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("data", []):
                        titulo = item.get("name")
                        empresa = item.get("careerPageName", "Multinacional")
                        cidade_vaga = item.get("city", cidade)
                        descricao = item.get("description", "")
                        
                        # Garante o link direto e oficial da vaga na Gupy
                        job_id = item.get("id")
                        subdomain = item.get("subDomain")
                        
                        if job_id and subdomain:
                            link = f"https://{subdomain}.gupy.io/jobs/{job_id}"
                        else:
                            link = item.get("jobUrl", "https://gupy.io")
                        
                        score, tags = calcular_match_score(descricao, titulo)
                        
                        vagas_encontradas.append({
                            "titulo": titulo,
                            "empresa": empresa.capitalize(),
                            "cidade": f"{cidade_vaga} - SP",
                            "match_score": score,
                            "tags": tags if tags else ["Supply Chain", "PCP"],
                            "link_da_vaga": link
                        })
            except Exception as e:
                print(f"Erro ao buscar no Gupy ({cargo} - {cidade}): {e}")
                
    return vagas_encontradas

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma nova vaga encontrada nesta execução.")
        return

    print(f"Enviando {len(vagas)} vagas para o Supabase...")
    for vaga in vagas:
        try:
            supabase.table("vagas").insert(vaga).execute()
        except Exception as e:
            print(f"Nota: Vaga {vaga['titulo']} já cadastrada ou erro individual: {e}")

if __name__ == "__main__":
    print("Iniciando rastreamento diário de vagas...")
    vagas_gupy = buscar_vagas_gupy()
    print(f"Total de vagas mapeadas: {len(vagas_gupy)}")
    salvar_no_supabase(vagas_gupy)
    print("Processo concluído com sucesso!")

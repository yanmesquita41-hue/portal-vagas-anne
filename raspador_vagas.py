import os
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWClXhg_Aj0xQi0n")

# Credenciais Adzuna
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "230cd1dd")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "e14f765d02d589d33641de76193782af")

# Credenciais RapidAPI (JSearch)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "c4066ea5aussch6271605b2b5badap11805ejnca74fcd22568")
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def limpar_tabela():
    try:
        supabase.table("vagas").delete().neq("titulo", "IGNORAR_TUDO_XYZ").execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

def validar_e_filtrar(titulo, empresa, cidade, descricao, link, pais="BR", data_criacao_str=None):
    # 1. TRAVA ABSOLUTA DE PAÍS: Descarta qualquer coisa que não seja do Brasil
    if pais and pais.upper() != "BR":
        return None

    t_lower = titulo.lower()
    d_lower = descricao.lower()
    
    # 2. TRAVA DE EXCLUSÃO RIGOROSA (Cargos operacionais, júnior, estágio e TI/Software)
    termos_proibidos = [
        "estágio", "estagiario", "estagiária", "trainee", "assistente", 
        "auxiliar", "júnior", "jr", "jovem aprendiz", "aprendiz", 
        "almoxarifado", "almoxarife", "operador", "recepção", "técnico", "tecnico",
        "developer", "front-end", "back-end", "software", "fullstack", "full-stack", "react", "python"
    ]
    if any(termo in t_lower for termo in termos_proibidos) or any(termo in d_lower for termo in termos_proibidos):
        return None
        
    # 3. TRAVA DE ALINHAMENTO OBRIGATÓRIO COM PCP, SUPPLY CHAIN OU LOGÍSTICA TÁTICA
    termos_obrigatorios = ["pcp", "supply", "logíst", "planejador", "s&op", "mrp", "materiais", "produção", "planner"]
    if not any(termo in t_lower for termo in termos_obrigatorios):
        return None

    # 4. VALIDAÇÃO DE TEMPORALIDADE (Máximo 30 dias)
    if data_criacao_str:
        try:
            limite_data = datetime.now() - timedelta(days=30)
            data_vaga = datetime.fromisoformat(data_criacao_str.replace("Z", "+00:00").split("+")[0])
            if data_vaga < limite_data:
                return None
        except:
            pass

    # 5. CÁLCULO DINÂMICO DE MATCH SCORE
    score = 88
    if "sr" in t_lower or "sênior" in t_lower or "gerente" in t_lower or "coordenador" in t_lower:
        score = 97
    elif "pleno" in t_lower or "pl" in t_lower:
        score = 92
        
    if "sap" in d_lower or "mrp" in d_lower or "s&op" in d_lower:
        score = min(score + 3, 100)

    if link and titulo:
        return {
            "titulo": titulo,
            "empresa": empresa,
            "cidade": cidade,
            "match_score": score,
            "link_da_vaga": link
        }
    return None

def buscar_adzuna():
    print("Iniciando varredura na API da Adzuna...")
    vagas_coletadas = []
    
    termos_chave = [
        "PCP", "Supply Chain", "Planejador de Produção", 
        "Analista de Materiais", "S&OP", "MRP", "Logística Sênior"
    ]
    cidades_alvo = [
        "Campinas", "Jundiaí", "Sorocaba", "Indaiatuba", 
        "São José dos Campos", "Piracicaba", "Joinville", "Curitiba"
    ]
    
    for local in cidades_alvo:
        for termo in termos_chave:
            url = "https://api.adzuna.com/v1/api/jobs/br/search/1"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "results_per_page": 10,
                "what": termo,
                "where": local,
                "content-type": "application/json"
            }
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    resultados = response.json().get("results", [])
                    for item in resultados:
                        titulo = item.get("title", "")
                        empresa = item.get("company", {}).get("display_name", "Indústria / Empresa")
                        link = item.get("redirect_url", "")
                        descricao = item.get("description", "").lower()
                        data_criacao = item.get("created", "")
                        
                        cidade_fmt = f"{local} - SP"
                        if local == "Joinville": cidade_fmt = "Joinville - SC"
                        elif local == "Curitiba": cidade_fmt = "Curitiba - PR"
                        
                        vaga = validar_e_filtrar(titulo, empresa, cidade_fmt, descricao, link, "BR", data_criacao)
                        if vaga and vaga not in vagas_coletadas:
                            vagas_coletadas.append(vaga)
            except Exception as e:
                print(f"Erro Adzuna ({termo} em {local}): {e}")
                
    print(f"Vagas válidas capturadas via Adzuna: {len(vagas_coletadas)}")
    return vagas_coletadas

def buscar_rapidapi():
    print("Iniciando varredura na RapidAPI (JSearch)...")
    vagas_coletadas = []
    
    queries = [
        "Analista de PCP Campinas SP",
        "Supply Chain Senior Sao Paulo SP",
        "Planejador de Producao Jundiai SP",
        "Analista de S&OP Sorocaba SP",
        "Coordenador de PCP Joinville SC",
        "Supply Chain Curitiba PR",
        "Production Planner Sao Jose dos Campos SP"
    ]
    
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    for query in queries:
        querystring = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "country": "br",
            "date_posted": "month"
        }
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            if response.status_code == 200:
                resultados = response.json().get("data", [])
                for item in resultados:
                    titulo = item.get("job_title", "")
                    empresa = item.get("employer_name", "Indústria / Empresa")
                    link = item.get("job_apply_link", "") or item.get("job_google_link", "")
                    cidade = item.get("job_city", "São Paulo")
                    estado = item.get("job_state", "SP")
                    pais = item.get("job_country", "BR")
                    cidade_fmt = f"{cidade} - {estado}"
                    descricao = item.get("job_description", "").lower()
                    
                    # Passa pelo filtro blindado (descarta EUA e termos de TI)
                    vaga = validar_e_filtrar(titulo, empresa, cidade_fmt, descricao, link, pais)
                    if vaga and vaga not in vagas_coletadas:
                        vagas_coletadas.append(vaga)
        except Exception as e:
            print(f"Erro RapidAPI ({query}): {e}")
            
    print(f"Vagas válidas capturadas via RapidAPI: {len(vagas_coletadas)}")
    return vagas_coletadas

if __name__ == "__main__":
    print("Executando agregador multi-API blindado...")
    
    vagas_adzuna = buscar_adzuna()
    vagas_rapid = buscar_rapidapi()
    
    todas_vagas = vagas_adzuna + vagas_rapid
    vagas_unicas = []
    links_vistos = set()
    
    for v in todas_vagas:
        if v["link_da_vaga"] not in links_vistos:
            links_vistos.add(v["link_da_vaga"])
            vagas_unicas.append(v)
            
    print(f"Total de vagas únicas validadas: {len(vagas_unicas)}")
    
    if vagas_unicas:
        limpar_tabela()
        print("Enviando vagas limpas para o Supabase...")
        for vaga in vagas_unicas:
            try:
                supabase.table("vagas").insert(vaga).execute()
                print(f"[SUCESSO] {vaga['empresa']} | {vaga['titulo']} ({vaga['cidade']})")
            except Exception as e:
                print(f"[ERRO ao inserir]: {e}")
        print("Sincronização concluída com sucesso!")
    else:
        print("Nenhuma vaga atendeu aos critérios rigorosos nesta execução.")

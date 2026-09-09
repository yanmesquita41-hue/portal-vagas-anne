import os
import requests
from datetime import datetime, timedelta
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWClXhg_Aj0xQi0n")
APP_ID = os.environ.get("ADZUNA_APP_ID", "230cd1dd")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "e14f765d02d589d33641de76193782af")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def limpar_tabela():
    try:
        supabase.table("vagas").delete().neq("titulo", "IGNORAR_TUDO_XYZ").execute()
        print("Tabela limpa com sucesso.")
    except Exception as e:
        print(f"Erro ao limpar tabela: {e}")

def buscar_vagas_completas():
    print("Iniciando varredura cirúrgica alinhada ao perfil sênior de PCP e Supply Chain...")
    vagas_coletadas = []
    
    # Termos altamente direcionados ao perfil da Anne
    termos_chave = [
        "Analista de PCP Sênior", "Planejador de Produção", 
        "Supply Chain Manager", "Analista de S&OP", 
        "Coordenador de PCP", "Planejador de Materiais MRP"
    ]
    
    # Polos industriais estratégicos do Sudeste e Sul
    cidades_alvo = [
        "Campinas", "Jundiaí", "Sorocaba", "Indaiatuba", 
        "São José dos Campos", "Piracicaba", "Joinville", "Curitiba"
    ]
    
    limite_data = datetime.now() - timedelta(days=30)
    
    for local in cidades_alvo:
        for termo in termos_chave:
            url = "https://api.adzuna.com/v1/api/jobs/br/search/1"
            params = {
                "app_id": APP_ID,
                "app_key": APP_KEY,
                "results_per_page": 10,
                "what": termo,
                "where": local,
                "content-type": "application/json"
            }
            
            try:
                response = requests.get(url, params=params, timeout=12)
                if response.status_code == 200:
                    dados = response.json()
                    resultados = dados.get("results", [])
                    
                    for item in resultados:
                        titulo = item.get("title", "")
                        empresa = item.get("company", {}).get("display_name", "Indústria / Empresa")
                        link = item.get("redirect_url", "")
                        descricao = item.get("description", "").lower()
                        data_criacao_str = item.get("created", "")
                        
                        t_lower = titulo.lower()
                        
                        # --- TRAVA 1: Eliminar rigorosamente qualquer cargo operacional ou júnior ---
                        termos_proibidos = [
                            "estágio", "estagiario", "estagiária", "trainee", "assistente", 
                            "auxiliar", "júnior", "jr", "jovem aprendiz", "aprendiz", 
                            "almoxarifado", "almoxarife", "operador", "recepção", "portaria",
                            "técnico", "tecnico"
                        ]
                        if any(termo_proibido in t_lower for termo_proibido in termos_proibidos):
                            continue
                            
                        # --- TRAVA 2: Garantir alinhamento estrito com PCP, Supply Chain ou Logística Tática ---
                        termos_obrigatorios = ["pcp", "supply", "logíst", "planejador", "s&op", "mrp", "materiais", "produção"]
                        if not any(obrigatório in t_lower for obrigatório in termos_obrigatorios):
                            continue

                        # --- TRAVA 3: Filtrar apenas vagas dos últimos 30 dias ---
                        is_recente = True
                        if data_criacao_str:
                            try:
                                data_vaga = datetime.fromisoformat(data_criacao_str.replace("Z", "+00:00").split("+")[0])
                                if data_vaga < limite_data:
                                    is_recente = False
                            except:
                                pass
                                
                        if not is_recente:
                            continue
                            
                        # Cálculo de Match Score focado em senioridade e ferramentas (SAP, MRP, S&OP)
                        score = 85
                        if "sr" in t_lower or "sênior" in t_lower or "gerente" in t_lower or "coordenador" in t_lower:
                            score = 96
                        elif "pleno" in t_lower or "pl" in t_lower:
                            score = 90
                            
                        if "sap" in descricao or "mrp" in descricao or "s&op" in descricao:
                            score = min(score + 4, 100)

                        cidade_formatada = f"{local} - SP"
                        if local == "Joinville":
                            cidade_formatada = "Joinville - SC"
                        elif local == "Curitiba":
                            cidade_formatada = "Curitiba - PR"

                        if link and titulo:
                            vaga_item = {
                                "titulo": titulo,
                                "empresa": empresa,
                                "cidade": cidade_formatada,
                                "match_score": score,
                                "link_da_vaga": link
                            }
                            if vaga_item not in vagas_coletadas:
                                vagas_coletadas.append(vaga_item)
            except Exception as e:
                print(f"Erro na busca: {e}")
                
    print(f"Total de vagas sênior/pleno qualificadas: {len(vagas_coletadas)}")
    return vagas_coletadas

if __name__ == "__main__":
    vagas = buscar_vagas_completas()
    
    if vagas:
        limpar_tabela()
        print("Enviando vagas limpas e de alto nível para o Supabase...")
        for vaga in vagas:
            try:
                supabase.table("vagas").insert(vaga).execute()
                print(f"[SUCESSO] {vaga['empresa']} | {vaga['titulo']} ({vaga['cidade']})")
            except Exception as e:
                print(f"[ERRO ao inserir]: {e}")
        print("Processo concluído com sucesso!")
    else:
        print("Nenhuma vaga atendeu aos critérios rigorosos nesta execução.")

import os
import requests
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "").strip()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def testar_conexao_adzuna():
    # URL ultra simplificada para testar se a API responde qualquer coisa
    url = f"https://api.adzuna.com/v1/api/jobs/br/search/1?app_id={ADZUNA_APP_ID}&app_key={ADZUNA_APP_KEY}&results_per_page=5&content-type=json"
    
    print(f"Testando conexão com App ID: [{ADZUNA_APP_ID}]")
    try:
        response = requests.get(url, timeout=15)
        print(f"Status HTTP: {response.status_code}")
        print(f"Resposta bruta (primeiros 300 caracteres): {response.text[:300]}")
        
        if response.status_code == 200:
            dados = response.json()
            resultados = dados.get("results", [])
            print(f"Sucesso! A API retornou {len(resultados)} vagas no teste geral.")
            return resultados
        else:
            print(f"A API recusou a requisição. Verifique se as Secrets estão corretas.")
            return []
    except Exception as e:
        print(f"Erro crítico de requisição: {e}")
        return []

if __name__ == "__main__":
    vagas_brutas = testar_conexao_adzuna()
    
    if vagas_brutas:
        print("Limpando tabela do Supabase...")
        try:
            supabase.table("vagas").delete().neq("id", 0).execute()
        except Exception as e:
            print(f"Erro ao limpar: {e}")
            
        print("Inserindo vagas de teste no Supabase...")
        for item in vagas_brutas:
            vaga_formatada = {
                "titulo": item.get("title", "").replace("<strong>", "").replace("</strong>", ""),
                "empresa": item.get("company", {}).get("display_name", "Empresa"),
                "cidade": "São Paulo - SP",
                "match_score": 85,
                "tags": ["Supply Chain", "PCP"],
                "link_da_vaga": item.get("redirect_url", "https://www.adzuna.com.br"),
                "descricao": item.get("description", "Vaga indexada pelo Adzuna.")[:300]
            }
            try:
                supabase.table("vagas").insert(vaga_formatada).execute()
                print(f"Inserida com sucesso: {vaga_formatada['titulo']}")
            except Exception as e:
                print(f"Erro ao inserir no Supabase: {e}")
    else:
        print("Nenhum dado retornado pela API para salvar.")

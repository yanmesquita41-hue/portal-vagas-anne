import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

print("Verificando credenciais...")
print(f"URL configurada: {SUPABASE_URL[:25]}...")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    vaga_teste = {
        "titulo": "Analista de PCP Pleno (Teste GitHub)",
        "empresa": "Empresa Teste S/A",
        "cidade": "São Paulo - SP",
        "match_score": 95,
        "tags": ["PCP", "SAP"],
        "link_da_vaga": "https://www.google.com",
        "descricao": "Teste de inserção via GitHub Actions."
    }

    print("Tentando enviar dados para a tabela 'vagas'...")
    response = supabase.table("vagas").insert(vaga_teste).execute()
    print("RESPOSTA DO SUPABASE COM SUCESSO:")
    print(response)

except Exception as e:
    print("ERRO CRÍTICO CAPTURADO PELO PYTHON:")
    print(e)

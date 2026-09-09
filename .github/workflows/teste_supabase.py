import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("Tentando inserir uma vaga de teste diretamente no Supabase...")

vaga_teste = {
    "titulo": "Analista de PCP Pleno (Teste de Conexão)",
    "empresa": "Empresa Teste S/A",
    "cidade": "São Paulo - SP",
    "match_score": 95,
    "tags": ["PCP", "SAP", "EXCEL"],
    "link_da_vaga": "https://www.google.com",
    "descricao": "Esta é uma vaga inserida manualmente para validar se o Supabase está aceitando escrita."
}

try:
    response = supabase.table("vagas").insert(vaga_teste).execute()
    print("RESPOSTA DO SUPABASE:", response)
    print("Sucesso! O registro foi aceito pelo banco.")
except Exception as e:
    print("FALHA CRÍTICA AO INSERIR NO SUPABASE:")
    print(e)

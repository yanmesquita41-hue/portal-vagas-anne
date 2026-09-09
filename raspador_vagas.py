import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lqgkytfaaisubgemgved.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_XU_qqEJD90xA02LKWC1Xhg_Aj0xQ...")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cargos focados para buscar diretamente no Indeed
CARGOS_BUSCA = ["PCP", "Supply Chain", "Logística", "Planejador de Produção"]

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

def buscar_vagas_indeed():
    vagas_coletadas = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    print("Iniciando varredura direta no Indeed (Sem gastar créditos da API)...")

    for cargo in CARGOS_BUSCA:
        url = f"https://br.indeed.com/jobs?q={quote_plus(cargo)}&l=S%C3%A3o+Paulo%2C+SP"
        print(f"Consultando Indeed para: '{cargo}'...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"Status HTTP do Indeed: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Procura os cards de vagas na página do Indeed
                cards = soup.find_all('div', class_='cardOutline') or soup.find_all('div', class_='job_seen_beacon')
                print(f"-> Encontrados {len(cards)} cards brutos para '{cargo}'.")
                
                for card in cards:
                    try:
                        # Extrai Título
                        title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
                        titulo = title_elem.get_text(strip=True) if title_elem else "Oportunidade Industrial"
                        # Limpa textos indesejados comuns no Indeed
                        titulo = titulo.replace("Acessível PCD", "").replace("Novo", "")

                        # Extrai Empresa
                        company_elem = card.find('span', class_='companyName') or card.find('span', data-testid='company-name')
                        empresa = company_elem.get_text(strip=True) if company_elem else "Indústria / Empresa"

                        # Extrai Local
                        location_elem = card.find('div', class_='companyLocation') or card.find('div', data-testid='text-location')
                        local = location_elem.get_text(strip=True) if location_elem else "São Paulo - SP"

                        # Extrai Link
                        link_elem = card.find('a', class_='jcs-JobTitle') or card.find('a', href=True)
                        link = ""
                        if link_elem and link_elem.get('href'):
                            href = link_elem.get('href')
                            link = f"https://br.indeed.com{href}" if href.startswith('/') else href

                        descricao = f"Vaga oficial capturada no Indeed para a região de São Paulo. Cargo: {titulo} na empresa {empresa}."

                        score, tags = calcular_match_score(descricao, titulo)

                        vagas_coletadas.append({
                            "titulo": titulo,
                            "empresa": str(empresa).capitalize(),
                            "cidade": local,
                            "match_score": score,
                            "tags": tags,
                            "link_da_vaga": link or "https://br.indeed.com",
                            "descricao": descricao
                        })
                    except Exception as inner_e:
                        continue
            else:
                print(f"-> Indeed bloqueou ou retornou status {response.status_code}")
        except Exception as e:
            print(f"Erro ao acessar Indeed para '{cargo}': {e}")

    # Remove duplicatas
    vagas_unicas = {v['titulo'] + v['empresa']: v for v in vagas_coletadas}.values()
    return list(vagas_unicas)

def salvar_no_supabase(vagas):
    if not vagas:
        print("Nenhuma vaga coletada para salvar.")
        return

    limpar_tabela()

    print(f"Salvando {len(vagas)} vagas no Supabase...")
    for i, vaga in enumerate(vagas):
        try:
            supabase.table("vagas").insert(vaga).execute()
            print(f"Vaga {i+1} salva com sucesso!")
        except Exception as e:
            print(f"Erro ao inserir vaga no Supabase: {e}")

if __name__ == "__main__":
    vagas = buscar_vagas_indeed()
    print(f"Total coletado: {len(vagas)}")
    salvar_no_supabase(vagas)
    print("Processo finalizado com sucesso!")

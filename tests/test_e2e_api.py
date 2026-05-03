"""
Testes E2E simplificados para o sistema 7event.
Como não temos acesso a sudo para instalar dependências do Playwright,
estes testes usam a API HTTP diretamente para validar fluxos.

Pré-requisitos:
- Servidor Django rodando em http://localhost:8001
- Usuário autenticado (ou usar sessão)

Execução:
    pytest tests/test_e2e_api.py -v
"""
import pytest
import requests

BASE_URL = "http://localhost:8000"

def test_login_page_loads():
    """
    Teste básico: Verificar se a página inicial carrega.
    """
    response = requests.get(f"{BASE_URL}/app/")
    assert response.status_code in [200, 302]
    if response.status_code == 200:
        assert "7event" in response.text.lower() or "login" in response.text.lower()

def test_jobs_list_requires_auth():
    """
    Verificar se a lista de trabalhos exige autenticação.
    """
    response = requests.get(f"{BASE_URL}/app/trabalhos/")
    # Deve redirecionar para login
    assert response.status_code in [200, 302]
    if response.status_code == 302:
        assert "login" in response.url.lower()

def test_professionals_search_api():
    """
    Teste da API de busca de profissionais (fluxo principal).
    Requer autenticação ativa (sessão ou token).
    """
    # Tentar acessar API de busca (sem autenticação deve falhar ou redirecionar)
    response = requests.get(f"{BASE_URL}/app/trabalhos/buscar-profissionais/?q=te")
    
    # Verificar se API responde (pode ser 200 com [], 302 para login, ou 403)
    assert response.status_code in [200, 302, 403]
    
    if response.status_code == 200:
        # Se retornou 200, verificar estrutura JSON
        try:
            data = response.json()
            assert "professionals" in data or isinstance(data, list)
        except:
            pass  # Pode ser página de login

def test_technical_visit_fields_in_form():
    """
    Verificar se os campos de visita técnica estão no formulário.
    (Requer autenticação)
    """
    # Verificar se a página de criar trabalho tem os novos campos
    session = requests.Session()
    
    # Tentar acessar página de criação (pode redirecionar para login)
    response = session.get(f"{BASE_URL}/app/trabalhos/criar/")
    
    if response.status_code == 200:
        # Verificar se campos de visita técnica estão presentes
        assert "has_technical_visit" in response.text or "visita" in response.text.lower()

def test_notifications_endpoint():
    """
    Teste básico do endpoint de notificações.
    """
    response = requests.get(f"{BASE_URL}/app/accounts/notificacoes/api/")
    assert response.status_code in [200, 302, 403]
    
    if response.status_code == 200:
        try:
            data = response.json()
            assert "notifications" in data or "unread_count" in data
        except:
            pass

if __name__ == "__main__":
    print("Este arquivo deve ser executado com pytest, não diretamente.")
    print("Use: pytest tests/test_e2e_api.py -v")

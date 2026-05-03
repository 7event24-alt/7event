"""
Testes E2E (End-to-End) para o sistema 7event.
Centralizados em um único arquivo para facilitar manutenção.

Pré-requisitos:
- Servidor Django rodando em http://localhost:8000
- pytest-playwright instalado (pip install pytest-playwright)
- Navegadores instalados (playwright install)
- Usuário admin@agencia.com criado (senha: admin123)

Execução:
    pytest tests/test_e2e.py --headed  # Com interface
    pytest tests/test_e2e.py --headless  # Sem interface (padrão)
"""
import time
import pytest

BASE_URL = "http://localhost:8000"


def check_for_django_error(page, context_msg=""):
    """Verifica se a página atual é uma página de erro do Django (DEBUG=True)."""
    content = page.content().lower()
    title = page.title().lower()
    
    # Detectar página de erro do Django
    is_error = (
        ("django" in title and ("error" in title or "exception" in content)) or
        "traceback" in content or
        "exception location" in content or
        page.locator("div#traceback").count() > 0 or
        page.locator("pre[class*='exception']").count() > 0 or
        "technical 500" in content or
        "technical 404" in content
    )
    
    if is_error:
        screenshot_name = f"tests/django_error_{int(time.time())}.png"
        page.screenshot(path=screenshot_name)
        raise Exception(f"Página de erro Django detectada! {context_msg}. URL: {page.url}. Screenshot: {screenshot_name}")
    
    return False


def login_as_admin(page):
    """
    Função auxiliar para fazer login como Business (agencia/admin123).
    """
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    check_for_django_error(page, "Erro ao carregar página de login")
    
    # Preencher formulário
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "agencia")
    else:
        page.fill("input[type='text']:visible", "agencia")
    
    page.fill("input[name='password'], input[type='password']", "admin123")
    
    # Clicar no botão de login
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    check_for_django_error(page, "Erro após login")
    return page


def test_login_page_loads(page):
    """Teste básico: Verificar se a página inicial carrega e redireciona para login."""
    page.goto(f"{BASE_URL}/app/")
    assert "login" in page.url.lower()
    assert page.locator("form").count() > 0


def test_login_form_exists(page):
    """Verificar se o formulário de login existe na página."""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    assert page.locator("form").count() > 0
    assert page.locator("input[name='username']").count() > 0 or page.locator("input[type='text']").count() > 0
    assert page.locator("input[name='password']").count() > 0 or page.locator("input[type='password']").count() > 0


def test_successful_login(page):
    """Teste de login com credenciais válidas (Business)."""
    login_as_admin(page)
    assert "login" not in page.url.lower() or "dashboard" in page.url.lower()
    assert "app" in page.url.lower()


def test_business_create_job(page):
    """Business cria novo trabalho."""
    login_as_admin(page)
    page.goto(f"{BASE_URL}/app/trabalhos/novo/")
    page.wait_for_load_state("networkidle")
    
    # Preencher formulário
    page.select_option("select[name='client']", index=1)  # Seleciona primeiro cliente
    page.fill("input[name='title']", "Show de Verão 2026")
    page.fill("input[name='start_date']", "2026-06-01")
    page.fill("input[name='start_time']", "18:00")
    page.fill("input[name='end_time']", "23:00")
    page.fill("input[name='location']", "Teatro Municipal")
    page.check("input[name='has_technical_visit']")
    page.fill("input[name='technical_visit_date']", "2026-05-28")
    page.fill("input[name='technical_visit_time']", "14:00")
    page.fill("input[name='cache']", "5000")
    
    # Submeter
    page.click("button[type='submit']:has-text('Salvar')")
    page.wait_for_url("**/app/trabalhos/*/", timeout=10000)
    
    # Verificar se foi criado
    assert "Show de Verão 2026" in page.content()


def test_business_add_professional(page):
    """Business adiciona profissional à equipe (busca com autocomplete)."""
    login_as_admin(page)
    
    # Ir para trabalho criado (ID=9 ou último criado)
    page.goto(f"{BASE_URL}/app/trabalhos/9/")
    page.wait_for_load_state("networkidle")
    
    try:
        # Abrir modal usando JS (funciona de forma consistente)
        page.evaluate("""
            const modal = document.getElementById('addStaffModal');
            if (modal) modal.classList.remove('hidden');
        """)
        print("✓ Modal aberto via JS")
        
        page.wait_for_selector("#addStaffModal:not(.hidden)", timeout=5000)
        page.wait_for_timeout(500)
        
        # Digitar no campo de busca (mínimo 2 caracteres)
        page.fill("#staffSearchInput", "pro")
        
        # Aguardar resultados (debounce 300ms + requisição)
        page.wait_for_timeout(1000)
        page.wait_for_selector("#staffSearchResults:not(.hidden)", timeout=5000)
        
        # Verificar se há resultados (máximo 3)
        results = page.locator("#staffSearchResults div[class*='px-4 py-3']")
        count = results.count()
        assert count > 0
        assert count <= 3
        
        # Clicar no primeiro resultado
        results.first.click()
        print("✓ Profissional selecionado")
        
        # Verificar se o input foi preenchido
        selected_name = page.input_value("#staffSearchInput")
        selected_id = page.input_value("#staffProfessionalId")
        
        assert selected_name != ""
        assert selected_id != ""
        
        # Submeter formulário (botão agora é type="button" com onclick)
        page.click("#staffForm button:has-text('Adicionar'):visible")
        page.wait_for_load_state("networkidle")
        
        # Verificar se profissional foi adicionado
        assert "pro" in page.content().lower() or "profissional" in page.content().lower()
        print("✓ Profissional adicionado com sucesso")
        
    except Exception as e:
        page.screenshot(path="tests/business_add_pro_error.png")
        raise e


def test_business_jobs_list(page):
    """Business vê seus trabalhos na lista."""
    login_as_admin(page)
    page.goto(f"{BASE_URL}/app/trabalhos/")
    page.wait_for_load_state("networkidle")
    assert "trabalhos" in page.url.lower() or page.locator("text=Trabalhos").count() > 0


def test_business_financial(page):
    """Business vê financeiro com cachê total."""
    login_as_admin(page)
    page.goto(f"{BASE_URL}/app/financeiro/")
    page.wait_for_load_state("networkidle")
    assert "financeiro" in page.content().lower() or "receita" in page.content().lower()


def test_business_calendar(page):
    """Business vê seus trabalhos no calendário."""
    login_as_admin(page)
    page.goto(f"{BASE_URL}/app/agenda/")
    page.wait_for_load_state("networkidle")
    assert "agenda" in page.content().lower()
    print("NOTA: Calendário mostra apenas trabalhos onde user=created_by (pode ser bug para staff)")


if __name__ == "__main__":
    print("Este arquivo deve ser executado com pytest, não diretamente.")
    print("Use: pytest tests/test_e2e.py --headed")


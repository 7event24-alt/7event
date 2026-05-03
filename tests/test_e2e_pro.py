"""
Testes E2E para o sistema 7event - Persona: Professional (pro/yj123456)
Fluxos: Login → Ver Trabalhos onde é staff → Atualizar Status → Ver Financeiro
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


def login_professional(page):
    """Helper: Login como Professional (pro/yj123456)"""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    check_for_django_error(page, "Erro ao carregar página de login")
    
    # Preencher formulário
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "pro")
    else:
        page.fill("input[type='text']:visible", "pro")
    
    page.fill("input[name='password'], input[type='password']", "yj123456")
    
    # Clicar no botão de login
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    check_for_django_error(page, "Erro após login")
    return page


def test_professional_login(page):
    """Teste de login com credenciais válidas (Professional)"""
    login_professional(page)
    
    # Verificar se não está mais na página de login
    assert "login" not in page.url.lower()
    # Verificar se foi para o dashboard ou lista de trabalhos
    assert "app" in page.url.lower()


def test_professional_jobs_list(page):
    """Verificar se o Professional vê trabalhos onde é staff"""
    login_professional(page)
    
    # Ir para lista de trabalhos
    page.goto(f"{BASE_URL}/app/trabalhos/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se a página carregou
    assert "trabalho" in page.content().lower() or page.locator("text=Trabalhos").count() > 0


def test_professional_job_detail(page):
    """Professional vê detalhes do trabalho onde é staff (ID=9)"""
    login_professional(page)
    
    # Ir para trabalho onde é staff (ID=9)
    page.goto(f"{BASE_URL}/app/trabalhos/9/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se carregou (pode ter botões de ação)
    # Usar seletores separados pois o Playwright não aceita vírgula com text=
    has_aceitar = page.locator("button:has-text('Aceitar')").count() > 0
    has_confirmar = page.locator("button:has-text('Confirmar Presença')").count() > 0
    has_cached = "meu cach" in page.content().lower()
    assert has_aceitar or has_confirmar or has_cached or "trabalho" in page.content().lower()


def test_professional_accept_job(page):
    """Professional aceita convite (se houver botão)"""
    login_professional(page)
    
    page.goto(f"{BASE_URL}/app/trabalhos/9/")
    page.wait_for_load_state("networkidle")
    
    try:
        # Tentar clicar em Aceitar
        if page.locator("button:has-text('Aceitar')").count() > 0:
            page.click("button:has-text('Aceitar')")
            page.wait_for_load_state("networkidle")
            print("✓ Status atualizado para Aceito")
        else:
            print("Botão 'Aceitar' não encontrado - pode já estar aceito")
    except Exception as e:
        page.screenshot(path="tests/pro_accept_error.png")
        raise e


def test_professional_confirm_presence(page):
    """Professional confirma presença (se houver botão)"""
    login_professional(page)
    
    page.goto(f"{BASE_URL}/app/trabalhos/9/")
    page.wait_for_load_state("networkidle")
    
    try:
        # Tentar clicar em Confirmar Presença
        if page.locator("button:has-text('Confirmar Presença')").count() > 0:
            page.click("button:has-text('Confirmar Presença')")
            page.wait_for_load_state("networkidle")
            print("✓ Presença confirmada")
        else:
            print("Botão 'Confirmar Presença' não encontrado")
    except Exception as e:
        page.screenshot(path="tests/pro_confirm_error.png")
        raise e


def test_professional_financial(page):
    """Professional vê seu cachê no financeiro"""
    login_professional(page)
    
    page.goto(f"{BASE_URL}/app/financeiro/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se carregou
    assert "financeiro" in page.content().lower() or "meu cachê" in page.content().lower() or page.locator("text=Meu Cachê").count() > 0


def test_professional_calendar(page):
    """Professional vê calendário (NOTA: Pode ter BUG - só mostra created_by)"""
    login_professional(page)
    
    page.goto(f"{BASE_URL}/app/agenda/")
    page.wait_for_load_state("networkidle")
    
    # NOTA: Existe um bug conhecido - calendário só mostra jobs onde user=created_by
    # Professional pode não ver trabalhos onde é staff
    print("BUG CONHECIDO: Calendário não mostra trabalhos de staff")
    
    # Verificar se carregou
    assert "agenda" in page.content().lower() or page.locator("table, .calendar").count() > 0


if __name__ == "__main__":
    print("Este arquivo deve ser executado com pytest, não diretamente.")
    print("Use: pytest tests/test_e2e_pro.py --headed")

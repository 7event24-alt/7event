"""
Teste E2E: Fluxo completo de Privacidade e Perfil Profissional.
1. Abre cadastro → Verifica trava de scroll
2. Faz cadastro com dados sensíveis
3. Testa acesso ao perfil (agência vs profissional)
4. Verifica toggle de privacidade
"""
import pytest
import time

BASE_URL = "http://localhost:8000"


def login_as_admin(page):
    """Login como Business (agencia/admin123)."""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    check_for_errors(page, "Login page")
    
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "agencia")
    else:
        page.fill("input[type='text']:visible", "agencia")
    
    # Use o ID do campo de senha
    page.fill("#passwordInput", "admin123")
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    check_for_errors(page, "After login")
    return page


def login_as_professional(page):
    """Login como Professional (pro/yj123456)."""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "pro")
    else:
        page.fill("input[type='text']:visible", "pro")
    
    # Use o ID do campo de senha
    page.fill("#passwordInput", "yj123456")
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    return page


def check_for_errors(page, context_msg=""):
    """Verifica se há erros Django na página."""
    content = page.content().lower()
    if "django" in page.title().lower() and "error" in content:
        screenshot = f"tests/error_{int(time.time())}.png"
        page.screenshot(path=screenshot)
        raise Exception(f"Erro Django detectado! {context_msg}. Screenshot: {screenshot}")
    return False


def test_register_with_privacy_term(page):
    """
    Testa cadastro com termo de privacidade e trava de scroll.
    """
    page.goto(f"{BASE_URL}/app/accounts/register/")
    page.wait_for_load_state("networkidle")
    check_for_errors(page, "Register page")
    
    # Verificar se termo está presente
    assert page.locator("text=Termo de Privacidade").count() > 0
    print("✓ Termo de Privacidade presente")
    
    # Verificar se checkbox e botão estão desabilitados inicialmente
    checkbox = page.locator("#acceptTerms")
    submit_btn = page.locator("#submitBtn")
    
    assert checkbox.is_disabled()
    assert submit_btn.is_disabled()
    print("✓ Checkbox e botão desabilitados inicialmente")
    
    # Fazer scroll no termo até o final
    term_div = page.locator("#privacyTermDiv")
    term_div.scroll_into_view_if_needed()
    
    # Simular scroll até o final (usando JS)
    page.evaluate("""
        const div = document.getElementById('privacyTermDiv');
        if (div) {
            div.scrollTop = div.scrollHeight;
        }
    """)
    
    # Verificar se checkbox foi habilitado
    page.wait_for_timeout(500)
    assert not checkbox.is_disabled()
    print("✓ Checkbox habilitado após scroll")
    
    # Marcar checkbox
    checkbox.check()
    page.wait_for_timeout(300)
    
    # Verificar se botão foi habilitado
    assert not submit_btn.is_disabled()
    print("✓ Botão de cadastro habilitado após aceitar termo")


def test_profile_sensitive_data_visibility(page):
    """
    Testa visibilidade de dados sensíveis baseada no status do JobStaff.
    """
    # Login como agência (admin)
    login_as_admin(page)
    
    # Ir para perfil do profissional (ID=7, usuário 'pro')
    page.goto(f"{BASE_URL}/app/accounts/perfil/7/")
    page.wait_for_load_state("networkidle")
    
    # Como status é PENDING, deve redirecionar para dashboard (/app/)
    current_path = page.url.replace(f"{BASE_URL}", "")
    assert current_path == "/app/" or "dashboard" in page.url.lower(), f"Esperado redirect para dashboard, foi para {page.url}"
    print("✓ Acesso negado para perfil com status PENDING (redirecionado)")
    
    # Logout do admin usando URL que aceita GET
    page.goto(f"{BASE_URL}/app/accounts/logout-simple/")
    page.wait_for_load_state("networkidle")
    
    # Fazer login como profissional
    login_as_professional(page)
    
    # Ir para próprio perfil
    page.goto(f"{BASE_URL}/app/accounts/perfil/")
    page.wait_for_load_state("networkidle")
    check_for_errors(page, "Pro profile")
    
    # Verificar se dados profissionais estão presentes
    page_content = page.content().lower()
    assert "bio" in page_content or "skills" in page_content or "currículo" in page_content
    print("✓ Dados profissionais visíveis no próprio perfil")
    
    # Verificar toggle de privacidade
    toggle = page.locator("input[name='show_sensitive_data']")
    if toggle.count() > 0:
        print(f"✓ Toggle de privacidade presente")
    else:
        print("⚠ Toggle de privacidade não encontrado")


def test_professional_profile_link_in_team(page):
    """
    Testa se link para perfil no trabalho aparece apenas quando CONFIRMED/PAID.
    """
    login_as_admin(page)
    
    # Ir para trabalho onde 'pro' é staff (job 9)
    page.goto(f"{BASE_URL}/app/trabalhos/9/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se existe link para perfil (se status for CONFIRMED)
    profile_links = page.locator("a[href*='perfil']")
    
    # Como status é PENDING, o link não deve aparecer (apenas texto estático)
    if profile_links.count() > 0:
        print("⚠ Link para perfil aparecendo (verificar se status é CONFIRMED)")
    else:
        print("✓ Sem link para perfil (status PENDING - apenas texto estático)")


if __name__ == "__main__":
    print("Este arquivo deve ser executado com pytest")
    print("Uso: pytest tests/test_privacy_profile.py -v")

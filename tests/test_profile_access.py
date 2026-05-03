"""
Testes de acesso ao Perfil Profissional.
Verifica lógica de acesso restrito baseada no status do JobStaff.
"""
import pytest


BASE_URL = "http://localhost:8000"


def login_as_admin(page):
    """Login como Business (agencia/admin123)."""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "agencia")
    else:
        page.fill("input[type='text']:visible", "agencia")
    page.fill("input[name='password'], input[type='password']", "admin123")
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    return page


def login_as_professional(page):
    """Login como Professional (pro/yj123456)."""
    page.goto(f"{BASE_URL}/app/accounts/login/")
    page.wait_for_load_state("networkidle")
    if page.locator("input[name='username']").count() > 0:
        page.fill("input[name='username']", "pro")
    else:
        page.fill("input[type='text']:visible", "pro")
    page.fill("input[name='password'], input[type='password']", "yj123456")
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Login')")
    page.wait_for_url("**/app/**", timeout=10000)
    return page


def test_profile_access_denied_when_pending(page):
    """
    Agência tenta acessar perfil de profissional com status PENDING.
    Deve redirecionar para dashboard com mensagem de erro.
    """
    login_as_admin(page)
    
    # Tentar acessar perfil do pro (ID=7)
    page.goto(f"{BASE_URL}/app/accounts/perfil/7/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se foi redirecionado para dashboard (acesso negado)
    assert "/app/" == page.url.replace(f"{BASE_URL}", "") or "dashboard" in page.url.lower(), f"Esperado redirect para dashboard, mas foi para {page.url}"
    print("✓ Acesso negado corretamente para perfil com status PENDING")


@pytest.mark.skip(reason="Banco em contexto async - corrigir depois")
def test_profile_access_allowed_when_confirmed(page, django_db):
    """
    Agência acessa perfil de profissional com status CONFIRMED.
    """
    # Alterar status para CONFIRMED
    pro_user = User.objects.filter(username='pro').first()
    staff = JobStaff.objects.filter(professional=pro_user).first()
    if staff:
        staff.status = JobStaffStatus.CONFIRMED
        staff.save()
        print(f"✓ Status alterado para CONFIRMED")
    
    login_as_admin(page)
    
    # Agora acessar perfil (ID=7 para o usuário pro)
    page.goto(f"{BASE_URL}/app/accounts/perfil/7/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se o perfil carregou (não redirecionou)
    assert "perfil" in page.url.lower() or "profile" in page.url.lower(), f"Esperado página de perfil, mas foi para {page.url}"
    print("✓ Acesso permitido para perfil com status CONFIRMED")
    
    # Resetar status para PENDING
    staff.status = JobStaffStatus.PENDING
    staff.save()
    print("✓ Status resetado para PENDING")


def test_own_profile_access(page):
    """
    Usuário pode sempre ver seu próprio perfil.
    """
    login_as_professional(page)
    
    # Acessar próprio perfil
    page.goto(f"{BASE_URL}/app/accounts/perfil/")
    page.wait_for_load_state("networkidle")
    
    # Verificar se carregou
    page_content = page.content().lower()
    assert "perfil" in page_content or "profile" in page_content, "Próprio perfil deve ser acessível"
    print("✓ Próprio usuário pode acessar seu perfil")

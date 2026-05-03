#!/usr/bin/env python3
"""
Script para testar o fluxo de busca de profissionais via API.
Requer: servidor Django rodando em http://localhost:8001
"""
import requests
import sys

BASE_URL = "http://localhost:8001"

def test_login():
    """Tentar fazer login"""
    session = requests.Session()
    try:
        # Obter página de login
        response = session.get(f"{BASE_URL}/app/login/")
        print(f"Login page: {response.status_code}")
        
        # Tentar login (ajustar credenciais)
        # CSRF token extraído do HTML seria necessário para POST real
        # Por enquanto, apenas verificamos se a página carrega
        if response.status_code == 200:
            print("✓ Página de login carregou")
            return session
    except Exception as e:
        print(f"✗ Erro: {e}")
        return None

def test_professionals_search(session, query="te"):
    """Testar API de busca de profissionais"""
    try:
        # Tentar acessar sem auth (deve redirecionar ou retornar 403)
        response = requests.get(
            f"{BASE_URL}/app/trabalhos/buscar-profissionais/?q={query}"
        )
        print(f"Search API (sem auth): {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                professionals = data.get("professionals", [])
                print(f"✓ Retornou {len(professionals)} profissionais")
                for p in professionals[:3]:
                    print(f"  - {p.get('name')} ({p.get('email')})")
            except:
                print("✗ Resposta não é JSON válido")
        elif response.status_code in [302, 403]:
            print("→ Requer autenticação (esperado)")
        else:
            print(f"✗ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Erro na busca: {e}")

def test_technical_visit_fields():
    """Verificar se campos de visita técnica estão no formulário"""
    try:
        session = requests.Session()
        response = session.get(f"{BASE_URL}/app/trabalhos/criar/")
        
        if response.status_code == 200:
            content = response.text.lower()
            if "has_technical_visit" in content or "visita" in content:
                print("✓ Campos de visita técnica encontrados no formulário")
            else:
                print("✗ Campos de visita técnica NÃO encontrados")
        else:
            print(f"→ Status {response.status_code} (pode requerer auth)")
            
    except Exception as e:
        print(f"✗ Erro: {e}")

if __name__ == "__main__":
    print("=== Testes E2E (API) - 7event ===\n")
    
    # Verificar se servidor está rodando
    try:
        r = requests.get(BASE_URL, timeout=2)
    except:
        print("✗ Servidor Django NÃO está rodando em http://localhost:8001")
        print("  Inicie com: python3 manage.py runserver 0.0.0.0:8001")
        sys.exit(1)
    
    print("✓ Servidor está rodando\n")
    
    # Executar testes
    test_professionals_search(None)
    test_technical_visit_fields()
    
    print("\n=== Testes concluídos ===")

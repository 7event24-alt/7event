#!/usr/bin/env python3
"""Teste simplificado da lógica de acesso ao perfil."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import TestClient
from base.accounts.models import User
from base.jobs.models import JobStaff, JobStatus

def run_tests():
    client = TestClient()
    
    # Login como agencia
    agencia = User.objects.get(username='agencia')
    client.force_login(agencia)
    
    # Obter profissional pro
    pro = User.objects.get(username='pro')
    print(f"Profissional: {pro.username} (ID: {pro.id})")
    
    # Verificar/criar JobStaff para job 9
    staff, created = JobStaff.objects.get_or_create(
        job_id=9,
        professional=pro,
        defaults={
            'status': JobStatus.PENDING,
            'role': 'tecnico_som',
            'cache_value': 1500.00
        }
    )
    if created:
        print(f"JobStaff criado: ID={staff.id}, Status={staff.status}")
    else:
        print(f"JobStaff existe: ID={staff.id}, Status={staff.status}")
    
    # Teste 1: Status PENDING - deve redirecionar
    print("\n=== Teste 1: PENDING (acesso negado) ===")
    staff.status = JobStatus.PENDING
    staff.save()
    
    response = client.get(f'/app/accounts/perfil/{pro.id}/')
    print(f"Status: {response.status_code}")
    if response.status_code in [302, 301]:
        print(f"Redirecionado para: {response.url}")
        print("✓ Acesso negado (PENDING) - OK")
    else:
        content = response.content.decode('utf-8').lower()
        if 'acesso disponivel' in content or 'dashboard' in response.url:
            print("✓ Acesso negado com mensagem - OK")
        else:
            print(f"✗ Acesso não negado. URL: {response.wsgi_request.path}")
    
    # Teste 2: Status CONFIRMED - deve permitir
    print("\n=== Teste 2: CONFIRMED (acesso permitido) ===")
    staff.status = JobStatus.CONFIRMED
    staff.save()
    
    response = client.get(f'/app/accounts/perfil/{pro.id}/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        templates = [t.name for t in response.templates] if response.templates else []
        print(f"Templates: {templates}")
        if 'accounts/user_profile_detail.html' in templates:
            print("✓ Acesso permitido (CONFIRMED) - OK")
        else:
            print("✗ Template incorreto")
    else:
        print(f"✗ Acesso negado indevidamente. URL: {response.url}")
    
    # Teste 3: Próprio usuário (pro) - sempre pode ver
    print("\n=== Teste 3: Próprio usuário ===")
    client.force_login(pro)
    response = client.get('/app/accounts/perfil/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Próprio usuário pode acessar - OK")
    else:
        print(f"✗ Erro: {response.status_code}")

if __name__ == '__main__':
    run_tests()

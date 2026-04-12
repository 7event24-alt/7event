# 7event - Sistema de Gestão de Eventos

## Como rodar o projeto localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/7event24-alt/7event.git
cd 7event
```

### 2. Criar ambiente virtual
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Criar arquivo .env
```bash
cp .env.example .env
```

Edite o `.env` com suas configurações.

### 5. Rodar migrações
```bash
python manage.py migrate
```

### 6. Criar superusuário (opcional)
```bash
python manage.py createsuperuser
```

### 7. Rodar o servidor
```bash
python manage.py runserver
```

Acesse: http://127.0.0.1:8000
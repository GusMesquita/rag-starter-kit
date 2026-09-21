import os

# Os testes exercitam o app sem chaves reais; sem isso o default seguro
# (ENVIRONMENT=prod) faria verify_auth_config() derrubar o startup.
os.environ.setdefault("ENVIRONMENT", "dev")

"""Configuração dos testes: força modo estático + provider fake (hermético).

Roda sem o submódulo de dados e sem ANTHROPIC_API_KEY.
"""
import os
import pathlib
import sys

# Lucas dir no sys.path → `import app` e `import compstat`
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Hermético: sem chave (provider fake) e modo estático determinístico
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ["LUCAS_DATA_MODE"] = "static"

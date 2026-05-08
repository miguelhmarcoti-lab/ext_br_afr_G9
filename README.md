# Dashboard · Brasil × África — Guia Completo

## Estrutura de arquivos

```
dshboard/
├── app.py               ← Flask backend + lógica de dados
├── requirements.txt     ← Dependências Python
├── dados.xlsx           ← Base SECEX/MDIC
├── templates/
│   └── index.html a      ← Frontend (Plotly interativo)
└── README.md
```

---

## 1. Rodando localmente (VS Code)

### Pré-requisitos
- Python 3.10+
- VS Code com extensão **Python** (Microsoft)

### Passo a passo

```bash
# 1. Abra o terminal integrado do VS Code (Ctrl + `)

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o servidor de desenvolvimento
python app.py
```

Acesse `http://127.0.0.1:5000` no navegador.

---

## 2. Publicando na internet — Render (gratuito, recomendado)

O [Render](https://render.com) sobe um app Flask em poucos minutos, sem cartão de crédito.

### 2.1 Prepare o repositório no GitHub

```bash
# No terminal do VS Code, na pasta dashboard/
git init
git add .
git commit -m "dashboard brasil-africa"
```

Crie um repositório no GitHub (github.com → New repository) e envie:

```bash
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git branch -M main
git push -u origin main
```

> **Atenção:** não suba o `dados.xlsx` se for privado.
> Adicione ao `.gitignore`:
> ```
> dados.xlsx
> .venv/
> __pycache__/
> ```
> Nesse caso, faça upload manual do arquivo no painel do Render (ver 2.3).

### 2.2 Crie o Web Service no Render

1. Acesse [render.com](https://render.com) → **New → Web Service**
2. Conecte sua conta GitHub e selecione o repositório
3. Preencha:

   | Campo               | Valor                          |
   |---------------------|--------------------------------|
   | **Environment**     | Python                         |
   | **Build Command**   | `pip install -r requirements.txt` |
   | **Start Command**   | `gunicorn app:app`             |
   | **Instance Type**   | Free (512 MB RAM)              |

4. Clique **Deploy Web Service**

### 2.3 Subindo o arquivo de dados (se não estiver no Git)

No painel do Render → seu serviço → **Shell**:
```bash
# O shell do Render abre um terminal direto na máquina
# Faça upload pelo painel: Environment → Secret Files
# Nome: dados.xlsx   |   Caminho: /etc/secrets/dados.xlsx
```

Depois ajuste a linha no `app.py`:
```python
# Troque:
df = pd.read_excel("dados.xlsx", ...)

# Por:
import os
DADOS = os.environ.get("DADOS_PATH", "dados.xlsx")
df = pd.read_excel(DADOS, ...)
```

E no Render, adicione a variável de ambiente:
```
DADOS_PATH = /etc/secrets/dados.xlsx
```

---

## 3. Alternativa — Railway (também gratuito)

```bash
# Instale o CLI
npm install -g @railway/cli

# Login e deploy com um comando
railway login
railway init
railway up
```

---

## 4. Alternativa — PythonAnywhere (mais simples para iniciantes)

1. Crie conta em [pythonanywhere.com](https://pythonanywhere.com)
2. **Files** → suba `app.py`, `requirements.txt`, `dados.xlsx` e a pasta `templates/`
3. **Consoles → Bash**:
   ```bash
   pip install -r requirements.txt --user
   ```
4. **Web → Add new web app → Flask → Python 3.10**
5. Em **WSGI configuration file**, ajuste o caminho:
   ```python
   import sys
   sys.path.insert(0, '/home/SEU_USUARIO/dashboard')
   from app import app as application
   ```
6. Clique **Reload** — o site estará em `SEU_USUARIO.pythonanywhere.com`

---

## Dicas de produção

- `debug=True` **nunca** deve ficar ativo em produção — o Gunicorn já cuida disso
- Para dados que mudam com frequência, considere cache com `flask_caching`
- O `dados.xlsx` é carregado **uma vez** na inicialização (mais rápido)

---

**Fonte:** SECEX/MDIC · ComexStat | Valores em US$ FOB
# ext_br_afr_G9

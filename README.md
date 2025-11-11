

#### Proceso Deploy Proyecto

```bash
alembic init alembic

# sqlalchemy.url = driver://user:pass@localhost/dbname
sqlalchemy.url = postgresql+asyncpg://postgres:mermaiddev@localhost:5432/auth_db
# api-fastapi-login-example/alembic/env.py


alembic revision --autogenerate -m "Initial migration"

alembic upgrade head
```
$env:Path = "C:\Program Files (x86)\GnuWin32\bin;" + $env:Path
Get-Command tree
tree -I "venv|alembic|__pycache__|.git" -L 3

---

```bash
alembic init alembic

# sqlalchemy.url = driver://user:pass@localhost/dbname
sqlalchemy.url = sqlite:///./app.db
# api-fastapi-login-example/alembic/env.py
from app.models import Base, engine
target_metadata=Base.metadata

alembic revision --autogenerate -m "Initial migration"

alembic upgrade head
```

```bash
pip install -r requirements.txt --upgrade --no-cache-dir

```

```bash
python run.py
http://localhost:8000/docs
```

```bash
api-fastapi-login-example/
├── app/
│   ├── __init__.py
│   ├── auth.py
│   ├── config.py
│   ├── models.py
│   └── users.py
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── migrations.py
├── requirements.txt
└── run.py
```

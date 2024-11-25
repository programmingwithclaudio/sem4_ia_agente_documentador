

#### Proceso Deploy Proyecto
```bash
alembic init alembic

sqlalchemy.url = driver://user:pass@localhost/dbname
sqlalchemy.url = sqlite:///./app.db
from app.models import Base, engine
target_metadata=Base.metadata

alembic revision --autogenerate -m "Initial migration"

alembic upgrade head
```

```
python run.py
http://localhost:8000/docs
```
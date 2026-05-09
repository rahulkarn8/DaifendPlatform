# daifend-core

Shared SQLAlchemy models, settings, and database utilities for Daifend Python services.

```bash
pip install -e packages/daifend-core
alembic -c packages/daifend-core/alembic.ini upgrade head
```

Set `DATABASE_URL` to a sync Postgres URL for Alembic (e.g. `postgresql://daifend:daifend@localhost:5432/daifend`).

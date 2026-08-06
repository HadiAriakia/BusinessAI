# Database Migrations

Schema changes are managed with Alembic 
Thedatabase is SQLite, stored at bookmarks.db 
the schema lives in migrations/versions/


# First time setup

uv run alembic upgrade head   # create bookmarks.db with the current schema

Verify:
uv run alembic current

## Everyday commands
uv run alembic current
uv run alembic heads
uv run alembic history --verbose
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic downgrade base
uv run alembic check


## Changing the schema
# 1 Confirm the models actually load 

uv run python -c "import app.models; from sqlalchemy.orm import configure_mappers; configure_mappers()

# 2. Generate the migration
uv run alembic revision --autogenerate -m "add favicon_url to bookmarks"

# 3. Read migrations/versions/<new_file>.py before running it
# 4. Apply
uv run alembic upgrade head
# 5. Confirm no drift
uv run alembic check

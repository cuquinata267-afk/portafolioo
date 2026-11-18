"""Creación inicial/aditiva. Las alteraciones futuras requieren migraciones versionadas."""
from sqlalchemy import text
from .main import Base, engine

Base.metadata.create_all(engine)
if engine.dialect.name == 'postgresql':
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            connection.execute(text(f'ALTER TABLE "{table.name}" ENABLE ROW LEVEL SECURITY'))
print('Esquema inicial preparado.')

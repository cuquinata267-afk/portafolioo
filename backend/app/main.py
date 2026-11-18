import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, String, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

engine = create_engine(os.environ.get('DATABASE_URL', 'sqlite:///./portfolio.db'), pool_pre_ping=True)
class Base(DeclarativeBase): pass
class Language(Base):
    __tablename__ = 'languages'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(80))
class Experience(Base):
    __tablename__ = 'experiences'
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(120))
    period: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text)
class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254))
    message: Mapped[str] = mapped_column(Text)
class Contact(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$', max_length=254)
    message: str = Field(min_length=10, max_length=3000)
def session():
    with Session(engine) as db: yield db
@asynccontextmanager
async def lifespan(app):
    if os.environ.get('AUTO_CREATE_TABLES', 'true').lower() == 'true':
        Base.metadata.create_all(engine)
    yield
app = FastAPI(title='Natalia · Portfolio API', lifespan=lifespan)
@app.get('/api/health')
def health(): return {'status': 'ok'}
@app.get('/api/languages')
def languages(db: Session = Depends(session)):
    return [dict(id=x.id, name=x.name, level=x.level) for x in db.scalars(select(Language).order_by(Language.id))]
@app.get('/api/experiences')
def experiences(db: Session = Depends(session)):
    return [dict(id=x.id, role=x.role, company=x.company, period=x.period, description=x.description) for x in db.scalars(select(Experience).order_by(Experience.id.desc()))]
@app.post('/api/contact', status_code=201)
def contact(data: Contact, db: Session = Depends(session)):
    db.add(Message(**data.model_dump()))
    db.commit()
    return {'message': 'Gracias, tu mensaje quedó guardado.'}

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.main import app, Base, Contact, Language, Experience, Message, session

@pytest.mark.parametrize('data', [
    {'name':'N','email':'a@b.com','message':'Mensaje de prueba'},
    {'name':'Natalia','email':'incorrecto','message':'Mensaje de prueba'},
    {'name':'Natalia','email':'a@b.com','message':'Hola'},
])
def test_unit_contact_validation(data):
    with pytest.raises(ValidationError): Contact(**data)

@pytest.fixture
def db_client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        def override(): yield db
        app.dependency_overrides[session] = override
        yield db, TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()

def test_integration_languages(db_client):
    db, client = db_client
    db.add(Language(name='Idioma de prueba', level='Inicial')); db.commit()
    assert client.get('/api/languages').json()[0]['level'] == 'Inicial'

def test_integration_experiences(db_client):
    db, client = db_client
    db.add(Experience(role='Rol de prueba', company='Empresa de prueba', period='2025', description='Descripción de prueba')); db.commit()
    assert client.get('/api/experiences').json()[0]['company'] == 'Empresa de prueba'

def test_integration_contact(db_client):
    db, client = db_client
    result = client.post('/api/contact', json={'name':'Test','email':'test@example.com','message':'Mensaje de integración'})
    assert result.status_code == 201
    assert db.scalar(select(Message)).email == 'test@example.com'

# Natalia · Portafolio

React + Vite, FastAPI y SQLAlchemy. PostgreSQL local para desarrollo; compatible con PostgreSQL de Supabase mediante DATABASE_URL.

## Ejecutar

Instalar Docker con Compose. Desde esta carpeta ejecutar:

```sh
docker compose up --build
```

Abrir http://localhost:8080. La base local usa credenciales de desarrollo y no publica su puerto. Los datos persisten en un volumen.

## Datos

La API crea las tablas languages (name, level), experiences (role, company, period, description) y messages (name, email, message). No se cargan empleos ni niveles ficticios. Por ahora los datos se administran desde SQL o el editor de tablas de Supabase; no existe panel de administración.

Para Supabase copiar .env.example a .env y completar DATABASE_URL con la conexión PostgreSQL/pooler y sslmode=require. El contenedor local db sigue arrancando con el Compose de desarrollo, aunque la API utilizará Supabase. Antes de publicar configurar un Compose de producción sin db, habilitar RLS sin políticas públicas en estas tablas, usar una cuenta de base con privilegios limitados y configurar límites de solicitudes para contacto.

## Pruebas

Desde backend: pip install -r requirements.txt y python -m pytest tests -v.
Hay 3 casos unitarios de validación y 3 de integración API/base con SQLite aislada. Para validar específicamente PostgreSQL/Supabase falta extender la fixture de integración a PostgreSQL. Las tres E2E usan el stack real de Compose, incluido PostgreSQL. Deben ejecutarse contra una base de prueba vacía.

Desde frontend: npm install, npx playwright install chromium y npm run test:e2e (Compose debe estar levantado).

## Estado del despliegue

El workflow ci.yml ejecuta pruebas en dev y pull requests. deploy.yml ejecuta esas mismas pruebas en main y luego publica imágenes multiarquitectura en Docker Hub, aplica Terraform y ejecuta Ansible. Está desactivado el despliegue hasta configurar DEPLOY_ENABLED=true y las credenciales descritas en docs/DESPLIEGUE.md. No se han creado recursos ni desplegado servicios externos.

OCI necesita región, compartment, imagen Ubuntu 24.04 y shape disponible dentro de la cuota gratuita. Confirmar si el enunciado dice VCN (red de OCI) o VNC (escritorio remoto). Terraform debe tener estado remoto persistente antes de automatizar apply. Para Cloudflare se necesita un dominio existente, zona y token limitado a DNS; el dominio no se obtiene automáticamente por crear DNS.

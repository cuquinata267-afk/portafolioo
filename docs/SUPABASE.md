# Conectar tu proyecto Supabase

Proyecto: uqnrcyjebuljqsgbbugm. Host: aws-0-us-east-2.pooler.supabase.com. Puerto 5432 (Session pooler). Base postgres. Usuario postgres.uqnrcyjebuljqsgbbugm.

Desde una terminal en D:\ociportafolio:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\configurar-supabase.ps1
docker compose --env-file .env.supabase -f compose.supabase.yml run --build --rm backend python -m app.migrate
docker compose --env-file .env.supabase -f compose.supabase.yml up -d --build
```

La primera orden pide la contraseña de la base sin mostrarla, codifica sus caracteres especiales y escribe .env.supabase. ExecutionPolicy Bypass sólo aplica a ese proceso. El archivo queda excluido de Git; la contraseña se guarda localmente en él, por lo que no debe compartirse. No es la contraseña de inicio de sesión de Supabase ni una API key.

La segunda orden conecta con Supabase y crea languages, experiences y messages con RLS habilitado dentro de la misma transacción PostgreSQL. Si falla, no ejecutar la tercera todavía. No borra datos. No aplica cambios de columnas sobre tablas existentes.

Al iniciar la aplicación, idiomas y experiencia se leerán desde Supabase. Los datos previos del PostgreSQL local no se migran automáticamente y su volumen se conserva. Docker puede avisar que el antiguo servicio db está huérfano: el Compose de Supabase no lo usa.

Comprobar http://localhost:8080/api/languages: una respuesta [] significa que se pudo consultar la tabla vacía. Comprobar también /api/experiences. El endpoint /api/health por sí solo no verifica la base.

En Supabase Table Editor se pueden cargar idiomas (name, level) y experiencia (role, company, period, description). No se habilitan políticas públicas: FastAPI usa la conexión de servidor. Nunca agregar la contraseña al frontend ni desactivar RLS para resolver errores.

Para GitHub Actions, copiar el valor después de DATABASE_URL= desde .env.supabase al secreto DATABASE_URL. No copiar el nombre de la variable. Los tests del pipeline siguen usando una base aislada.

Para regresar al PostgreSQL local, usar docker compose up -d --build (sin --env-file y sin -f). Mantener .env de la raíz sin una DATABASE_URL de producción para que se utilice la conexión local.

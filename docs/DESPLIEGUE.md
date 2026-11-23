# Despliegue OCI + Ansible + Supabase + Cloudflare

## Qué está implementado

- dev: pruebas unitarias, integración y E2E.
- main: las mismas pruebas, imágenes web/API para AMD64 y ARM64 etiquetadas con el commit, Terraform, Ansible y comprobación HTTP o HTTPS según la configuración.
- Terraform: VCN, subnet pública, gateway, rutas, reglas 22/80/443, VM Ubuntu con imagen configurable, A1 de 1 OCPU/6 GB/50 GB.
- Ansible: Docker, Compose, Git, Nginx, iptables persistentes; migración inicial de tablas; despliegue con Supabase; certificados Origin; registro DNS de Cloudflare.
- Estado remoto Terraform: backend OCI con bloqueo. El bucket se prepara una vez antes del pipeline.
- Producción usa Supabase externo. Compose local mantiene PostgreSQL para desarrollo y E2E.

Los archivos están preparados; aún no se han aplicado a una cuenta real. Revisar la cuota disponible y la etiqueta Always Free de la imagen/shape en tu región. La capacidad A1 puede no estar disponible y no se cambia automáticamente a una opción de pago.

## Preparación inicial

1. Crear un repositorio GitHub y subir este proyecto con ramas dev y main. Proteger main exigiendo las pruebas.
2. En Docker Hub crear repositorios **públicos** portfolio-api y portfolio-web y un access token con permiso de escritura. Ansible descarga imágenes públicas, sin credenciales Docker Hub en la VM.
3. En OCI crear un bucket **privado con versionado** para el estado. Anotar namespace y bucket. Dar al usuario API permisos sobre los recursos del compartment y lectura/escritura/borrado de objetos en este bucket. Usar el mismo bucket y key en todas las ejecuciones.
4. Seleccionar región, availability domain y OCID de una imagen **Ubuntu 24.04 ARM64** compatible con VM.Standard.A1.Flex. No usar imagen AMD64 con A1.
5. Crear un API key OCI y guardar el archivo privado como secreto GitHub.
6. Crear dos pares de claves ED25519: uno para acceso SSH del runner y otro para identidad SSH del servidor. Por ejemplo `ssh-keygen -t ed25519 -f portfolio_access` y `ssh-keygen -t ed25519 -f portfolio_host`. Para esta automatización se requieren claves sin passphrase, protegidas como secretos GitHub. No subirlas al repositorio.
7. En Supabase obtener la conexión **Session pooler** IPv4 desde Connect. Usar `postgresql+psycopg://USUARIO:CONTRASEÑA_CODIFICADA@HOST:5432/postgres?sslmode=require`. Codificar los caracteres especiales de la contraseña. La cuenta debe poder crear tablas y habilitar RLS; nunca compartir esta conexión con el frontend. La primera migración habilita RLS sin políticas públicas. La cuenta propietaria del backend puede acceder; anon/authenticated no reciben políticas.
8. Configurar variables y secretos en GitHub → Settings → Secrets and variables → Actions. Mantener `DEPLOY_ENABLED` sin definir hasta completar los valores de OCI, Docker Hub, SSH y Supabase.

## Variables GitHub

| Variable | Contenido |
|---|---|
| DEPLOY_ENABLED | `true` para activar publicación/despliegue después de las pruebas |
| DOCKERHUB_USERNAME | Tu usuario Docker Hub |
| OCI_REGION | Región OCI |
| OCI_COMPARTMENT_OCID | Compartment destino |
| OCI_AVAILABILITY_DOMAIN | Nombre completo del availability domain |
| OCI_UBUNTU_IMAGE_OCID | Ubuntu 24.04 ARM64 |
| OCI_STATE_BUCKET | Nombre del bucket privado |
| OCI_NAMESPACE | Namespace Object Storage |
| SSH_PUBLIC_KEY | Contenido de portfolio_access.pub |
| SSH_HOST_PUBLIC_KEY | Contenido de portfolio_host.pub |
| PORTFOLIO_DOMAIN | Opcional. Hostname sin `https://` ni rutas. Dejar sin definir para desplegar por IP. |
| CLOUDFLARE_ZONE_ID | ID de zona. Requerido si se define `PORTFOLIO_DOMAIN`. |

## Secretos GitHub

Para ambos modos se requieren `DOCKERHUB_TOKEN`, `OCI_API_KEY` (PEM completo), `OCI_USER_OCID`, `OCI_TENANCY_OCID`, `OCI_FINGERPRINT`, `SSH_PRIVATE_KEY` (`portfolio_access`), `SSH_HOST_PRIVATE_KEY` (`portfolio_host`) y `DATABASE_URL`.

Si se define `PORTFOLIO_DOMAIN`, también se requieren `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ORIGIN_CERT` y `CLOUDFLARE_ORIGIN_KEY`.

La clave host se configura mediante cloud-init y su pública se fija en known_hosts antes de Ansible. No se desactiva la comprobación de identidad SSH. La clave privada host queda en el estado Terraform y metadata de OCI: restringir el acceso al bucket y a la instancia.

## Ejecución y actualización

Cada push a main ejecuta pruebas. Con DEPLOY_ENABLED=true, construye imágenes y despliega. Terraform aplica cambios sobre la misma infraestructura; prevent_destroy protege la VM de una sustitución accidental. La regla SSH en OCI permite únicamente la IP pública /32 del runner actual. Para acceso manual, un administrador deberá autorizar su IP y reconciliar después el cambio con Terraform.

Para el primer despliegue por IP, deja `PORTFOLIO_DOMAIN` sin crear o vacío. En Actions abre **Publicar en OCI con Ansible → Run workflow**, elige `main` y ejecuta. El workflow comprueba la portada y `/api/health` y muestra el enlace `http://IP_PUBLICA` en el resumen. Usa datos ficticios si pruebas el formulario por HTTP.

Para activar Cloudflare más adelante, agrega un dominio que controles y activa su zona. Configura SSL/TLS **Full (strict)** para el sitio y genera un certificado de origen que incluya el hostname elegido. Guarda su certificado y clave privada, un token limitado a DNS Edit de la zona y el ID de zona. Elige un hostname libre e introduce `PORTFOLIO_DOMAIN` al final. Vuelve a ejecutar el workflow con el mismo bucket y estado de Terraform. Ansible configurará Nginx para HTTPS y actualizará el registro `A` con proxy en Cloudflare.

Ansible recibe secretos desde variables de entorno y usa no_log para las tareas sensibles. Sólo Nginx publica 80/443; los contenedores se alcanzan por 127.0.0.1:8080. Los mensajes tienen límite de tamaño y frecuencia en Nginx.

Para revertir una versión, seleccionar un SHA previamente publicado como IMAGE_TAG y ejecutar el playbook contra la VM. La migración inicial sólo crea tablas faltantes: cambios futuros de columnas requieren migraciones versionadas antes de desplegar. No se promete rollback automático de base de datos.

## VCN / VNC

VCN (red virtual OCI) está implementada. Si el docente exige literalmente VNC (escritorio remoto), falta añadir esa configuración y su autenticación; confirmar el término del enunciado. No se abre ningún puerto de escritorio remoto.

## Validación pendiente

Los archivos no sustituyen una ejecución real. Faltan credenciales para validar Terraform contra OCI, conectar Supabase y comprobar el dominio. La máquina local del asistente no tiene permiso para controlar Docker Desktop. Ejecutar el workflow y revisar sus logs antes de considerar el despliegue completo.

Referencias: https://developer.hashicorp.com/terraform/language/backend/oci y https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

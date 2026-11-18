"""Genera archivos privados desde variables del runner; nunca imprime credenciales."""
import json
import os
from pathlib import Path
import urllib.request

def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise SystemExit(f'Falta configurar {name}')
    return value

def write(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    path.chmod(0o600)

for name in ['DATABASE_URL', 'DOCKERHUB_USERNAME', 'PORTFOLIO_DOMAIN',
             'CLOUDFLARE_ZONE_ID', 'CLOUDFLARE_API_TOKEN',
             'CLOUDFLARE_ORIGIN_CERT', 'CLOUDFLARE_ORIGIN_KEY']:
    required(name)
database_url = required('DATABASE_URL')
if not database_url.startswith('postgresql+psycopg://') or any(c in database_url for c in "\n\r'"):
    raise SystemExit('DATABASE_URL requiere postgresql+psycopg y caracteres de contraseña codificados para URL.')
oci = Path.home() / '.oci'
write(oci / 'key.pem', required('OCI_API_KEY'))
write(oci / 'config', '\n'.join([
    '[DEFAULT]',
    'user=' + required('OCI_USER_OCID'),
    'tenancy=' + required('OCI_TENANCY_OCID'),
    'fingerprint=' + required('OCI_FINGERPRINT'),
    'region=' + required('OCI_REGION'),
    'key_file=' + str(oci / 'key.pem'),
]))
write(Path.home() / '.ssh' / 'portfolio', required('SSH_PRIVATE_KEY') + '\n')
with urllib.request.urlopen('https://api.ipify.org', timeout=20) as response:
    import ipaddress
    ip = str(ipaddress.IPv4Address(response.read().decode().strip()))
values = {
    'region': required('OCI_REGION'),
    'compartment_id': required('OCI_COMPARTMENT_OCID'),
    'availability_domain': required('OCI_AVAILABILITY_DOMAIN'),
    'ubuntu_image_id': required('OCI_UBUNTU_IMAGE_OCID'),
    'ssh_public_key': required('SSH_PUBLIC_KEY'),
    'ssh_host_private_key': required('SSH_HOST_PRIVATE_KEY'),
    'ssh_host_public_key': required('SSH_HOST_PUBLIC_KEY'),
    'ssh_cidr': ip + '/32',
}
write('infra/terraform/ci.auto.tfvars.json', json.dumps(values))
write('infra/terraform/backend.hcl', '\n'.join([
    'bucket = ' + json.dumps(required('OCI_STATE_BUCKET')),
    'namespace = ' + json.dumps(required('OCI_NAMESPACE')),
    'region = ' + json.dumps(required('OCI_REGION')),
    'key = "portfolio/production.tfstate"',
]))

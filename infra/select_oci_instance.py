"""Selecciona una VM flexible de 1 OCPU y 2 GB para el despliegue en OCI."""

import json
import os
from pathlib import Path
import re
import subprocess

import oci


TERRAFORM_DIR = Path(__file__).resolve().parent / 'terraform'
INSTANCE_ADDRESS = 'oci_core_instance.web'
TRIAL_SHAPES = ('VM.Standard.E4.Flex', 'VM.Standard.E5.Flex', 'VM.Standard3.Flex')
UBUNTU_AMD64 = re.compile(r'^Canonical-Ubuntu-24\.04-\d{4}\.\d{2}\.\d{2}-\d+$')


def current_instance(compute):
    # El estado contiene datos sensibles. Capturar JSON sin escribirlo en el log.
    output = subprocess.check_output(
        ['terraform', f'-chdir={TERRAFORM_DIR}', 'show', '-json'], encoding='utf-8',
    )
    resources = json.loads(output).get('values', {}).get('root_module', {}).get('resources', [])
    for resource in resources:
        if resource['address'] == INSTANCE_ADDRESS:
            values = resource['values']
            instance = compute.get_instance(values['id']).data
            if instance.lifecycle_state == 'TERMINATING':
                raise SystemExit('La VM anterior sigue terminando. Espera el estado TERMINATED antes de desplegar.')
            if instance.lifecycle_state == 'TERMINATED':
                print('La VM anterior está terminada. Se seleccionará capacidad para una nueva.')
                return None
            return values['shape'], values['source_details'][0]['source_id']
    return None


def select_trial_instance(compute, tenancy_id, settings):
    models = oci.core.models
    availability_domain = settings['availability_domain']
    offered_shapes = oci.pagination.list_call_get_all_results(
        compute.list_shapes, settings['compartment_id'], availability_domain=availability_domain,
    ).data
    offered_names = {shape.shape for shape in offered_shapes}
    candidates = [shape for shape in TRIAL_SHAPES if shape in offered_names]
    if not candidates:
        raise SystemExit(f'OCI no ofrece las formas de prueba configuradas en {availability_domain}.')

    report = compute.create_compute_capacity_report(models.CreateComputeCapacityReportDetails(
        compartment_id=tenancy_id,
        availability_domain=availability_domain,
        shape_availabilities=[
            models.CreateCapacityReportShapeAvailabilityDetails(
                instance_shape=shape,
                instance_shape_config=models.CapacityReportInstanceShapeConfig(ocpus=1, memory_in_gbs=2),
            )
            for shape in candidates
        ],
    )).data
    available = set()
    for entry in report.shape_availabilities:
        print(f'{entry.instance_shape}: {entry.availability_status}')
        if entry.availability_status == 'AVAILABLE' and entry.available_count != 0:
            available.add(entry.instance_shape)

    for shape in candidates:
        if shape not in available:
            continue
        images = oci.pagination.list_call_get_all_results(
            compute.list_images,
            settings['compartment_id'],
            operating_system='Canonical Ubuntu',
            operating_system_version='24.04',
            shape=shape,
            lifecycle_state='AVAILABLE',
            sort_by='TIMECREATED',
            sort_order='DESC',
        ).data
        for image in images:
            if UBUNTU_AMD64.fullmatch(image.display_name):
                return shape, image.id
        print(f'{shape}: sin imagen oficial Ubuntu 24.04 AMD64 en la lista regional.')

    raise SystemExit('OCI no reportó una VM de prueba disponible con Ubuntu 24.04 AMD64.')


def main():
    profile = os.environ.get('OCI_COMPUTE_PROFILE', 'trial')
    if profile not in {'trial', 'always-free'}:
        raise SystemExit('OCI_COMPUTE_PROFILE debe ser trial o always-free.')

    path = TERRAFORM_DIR / 'ci.auto.tfvars.json'
    settings = json.loads(path.read_text(encoding='utf-8'))
    config = oci.config.from_file()
    compute = oci.core.ComputeClient(config, timeout=(10, 30))
    try:
        instance = current_instance(compute)
        if instance:
            print(f'Reutilizando VM administrada en Terraform ({instance[0]}).')
        elif profile == 'always-free':
            print('Configuración Always Free: VM.Standard.A1.Flex.')
            return
        else:
            instance = select_trial_instance(compute, config['tenancy'], settings)
            print(f'VM seleccionada: {instance[0]} (1 OCPU, 2 GB, Ubuntu 24.04 AMD64).')
    except oci.exceptions.ServiceError as error:
        raise SystemExit(
            f'OCI rechazó la consulta de Compute: HTTP {error.status} {error.code} '
            f'({error.operation_name}). Request ID: {error.request_id}'
        ) from None

    settings['instance_shape'], settings['ubuntu_image_id'] = instance
    path.write_text(json.dumps(settings), encoding='utf-8')


if __name__ == '__main__':
    main()

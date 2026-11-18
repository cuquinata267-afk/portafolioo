terraform {
  required_version = ">= 1.12.0"
  backend "oci" {}
  required_providers {
    oci = {
      source = "oracle/oci"
      version = "~> 7.0"
    }
  }
}
provider "oci" { region = var.region }
variable "region" { type = string }
variable "compartment_id" { type = string }
variable "availability_domain" { type = string }
variable "ubuntu_image_id" {
  type = string
  description = "OCID de imagen Ubuntu 24.04 ARM64 compatible con A1 en tu región."
}
variable "ssh_public_key" { type = string }
variable "ssh_host_private_key" {
  type = string
  sensitive = true
}
variable "ssh_host_public_key" { type = string }
variable "ssh_cidr" {
  type = string
  description = "IP pública /32 del runner que ejecutará Ansible."
  validation {
    condition = can(cidrhost(var.ssh_cidr, 0)) && endswith(var.ssh_cidr, "/32")
    error_message = "Usar una sola IPv4 con prefijo /32 para SSH."
  }
}
resource "oci_core_vcn" "portfolio" {
  compartment_id = var.compartment_id
  cidr_block = "10.20.0.0/16"
  display_name = "portfolio-vcn"
  dns_label = "portfolio"
}
resource "oci_core_internet_gateway" "web" {
  compartment_id = var.compartment_id
  vcn_id = oci_core_vcn.portfolio.id
  enabled = true
}
resource "oci_core_route_table" "web" {
  compartment_id = var.compartment_id
  vcn_id = oci_core_vcn.portfolio.id
  route_rules {
    network_entity_id = oci_core_internet_gateway.web.id
    destination = "0.0.0.0/0"
  }
}
resource "oci_core_security_list" "web" {
  compartment_id = var.compartment_id
  vcn_id = oci_core_vcn.portfolio.id
  egress_security_rules {
    destination = "0.0.0.0/0"
    protocol = "all"
  }
  dynamic "ingress_security_rules" {
    for_each = { "22" = var.ssh_cidr, "80" = "0.0.0.0/0", "443" = "0.0.0.0/0" }
    content {
      protocol = "6"
      source = ingress_security_rules.value
      tcp_options {
        min = tonumber(ingress_security_rules.key)
        max = tonumber(ingress_security_rules.key)
      }
    }
  }
}
resource "oci_core_subnet" "web" {
  compartment_id = var.compartment_id
  vcn_id = oci_core_vcn.portfolio.id
  cidr_block = "10.20.1.0/24"
  route_table_id = oci_core_route_table.web.id
  security_list_ids = [oci_core_security_list.web.id]
  dns_label = "web"
}
resource "oci_core_instance" "web" {
  compartment_id = var.compartment_id
  availability_domain = var.availability_domain
  display_name = "natalia-portfolio"
  shape = "VM.Standard.A1.Flex"
  shape_config {
    ocpus = 1
    memory_in_gbs = 6
  }
  source_details {
    source_type = "image"
    source_id = var.ubuntu_image_id
    boot_volume_size_in_gbs = 50
  }
  create_vnic_details {
    subnet_id = oci_core_subnet.web.id
    assign_public_ip = true
  }
  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(join("\n", ["#cloud-config", yamlencode({
      ssh_keys = {
        ed25519_private = var.ssh_host_private_key
        ed25519_public = var.ssh_host_public_key
      }
    })]))
  }
  lifecycle { prevent_destroy = true }
}
output "public_ip" { value = oci_core_instance.web.public_ip }

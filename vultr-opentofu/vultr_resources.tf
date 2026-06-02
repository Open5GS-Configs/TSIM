resource "vultr_instance" "vplmn" {
    label = var.V_HOSTNAME
    hostname = var.V_HOSTNAME
    plan = var.vultr_plan_id
    region = var.h_region
    os_id = "2284"
    enable_ipv6 = false
    vpc_ids = [vultr_vpc.sepp-link.id]
    ssh_key_ids = [vultr_ssh_key.user_ssh_key.id, vultr_ssh_key.ansible_ssh_key.id]
}

resource "vultr_instance" "hplmn" {
    label = var.H_HOSTNAME
    hostname = var.H_HOSTNAME
    plan = var.vultr_plan_id
    region = var.v_region
    os_id = "2284"
    enable_ipv6 = false
    vpc_ids = [vultr_vpc.sepp-link.id]
    ssh_key_ids = [vultr_ssh_key.user_ssh_key.id, vultr_ssh_key.ansible_ssh_key.id]
}

variable "vultr_plan_id" {}
variable "H_HOSTNAME" {}
variable "h_region" {}
variable "V_HOSTNAME" {}
variable "v_region" {}


resource "vultr_vpc" "sepp-link" {
	description = "sepp-link-test"
	region = var.vpc_region
}

variable "vpc_region" {}


resource "vultr_ssh_key" "user_ssh_key" {
  name = "ssh_key"
  ssh_key = var.user_ssh_key
}

variable "user_ssh_key" {}


resource "vultr_ssh_key" "ansible_ssh_key" {
  name = "ansible_ssh_key"
  ssh_key = var.ansible_ssh_key
}

variable "ansible_ssh_key" {}


output "vplm_ip" {
  value = vultr_instance.vplmn.main_ip
}


output "hplm_ip" {
  value = vultr_instance.hplmn.main_ip
}
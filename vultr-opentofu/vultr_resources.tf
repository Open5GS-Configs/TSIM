resource "vultr_instance" "vplmn" {
    label = var.H_HOSTNAME
    hostname = var.H_HOSTNAME
    plan = var.VULTR_PLAN_ID
    region = var.H_REGION
    os_id = "2284"
    enable_ipv6 = false
    vpc_ids = [vultr_vpc.sepp-link.id]
    ssh_key_ids = [vultr_ssh_key.user_ssh_key.id, vultr_ssh_key.ansible_ssh_key.id]
}

resource "vultr_instance" "hplmn" {
    label = var.V_HOSTNAME
    hostname = var.V_HOSTNAME
    plan = var.VULTR_PLAN_ID
    region = var.V_REGION
    os_id = "2284"
    enable_ipv6 = false
    vpc_ids = [vultr_vpc.sepp-link.id]
    ssh_key_ids = [vultr_ssh_key.user_ssh_key.id, vultr_ssh_key.ansible_ssh_key.id]
}

variable "VULTR_PLAN_ID" {}
variable "H_HOSTNAME" {}
variable "H_REGION" {}
variable "V_HOSTNAME" {}
variable "V_REGION" {}


resource "vultr_vpc" "sepp-link" {
	description = "sepp-link-test"
	region = var.VPC_REGION
}

variable "VPC_REGION" {}


resource "vultr_ssh_key" "user_ssh_key" {
  name = "ssh_key"
  ssh_key = var.USER_SSH_KEY
}

variable "USER_SSH_KEY" {}


resource "vultr_ssh_key" "ansible_ssh_key" {
  name = "ansible_ssh_key"
  ssh_key = var.ANSIBLE_SSH_KEY
}

variable "ANSIBLE_SSH_KEY" {}
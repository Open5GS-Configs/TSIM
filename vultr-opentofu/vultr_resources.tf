locals {
  create_user_ssh_key = var.user_ssh_key != ""

  ssh_key_ids = concat(
    [vultr_ssh_key.ansible_ssh_key.id],
    local.create_user_ssh_key ? [vultr_ssh_key.user_ssh_key[0].id] : []
  )
}


resource "vultr_instance" "box" {
  for_each = var.boxes

  plan = var.vultr_plan_id
  os_id = "2284"
  enable_ipv6 = false

  vpc_ids = [
    for vpc_name in each.value["vpcs"]:
    vultr_vpc.vpc-link[vpc_name].id
  ]
  
  ssh_key_ids = local.ssh_key_ids

  label = each.value["hostname"]
  hostname = each.value["hostname"]
  region = each.value["region"]
}

variable "boxes" {}
variable "vultr_plan_id" {}

resource "vultr_vpc" "vpc-link" {
  for_each = var.descriptions
  description = each.value

	region = var.vpc_region
  v4_subnet  = var.vpc_v4_subnet
	v4_subnet_mask = var.vpc_v4_subnet_mask
}

variable "descriptions" {}
variable "vpc_region" {}
variable "vpc_v4_subnet_mask" {}
variable "vpc_v4_subnet" {}


resource "vultr_ssh_key" "user_ssh_key" {
  count = local.create_user_ssh_key ? 1 : 0
  name = "ssh_key"
  ssh_key = var.user_ssh_key
}

variable "user_ssh_key" {}


resource "vultr_ssh_key" "ansible_ssh_key" {
  name = "ansible_ssh_key"
  ssh_key = var.ansible_ssh_key
}

variable "ansible_ssh_key" {}

output "instance_ips" {
  value = {
    for name, instance in vultr_instance.box :
    name => instance.main_ip
  }
}
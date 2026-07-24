locals {
  create_user_ssh_key = var.user_ssh_key != ""

  ssh_key_ids = concat(
    [vultr_ssh_key.ansible_ssh_key.id],
    local.create_user_ssh_key ? [vultr_ssh_key.user_ssh_key[0].id] : []
  )
}


resource "vultr_instance" "box" {
  for_each = var.boxes

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
  plan = each.value["plan_id"]
}

variable "boxes" {}

resource "vultr_vpc" "vpc-link" {
  for_each = var.peerings
  
  description = each.value["description"]

	region = each.value["region"]
  v4_subnet  = each.value["v4_subnet"]
	v4_subnet_mask = each.value["v4_subnet_mask"]
}

variable "peerings" {}

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

# TOPSSIM Environment Setup

The purpose of this project is to create a reproducible environment for testing 5G core performance within the TOPSSIM project. It uses a number of tools to automate the creation and configuration of virtual machines used for testing. Currently, it creates two VMs, one per PLMN. This could be extended to create a VM per component, connecting each VM through a private network and running only its particular function in the future. 

This project uses:
  - A Python script for parsing arguments and connecting different tools together
  - [OpenTofu](https://opentofu.org/docs/intro/install/deb/#step-by-step-instructions) to create and initially configure cloud VMs (provided by Vultr)
  - [Vagrant](https://developer.hashicorp.com/vagrant/install#linux) to create and configure local VMs (provided by VirtualBox and VMWare)
  - [Ansible](https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html#installing-and-upgrading-ansible-with-pip) to install dependencies, bring Open5GS configurations, and run tests

### Config 
It requires a .yaml config file to store the required parameters for execution. This is a sample of a config file:
```
---

OGS: "abc"
USER_SSH_KEY: "your ssh key"

H-IP: "10.10.0.1"
V-IP: "10.10.0.2"

PROVIDER: "Vultr"

H-REGION: "yto"
V-REGION: "yto"
VPC-REGION: "yto"
VULTR_API_KEY: "your api key"
VULTR_PLAN_ID: "vc2-1c-1gb"
```

### Running the program
You can call it using:
`python3 topssim_setup.py  /directory/your_config_file.yaml`

You can check other command-line options with `python3 topssim_setup.py -h`.


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

ogs_repo: "abc"
hplmn_config_repo: "def"
vplmn_config_repo: "ghi"
vplmn_hosts_path: /etc/hosts
hplmn_hosts_path: /etc/hosts

user_ssh_key: "your ssh key"

h_ip: "10.10.0.1"
v_ip: "10.10.0.2"

provider: "Vultr"

h_region: "yto"
v_region: "yto"
vpc_region: "yto"
vultr_api_key: "your api key"
vultr_plan_id: "vc2-1c-1gb"
```

### Running the program
You can call it using:
`python3 topssim_setup.py  -c /directory/your_config_file.yaml`

You can check other command-line options with `python3 topssim_setup.py -h`.

### Troubleshooting

1. If any issues are present with OpenTofu this is good to keep in mind:

- If a resource has been deleted manually, OpenTofu will not recognize the change. It must be manually deleted from its instances. 
This shows the states that are being tracked: `tofu state list`
If the instance deleted is still there, you can remove it with: `tofu state rm vultr_vpc.sepp-link` (instead of `vultr_vpc.sepp-link` insert your instance's address).

2. Ansible:

- To add a SSH key passphrase to be recognized by Ansible when creating the SSH connection to the hosts:
Start SSH Agent:
`eval "$(ssh-agent -s)"`
And add private key:
`ssh-add ~/.ssh/id_rsa`

# TOPSSIM Environment Setup

The purpose of this project is to create a reproducible environment for testing 5G core performance within the TOPSSIM project. It uses a number of tools to automate the creation and configuration of virtual machines used for testing. Currently, it creates two VMs, one per PLMN. This could be extended to create a VM per component, connecting each VM through a private network and running only its particular function in the future. 

This project uses:
  - A Python script for parsing arguments and connecting different tools together
  - [OpenTofu](https://opentofu.org/docs/intro/install/deb/#step-by-step-instructions) to create and initially configure cloud VMs (provided by Vultr)
  - [Vagrant](https://developer.hashicorp.com/vagrant/install#linux) to create and configure local VMs (provided by VirtualBox and VMWare)
  - [Ansible](https://docs.ansible.com/projects/ansible/latest/installation_guide/intro_installation.html#installing-and-upgrading-ansible-with-pip) to install dependencies, bring Open5GS configurations, and run tests


It clones and builds an Open5GS repo into /root/open5gs/ and copies the specified config files into /root/open5gs/install/etc/open5gs/ (the config files need to take this into account for pathing).

<img src="/img/diagram.png" width="75%">

### Config 
It requires a .yaml config file to store the required parameters for execution. This is a sample of a config file:

```
---

ogs_repo: "<Open5GS repo>"
ogs_version: main
hplmn_config_repo: “<HPLMN Config repo>”
vplmn_config_repo: “<VPLMN Config repo>”
vplmn_hosts_path: “<Path to Hosts used in VPLMN>”
hplmn_hosts_path: “<Path to Hosts used in HPLMN>”
create_services: true

user_ssh_key: "<SSH key of the user>"

hplmn_test_command: ./misc/db/open5gs-dbctl add "999700000021309" "465B5CE8 B199B49F AA5F0A2E E238A6BC" "E8ED289D EBA952E4 283B54E8 8E6183CA"
vplmn_test_command: ./build/tests/registration/registration -c /root/open5gs/build/configs/examples/gnb-001-01-ue-999-70.yaml simple-test

hplmn_ip: "10.10.0.3"
vplmn_ip: "10.10.0.4"
vpc_v4_subnet: "10.10.0.0"
vpc_v4_subnet_mask: "28"

provider: "Vultr"

h_region: "yto"
v_region: "yto"
vpc_region: "yto"
vultr_plan_id: "vc2-2c-2gb"

```

The API key for Vultr should be provided as an environment variable with:
`export VULTR_API_KEY=<your API key>`


### Running the program
You can call it using:
`python3 topssim_setup.py  -c /directory/your_config_file.yaml`

You can check other command-line options with `python3 topssim_setup.py -h`.

Some examples are:
To run just the configuration and testing stages of Ansible on already existing machines:
`python3 topssim_setup.py -c /home/agustin/5G_Setup/config.yaml -ansible --ansible_tags "config_stage testing_stage"`

It is also useful to know that both OpenTofu and Ansible provide CLI tools. These can be used to isolate a part of the process. Some notable commands are:

1. OpenTofu:   
`tofu show`    
`tofu state list`    
`tofu state show vultr_vpc.sepp-link` (the address of the instances lives in _vultr-opentofu/vultr_resources.tf_)   

2. Ansible:    
`ansible all -m ping ` to test connectivity    
`ansible-playbook topssim_setup.yaml` to run the playbook   
`ansible-inventory --list-hosts` to see the hosts    
`ansible-galaxy role list` to see the installed roles    

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

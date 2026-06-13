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
It requires a .yaml config file to store the required parameters for execution. Options differ between providers. This is a sample of a config file:

```
---
ogs:
  - repo: "<Open5GS repo>"
  - version: <the git version used when cloning the repo>

hplmn:
  - config_repo: <HPLMN Config repo> 
  - hosts_path: <Path to Hosts used in HPLMN>
  - test_script: <Path to your test script>
  - private_ip: "<IP for private network>"
  - region: "<region for HPLMN>"


vplmn:
  - config_repo: <VPLMN Config repo> 
  - hosts_path: <Path to Hosts used in VPLMN>
  - test_script: <Path to your test script>
  - private_ip: "<IP for private network>"
  - region: "<region for VPLMN>"

vultr:
  - vpc:
    - v4_subnet: "<subnet for private network>"
    - v4_subnet_mask: "<subnet mask for private network>"
    - region: "<region for private network>"
  - plan_id: "<plan used for machines>"

vagrant:
  ram: <RAM to be allocated to each VM (in MB)>
  cpu: <CPU cores to be allocated to each VM>
  disk: <Disk size of each VM (in GB)>

create_services: <(true or false) creates service files in /etc/systemd/system and enables all components to run at boot>
user_ssh_key: "<SSH key of the user>"
provider: "<your VM provider>"
```

### Running the program
You can call it using:
`python3 topssim_setup.py  -c /directory/your_config_file.yaml`

You can check other command-line options with `python3 topssim_setup.py -h`.

Some examples are:
To run just the configuration and testing stages of Ansible on already existing machines:
`python3 topssim_setup.py -c /home/agustin/5G_Setup/config.yaml -ansible --ansible_tags "config_stage testing_stage"`

It is also useful to know that both OpenTofu and Ansible provide CLI tools. These can be used to isolate a part of the process. Some notable commands are:

1. Ansible:    
`ansible all -m ping ` to test connectivity    
`ansible-playbook topssim_setup.yaml` to run the playbook   
`ansible-inventory --list-hosts` to see the hosts    
`ansible-galaxy role list` to see the installed roles  

2. OpenTofu:   
`tofu show`    
`tofu state list`    
`tofu state show vultr_vpc.sepp-link` (the address of the instances lives in _vultr-opentofu/vultr_resources.tf_)   

  

### Troubleshooting

1. Ansible:      

- To add a SSH key passphrase to be recognized by Ansible when creating the SSH connection to the hosts:    
Start SSH Agent:     
`eval "$(ssh-agent -s)"`     
And add private key:     
`ssh-add ~/.ssh/id_rsa`     

2. If any issues are present with OpenTofu this is good to keep in mind:     

- If a resource has been deleted manually, OpenTofu will not recognize the change. It must be manually deleted from its instances.     
This shows the states that are being tracked: `tofu state list`      
If the instance deleted is still there, you can remove it with: `tofu state rm vultr_vpc.sepp-link` (instead of `vultr_vpc.sepp-link` insert your instance's address).     


#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

until sudo apt update; do
    sleep 10
done

sudo apt install -y python3 python3-debian
#systemctl --force --force reboot

#!/bin/bash
# prepare repositories
sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu xenial stable"

if [ ! -f "/etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-xenial.list" ]; then
    sudo add-apt-repository ppa:deadsnakes/ppa
fi

# install packages
sudo apt-get update -y
sudo apt-get -y install docker-ce docker-ce-cli python3-pip python3.9-dev python3.9-venv python3.9-distutils libssl-dev libtool libldap2-dev libssl-dev libsasl2-dev libmysqlclient-dev libcurl4-openssl-dev
python3.9 -m ensurepip

# prepare venv
cd ~/
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r vaas/vaas-app/requirements/dev.txt
echo ". venv/bin/activate" >> ~/.bash_profile

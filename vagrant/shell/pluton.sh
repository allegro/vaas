#!/bin/bash
# prepare repositories
sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-xenial main" | sudo tee /etc/apt/sources.list.d/docker.list

# install packages
sudo apt-get update -y
sudo apt-get -y install docker-engine python-virtualenv python3-pip python3.5
sudo pip install virtualenv

# prepare venv
cd ~/
virtualenv -p /usr/bin/python3.5 venv
source venv/bin/activate
pip install -r vaas/vaas-app/requirements/dev.txt
echo ". venv/bin/activate" >> ~/.bash_profile

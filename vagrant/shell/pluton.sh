#!/bin/bash
# prepare repositories
sudo apt-get update -y
sudo apt-get install -y apt-transport-https ca-certificates
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | sudo tee /etc/apt/sources.list.d/docker.list

# install packages
sudo apt-get update -y
sudo apt-get -y install docker-engine python-virtualenv python-pip
sudo pip install virtualenv

# prepare venv
cd ~/
virtualenv venv
source venv/bin/activate
pip install -r vaas/vaas-app/requirements/test.txt
echo ". venv/bin/activate" >> ~/.bash_profile

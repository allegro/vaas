# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.ssh.username = 'ubuntu'

  config.vm.define "vaas", primary: true do |vaas|

    vaas.vm.box_url = "https://storage.googleapis.com/allegro-vaas-public/vaas_dev_v0.09.box"
    vaas.vm.box = "vaas_dev_v0.09.box"
    vaas.vm.synced_folder ".", "/home/ubuntu/vaas"
    vaas.vm.provision :shell, :privileged => false, run: "always", :path => "vagrant/shell/vaas.sh"
    vaas.vm.network "private_network", ip: "192.168.200.11"

  end

  config.vm.define "pluton", autostart: false do |pluton|

    pluton.vm.box = "ubuntu/xenial64"
    pluton.vm.synced_folder ".", "/home/ubuntu/vaas"
    pluton.vm.provision :shell, :privileged => false, :path => "vagrant/shell/pluton.sh"
    pluton.vm.provision :shell, :privileged => false, run: "always", :path => "vagrant/shell/vaas.sh"

  end

  config.vm.host_name = "vaas.dev"

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end

  config.vm.network "forwarded_port", guest: 3030, host: 3030

end

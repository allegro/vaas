# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "vaas", primary: true do |vaas|

    vaas.vm.box_url = "http://box.allegro.tech/vaas_dev_v0.06.box"
    vaas.vm.box = "vaas_dev_v0.06.box"

    vaas.vm.synced_folder ".", "/home/vagrant/vaas"

    vaas.vm.provision :shell, :privileged => false, run: "always", :path => "vagrant/shell/vaas.sh"

  end

  config.vm.define "pluton", autostart: false do |pluton|

    pluton.vm.box = "ubuntu/trusty64"

    pluton.vm.synced_folder ".", "/home/vagrant/vaas"
    pluton.vm.synced_folder "vagrant/puppet/files", "/etc/puppet/files"

    pluton.vm.provision :shell, :path => "vagrant/shell/pluton.sh"

    pluton.vm.provision :puppet, run: "always" do |puppet|
      puppet.manifests_path = "vagrant/puppet/manifests"
      puppet.manifest_file  = "default.pp"
      puppet.options = "--parser future --fileserverconfig=/home/vagrant/vaas/vagrant/puppet/fileserver.conf"
      puppet.hiera_config_path = "vagrant/puppet/hiera.yaml"
    end

  end

  config.vm.host_name = "vaas.dev"

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end

  config.vm.network "private_network", ip: "192.168.200.10"
  config.vm.network "private_network", ip: "192.168.200.11"
  config.vm.network "private_network", ip: "192.168.200.12"
  config.vm.network "private_network", ip: "192.168.200.13"
  config.vm.network "private_network", ip: "192.168.200.14"
  config.vm.network "private_network", ip: "192.168.200.15"

  config.vm.network "forwarded_port", guest: 80, host: 80
  config.vm.network "forwarded_port", guest: 3030, host: 3030

end

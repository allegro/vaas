# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "vaas", primary: true do |vaas|

    vaas.vm.box_url = "http://box.allegro.tech/vaas_dev_v0.08.box"
    vaas.vm.box = "vaas_dev_v0.08.box"
    vaas.vm.synced_folder ".", "/home/vagrant/vaas"
    vaas.vm.provision :shell, :privileged => false, run: "always", :path => "vagrant/shell/vaas.sh"

  end

  config.vm.define "pluton", autostart: false do |pluton|

    pluton.vm.box = "ubuntu/trusty64"
    pluton.vm.synced_folder ".", "/home/vagrant/vaas"
    pluton.vm.provision :shell, :privileged => false, :path => "vagrant/shell/pluton.sh"
    pluton.vm.provision :shell, :privileged => false, run: "always", :path => "vagrant/shell/vaas.sh"

  end

  config.vm.host_name = "vaas.dev"

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end

  config.vm.network "forwarded_port", guest: 3030, host: 3030

end

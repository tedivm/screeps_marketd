# -*- mode: ruby -*-
# vi: set ft=ruby :


Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/wily64"

  config.vm.network "private_network", ip: "172.16.0.3"
  config.vm.provision "shell", path: "provisioning/vagrant.sh"

  config.vm.provider "virtualbox" do |v|
    v.memory = 2048
  end

end

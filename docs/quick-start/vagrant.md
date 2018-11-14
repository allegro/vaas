VaaS in Vagrant
===============
VaaS in Vagrant is a preconfigured VaaS application instance packed into a Vagrant box. It is useful for experimentation, testing and development purposes. The box runs the following services:

* VaaS application
* Varnish v3 instance in a docker container
* Varnish v4 instance in a docker container
* Several Nginx instances each in a separate docker container

Download and run
----------------
VaaS in Vagrant requires Virtual Box, Vagrant and Git to be installed on your machine. You can then run VaaS in Vagrant as follows:

    git clone https://github.com/allegro/vaas.git
    cd vaas
    vagrant up

This will spawn a Virtual Box machine and mount the VaaS repo as a local file system within the machine. You can use this environment to familiarize yourself with VaaS as well as to modify and develop VaaS code.

Log in to VaaS
--------------
Point your browser to <http://localhost:3030/> and log in using the following credentials:

    User: admin
    Password: admin

You will see a django admin GUI with two apps: Cluster and Manager. Configure your sample Varnish servers and VCL templates in Cluster app. Configure your backends, directors and probes in the Manager app. Refer to [GUI](../documentation/gui.md) or [API](../documentation/api.md) documentation to see how to do this.

Current VCL for the test Varnish instances can be previewed by clicking on Cluster -> Varnish servers -> Show vcl. HINT: Freshly after booting up VaaS in Vagrant, the configuration of the Varnish servers will not be loaded. Make some changes to the test backends or re-enable the test Varnish instances to trigger loading of the configuration.

Entering the VaaS box
---------------------
You can access the Vagrant box and make modifications as you require (eg. to run more Varnish or backend instances):

    vagrant ssh

The box by default has several IP interfaces preconfigured for testing. The IP addresses are:

    192.168.200.10
    192.168.200.11
    192.168.200.12
    192.168.200.13
    192.168.200.14
    192.168.200.15

Spawn more Varnish instances
----------------------------
You can easily spawn more Varnish instances (as many as your VM's resources will allow) as follows:

    # IP_address - one of the addresses mentioned above
    # IP_port - a TCP port
    # NUMBER - a number to distinguish this instance from other instances
    # IP_address_management - management address
    # IP_port_management - TCP management port
    # Varnish 3
    docker run -d -t -m 104857600b p <IP_address>:<IP_port>:6081 \
        -p <IP_address_management>:<IP_port_management>:6082 \
        --name varnish-3-<NUMBER> allegro/vaas-varnish-3
    # Varnish 4
    docker run -d -t -m 104857600b p <IP_address>:<IP_port>:6081 \
        -p <IP_address_management>:<IP_port_management>:6082 \
        --name varnish-4-<NUMBER> allegro/vaas-varnish-3

You will then need to add the new Varnish instances to your Cluster.

Spawn more Nginx instances
--------------------------
Similarly to new Varnish instances, you can also spawn new Nginx instances:

    # IP_address - one of the addresses mentioned above
    # IP_port - a TCP port
    # NUMBER - a number to distinguish this instance from other instances
    docker run -d -t -m 26214400b -p <IP_address>:<IP_port>:80 \
        -v /srv/www/first:/usr/share/nginx/html/first \
        -v /srv/www/second:/usr/share/nginx/html/second \
        --name nginx-<NUMBER> allegro/vaas-nginx

You will need to configure the new Nginx instance in Manager app.

VaaS cron jobs
--------------
Remember how we wrote that VaaS does not use an agent? That was a lie. VaaS uses old good cron as an agent to perform two simple tasks. We recommend using a configuration management system to configure these jobs on appropriate servers.

### Saving backend status to the database
Assuming you followed our quick-start instruction on [running VaaS in production](../quick-start/production.md), this cron job should run on VaaS application server:

    0-58/2 * * * * /home/ubuntu/prod-env/bin/backend_statuses

### Generating a startup VCL
On each Varnish server controlled by VaaS, run the following job to save running VCL so that it is available immediately after Varnish restarts:

    */5 * * * * bash -c "source /usr/local/bin/vcl_save.sh && save_vcl && put_vcl_in_place

Aditionally, you may want to keep a backup of the last known good configuration - in case of an emergency:

    * */6 * * * bash -c "source /usr/local/bin/vcl_save.sh && rotate_vcls"

Here's what /usr/local/bin/vcl_save.sh could look like:

    #!/bin/bash
    
    save_vcl () {
      if [ $(pgrep varnishd > /dev/null ; echo $?) -eq 0 ] ; then
        varnishadm vcl.show $(varnishadm vcl.list | grep active | egrep -o '[^ ]*$') > /etc/varnish/default.vcl_tmp
      fi
    }
    
    put_vcl_in_place () {
      if [ $(stat --printf="%s" /etc/varnish/default.vcl_tmp) -gt 0 ]; then
        mv /etc/varnish/default.vcl_tmp /etc/varnish/default.vcl
      fi
    }
    
    rotate_vcls () {
      cp /etc/varnish/default.vcl-6h /etc/varnish/default.vcl-12h
      cp /etc/varnish/default.vcl /etc/varnish/default.vcl-6h
    }


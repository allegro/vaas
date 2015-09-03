VaaS - Varnish as a Service
===========================
VaaS enables you to manage cluster(s) of Varnish servers from one place, via a web GUI or a REST API. Information about your Varnish servers and their backends, directors and probes is saved into a database. It is then used to automatically generate and distribute VCLs.

How it works
------------
By default, VaaS generates a very basic VCL using data from the database and sends it to Varnish servers in a matter of seconds, using native Varnish API (no agent required). If you require a more complex VCL, you can overwrite sections of the default VCL or create your own template intermingling ordinary VCL with mark ups. These mark ups tell VaaS where in the VCL to generate backends and directors or where to generate hints telling Varnish how to route traffic. You can wrap backend hints with complex rules to suit your needs.

What it offers
--------------
There are many benefits from using VaaS, including:

* Backend and Director deffinitions as well as VCL templates are kept in a database. No more VCS repos.
* Teams responsible for services can manage their directors and backends directly.
* VaaS prevents typos in VCLs as they are generated automatically.
* VaaS uses Varnish API, there is no need for a configuration agent on each Varnish server.
* VaaS free to use subject to Apache Version 2.0 License.

Try it
------
You can easily set up a sample VaaS instance with two test Varnish servers and several test backends using [VaaS in Vagrant](quick-start/vagrant.md). You might also like to check out [VaaS in Docker](quick-start/docker.md).

Release notes
-------------
Release notes will be published in a separate page as new releases appear.

Licensing
---------
VaaS is an application written in Python based on Django and several other libraries. These libraries are Open Source and subject to their licenses. VaaS code is published under Apache Version 2.0 License.

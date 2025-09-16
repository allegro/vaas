VaaS in multiple DCs
====================
VaaS can be used in a multiple DC architecture.

Single DC
---------
The easiest set up is a set-up where all Varnish servers and their backends are located in the same DC. Just assign directors to the same cluster as your Varnish servers, and you are ready to go. Varnish will generate a single director in the actual VCL per a director defined in VaaS.

Two DCs in active / standby mode
--------------------------------
If your service's backends reside in two (or more) DCs and you assign backends from different DCs to an active-active director, VaaS will generate two (or more) actual directors for the service in the VCL. Assuming you have a service_one director and two dcs: dc1 and dc2, Varnish is going to use the DC it is located in as primary and the other DCs as fallback. This is achieved by the following VCL code (stripped of some additional elements for clarity):

    sub vcl_init {

        new service_one_dc1 = directors.round_robin();
        service_one_dc1.add_backend(backend_1_in_dc1);
        service_one_dc1.add_backend(backend_2_in_dc1);

        new service_one_dc2 = directors.round_robin();
        service_one_dc2.add_backend(backend_1_in_dc2);
        service_one_dc2.add_backend(backend_2_in_dc2);

        [...]
    }

    sub vcl_recv {

        if (req.url ~ "^\/service_one_path\/(.*)") {

            set req.backend_hint = service_one_dc1.backend();

            if (!std.healthy(req.backend_hint)) {

                set req.backend_hint = service_one_dc2.backend();

            }
        }
    }

Two DCs in active / active mode
-------------------------------
If you load balance traffic between two (or more) DCs and configure directors in active-active mode as in the previous example (Two DCs in active / standby mode), VaaS will generate VCLs in such way that each Varnish instance will use backends from it's DC as primary and backends from the other DC(s) as fallback.

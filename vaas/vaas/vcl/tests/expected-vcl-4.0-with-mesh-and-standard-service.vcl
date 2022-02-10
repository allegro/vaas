# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

import std;
import directors;

## header vcl ###
## acl rules ##
backend mesh_default_proxy {
    .host = "127.0.0.1";
    .port = "30001";
}

## START director ten_director_in_forth_hyrid_cluster ###
probe ten_director_in_forth_hyrid_cluster_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend ten_director_in_forth_hyrid_cluster_11_dc1_4_1_80 {
    .host = "127.11.4.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = ten_director_in_forth_hyrid_cluster_test_probe_1;
}

## END director ten_director_in_forth_hyrid_cluster ###

sub vcl_init {
    ## START director init ten_director_in_forth_hyrid_cluster ###

    new ten_director_in_forth_hyrid_cluster_dc1 = directors.round_robin();
    ten_director_in_forth_hyrid_cluster_dc1.add_backend(ten_director_in_forth_hyrid_cluster_11_dc1_4_1_80);

    ## END director init ten_director_in_forth_hyrid_cluster ###

}

sub use_director_director_with_mesh_service_support {
    unset req.http.x-service-tag;
    set req.http.x-service-mesh-timeout = "300000";
    set req.http.x-mesh-host = "mesh_service_support";
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/mesh_service/support";
    unset req.http.X-VaaS-Director;
    set req.http.X-VaaS-Director = "service-mesh/director_with_mesh_service_support";
    unset req.http.x-action;
    set req.http.x-action = "service-mesh";
}
sub use_director_ten_director_in_forth_hyrid_cluster {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/ten";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/ten";
    set req.http.X-VaaS-Director = "dc1/ten_director_in_forth_hyrid_cluster";
    set req.backend_hint = ten_director_in_forth_hyrid_cluster_dc1.backend();
}

sub vcl_recv {
if (req.http.x-use-director) {
    if (req.http.x-use-director == "director_with_mesh_service_support") {
        call use_director_director_with_mesh_service_support;
    }
    if (req.http.x-use-director == "ten_director_in_forth_hyrid_cluster") {
        call use_director_ten_director_in_forth_hyrid_cluster;
    }
    if (req.http.X-VaaS-Director) {
        return(pass);
    }
}
}


sub vcl_recv {
    if (req.url == "/vaas_status") {
        return (synth(999, ""));
    }

    if (req.url == "/vaas/" && req.http.x-allow-metric-header) {
        return (synth(989, ""));
    }
}

sub vcl_synth {
    if (resp.status == 999) {
            set resp.status = 503;
        synthetic("");
    }
    if (resp.status == 989) {
        set resp.status = 200;
        set resp.http.Content-Type = "application/json";
        synthetic ( {"{ "vcl_version" : "8339a", "varnish_status": "disabled" }"} );
        return (deliver);
    }
}
## Proper protocol redirect ##
sub vcl_recv {
    if (!req.http.X-Forwarded-Proto) {
        set req.http.X-Forwarded-Proto = "http";
    }
}
sub vcl_synth {
    if (resp.status == 998) {
        set resp.http.Location = resp.reason + req.http.host + req.url;
        set resp.status = 301;
        synthetic ("");
        return (deliver);
    }
}
sub protocol_redirect {
    if (req.esi_level == 0 && (req.method == "GET" || req.method == "HEAD")) {
        if ((req.http.X-Accept-Proto != "both") && (req.http.X-Accept-Proto != req.http.X-Forwarded-Proto)) {
            return(synth(998, req.http.X-Accept-Proto + "://"));
        }
    }
}
sub vcl_recv {
    if (req.url ~ "^\/mesh_service\/support([\/\?].*)?$") {
        call use_director_director_with_mesh_service_support;
    }
    else if (req.url ~ "^\/ten([\/\?].*)?$") {
        call use_director_ten_director_in_forth_hyrid_cluster;
    }

# Flexible ROUTER

# Test ROUTER
if (req.http.x-validation == "1") {
    return (synth(601, "Test routing response"));
}
    # Call protocol redirect sub
    call protocol_redirect;
    # SET ACTION based on x-action
    # if last used director is reachable via sm - its proper time to overwrite host header
    if(req.http.x-action == "service-mesh") {
        set req.http.x-original-host = req.http.host;
        set req.http.host = req.http.x-mesh-host;
        unset req.http.x-mesh-host;
        # Setup default backend to use
        set req.backend_hint = mesh_default_proxy;
    }
    # Handler for no backend in director
    if(req.http.x-action != "nobackend") {
        set req.http.x-action = req.http.x-route-action;
    }
    if(req.http.x-action == "nobackend") {
        return(synth(404, "<!--Director " + req.http.x-director + " has no backends or is disabled-->"));
    } else if(req.http.x-action == "pipe") {
        return (pipe);
    }

    # POST, PUT, DELETE are passed directly to backend
    if (req.method != "GET" && req.method !="HEAD") {
        return (pass);
    }
    return (hash);
}

## test response synth ##
sub vcl_synth {
    if (resp.status == 601) {
        set req.http.X-Director = regsuball(req.http.X-VaaS-Director, ".*/", "\1");
        synthetic ( {"{ "route": ""} + req.http.X-Route + {"", "director": ""} + req.http.X-Director + {"" }"} );
        set resp.http.X-Validation-Response = 1;
        set resp.http.Content-Type = "application/json";
        set resp.status = 203;
        return (deliver);
    }
}
sub vcl_pipe {
    # http://www.varnish-cache.org/ticket/451
    # This forces every pipe request to be the first one.
    set bereq.http.connection = "close";
}
## other functions ##
## empty director synth ##
sub vcl_synth {
    if (resp.status == 404) {
        synthetic (resp.reason);
        set resp.status = 404;
        return (deliver);
    }
}
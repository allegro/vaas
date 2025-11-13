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


sub vcl_init {
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
    set req.http.X-VaaS-Director = "sm/director_with_mesh_service_support";
    unset req.http.x-action;
    set req.http.x-action = "service-mesh";
}
sub use_director_director_with_mesh_service_support_and_service_tag {
    set req.http.x-service-tag = "service-tag-1";
    set req.http.x-service-mesh-timeout = "300000";
    set req.http.x-mesh-host = "mesh_service_support_with_service_tag";
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/mesh_service_service_tag/support";
    unset req.http.X-VaaS-Director;
    set req.http.X-VaaS-Director = "sm/director_with_mesh_service_support_and_service_tag";
    unset req.http.x-action;
    set req.http.x-action = "service-mesh";
}

sub vcl_recv {
if (req.http.x-use-director) {
    if (req.http.x-use-director == "director_with_mesh_service_support") {
        call use_director_director_with_mesh_service_support;
    }
    if (req.http.x-use-director == "director_with_mesh_service_support_and_service_tag") {
        call use_director_director_with_mesh_service_support_and_service_tag;
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
        if (std.file_exists("/etc/vaas_status_503")) {
            set resp.status = 503;
        }
        synthetic("");
    }
    if (resp.status == 989) {
        set resp.status = 200;
        set resp.http.Content-Type = "application/json";
        synthetic ( {"{ "vcl_version" : "162ac", "varnish_status": "disabled" }"} );
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
    } else if (resp.status == 888) {
        set resp.http.Location = req.http.x-destination;
        set resp.status = std.integer(req.http.x-response-code, 301);
        synthetic ("");
        return (deliver);
    }
}
sub protocol_redirect {
    if (req.esi_level == 0 && (req.method == "GET" || req.method == "HEAD") && req.http.X-Accept-Proto) {
        if ((req.http.X-Accept-Proto != "both") && (req.http.X-Accept-Proto != req.http.X-Forwarded-Proto)) {
            return(synth(998, req.http.X-Accept-Proto + "://"));
        }
    }
}
sub vcl_recv {
    if (req.url ~ "^\/mesh_service\/support([\/\?].*)?$") {
        call use_director_director_with_mesh_service_support;
    }
    else if (req.url ~ "^\/mesh_service_service_tag\/support([\/\?].*)?$") {
        call use_director_director_with_mesh_service_support_and_service_tag;
    }

# Flexible ROUTER
    if (req.http.x-validation == "1") {
        set req.http.x-canary-random = 0;
    } else {
        set req.http.x-canary-random = std.random(0, 100);
    }

    unset req.http.x-canary-random;

# Flexible REDIRECT


# Test ROUTER
if (req.http.x-validation == "1") {
    return (synth(601, "Test routing response"));
}
if (req.http.x-validation == "2") {
    return (synth(602, "Test routing response"));
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
    # Handler for redirect
    if(req.http.x-action == "redirect") {
        return (synth(888, req.http.X-Forwarded-Proto + "://"));
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
        set req.http.x-director = regsuball(req.http.X-VaaS-Director, ".*/", "\1");
        synthetic ( {"{ "route": ""} + req.http.X-Route + {"", "director": ""} + req.http.x-director + {"" }"} );
        set resp.http.x-validation-response = 1;
        set resp.http.Content-Type = "application/json";
        set resp.status = 203;
        return (deliver);
    }
    if (resp.status == 602) {
        synthetic ( {"{ "redirect": ""} + req.http.x-redirect + {"", "location": ""} + req.http.x-destination + {"" }"} );
        set resp.http.x-validation-response = 1;
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
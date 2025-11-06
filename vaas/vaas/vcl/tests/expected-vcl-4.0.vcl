# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

import std;
import directors;

## header vcl ###
## acl rules ##
## START director third_service ###
probe third_service_test_probe_28_3 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend third_service_4_dc1_2_1_80 {
    .host = "127.8.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = third_service_test_probe_28_3;
}

## END director third_service ###
## START director fourth_director_which_has_a_ridiculously_long_name ###
probe fourth_director_which_has_a_ridiculously_long_name_test_probe_29_4 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend fourth_director_which_has_a_ridiculously_lon_5_dc1_255_254_65535 {
    .host = "127.9.255.254";
    .port = "65535";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = fourth_director_which_has_a_ridiculously_long_name_test_probe_29_4;
}

## END director fourth_director_which_has_a_ridiculously_long_name ###
## START director first_service ###
probe first_service_test_probe_26_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend first_service_1_dc2_1_1_80 {
    .host = "127.0.1.1";
    .port = "80";
    .max_connections = 1;
    .connect_timeout = 0.50s;
    .first_byte_timeout = 0.10s;
    .between_bytes_timeout = 1.00s;
    .probe = first_service_test_probe_26_1;
}

## END director first_service ###
## START director second_service ###
probe second_service_test_probe_27_2 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend second_service_2_dc2_2_1_80 {
    .host = "127.0.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = second_service_test_probe_27_2;
}

backend second_service_3_dc1_2_1_80 {
    .host = "127.4.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = second_service_test_probe_27_2;
}
backend second_service_9_dc1_2_2_80 {
    .host = "127.4.2.2";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = second_service_test_probe_27_2;
}

## END director second_service ###
## START director sixth_director_hashing_by_cookie ###
probe sixth_director_hashing_by_cookie_test_probe_31_6 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend sixth_director_hashing_by_cookie_7_dc1_2_1_80 {
    .host = "127.10.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = sixth_director_hashing_by_cookie_test_probe_31_6;
}

## END director sixth_director_hashing_by_cookie ###
## START director seventh_director_hashing_by_url ###
probe seventh_director_hashing_by_url_test_probe_32_7 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
}

backend seventh_director_hashing_by_url_8_dc1_2_1_80 {
    .host = "127.11.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = seventh_director_hashing_by_url_test_probe_32_7;
}

## END director seventh_director_hashing_by_url ###
## START director eighth_service ###
probe eighth_service_test_probe_start_as_healthy_8 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1.0s;
    .window = 5;
    .threshold = 3;
    .initial = 3;
}

backend eighth_service_10_dc1_3_1_80 {
    .host = "127.11.3.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.30s;
    .first_byte_timeout = 5.00s;
    .between_bytes_timeout = 1.00s;
    .probe = eighth_service_test_probe_start_as_healthy_8;
}

## END director eighth_service ###

sub vcl_init {
    ## START director init third_service ###

    new third_service_dc1 = directors.random();
    third_service_dc1.add_backend(third_service_4_dc1_2_1_80, 1);

    ## END director init third_service ###

    ## START director init fourth_director_which_has_a_ridiculously_long_name ###

    new fourth_director_which_has_a_ridiculously_long_name_dc1 = directors.random();
    fourth_director_which_has_a_ridiculously_long_name_dc1.add_backend(fourth_director_which_has_a_ridiculously_lon_5_dc1_255_254_65535, 1);

    ## END director init fourth_director_which_has_a_ridiculously_long_name ###

    ## START director init first_service ###

    new first_service_dc2 = directors.round_robin();
    first_service_dc2.add_backend(first_service_1_dc2_1_1_80);

    ## END director init first_service ###

    ## START director init second_service ###

    new second_service_dc2 = directors.random();
    second_service_dc2.add_backend(second_service_2_dc2_2_1_80, 1);

    new second_service_dc1 = directors.random();
    second_service_dc1.add_backend(second_service_3_dc1_2_1_80, 1);
    second_service_dc1.add_backend(second_service_9_dc1_2_2_80, 0);

    ## END director init second_service ###

    ## START director init sixth_director_hashing_by_cookie ###

    new sixth_director_hashing_by_cookie_dc1 = directors.hash();
    sixth_director_hashing_by_cookie_dc1.add_backend(sixth_director_hashing_by_cookie_7_dc1_2_1_80, 1);

    ## END director init sixth_director_hashing_by_cookie ###

    ## START director init seventh_director_hashing_by_url ###

    new seventh_director_hashing_by_url_dc1 = directors.hash();
    seventh_director_hashing_by_url_dc1.add_backend(seventh_director_hashing_by_url_8_dc1_2_1_80, 1);

    ## END director init seventh_director_hashing_by_url ###

    ## START director init eighth_service ###

    new eighth_service_dc1 = directors.round_robin();
    eighth_service_dc1.add_backend(eighth_service_10_dc1_3_1_80);

    ## END director init eighth_service ###

}

sub use_director_third_service {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "third.service.org";
    unset req.http.x-action;
    set req.http.X-VaaS-Director = "dc1/third_service";
    set req.backend_hint = third_service_dc1.backend();
}
sub use_director_fourth_director_which_has_a_ridiculously_long_name {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "unusual.name.org";
    unset req.http.x-action;
    set req.http.X-VaaS-Director = "dc1/fourth_director_which_has_a_ridiculously_long_name";
    set req.backend_hint = fourth_director_which_has_a_ridiculously_long_name_dc1.backend();
}
sub use_director_first_service {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/first";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/first";
    set req.http.X-VaaS-Director = "dc2/first_service";
    set req.backend_hint = first_service_dc2.backend();
}
sub use_director_second_service {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/second";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/second";
    set req.http.X-VaaS-Director = "dc2/second_service";
    set req.backend_hint = second_service_dc2.backend();
    if (!std.healthy(req.backend_hint)) {
        set req.http.X-VaaS-Director = "dc1/second_service";
        set req.backend_hint = second_service_dc1.backend();
    }
}
sub use_director_sixth_director_hashing_by_cookie {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/sixth";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/sixth";
    set req.http.X-VaaS-Director = "dc1/sixth_director_hashing_by_cookie";
    set req.backend_hint = sixth_director_hashing_by_cookie_dc1.backend(req.http.cookie);
}
sub use_director_seventh_director_hashing_by_url {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/seventh";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/seventh";
    set req.http.X-VaaS-Director = "dc1/seventh_director_hashing_by_url";
    set req.backend_hint = seventh_director_hashing_by_url_dc1.backend(req.url);
}
sub use_director_eighth_service {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/eighth";
    unset req.http.x-action;
    set req.http.X-Forwarded-Prefix = "/eighth";
    set req.http.X-VaaS-Director = "dc1/eighth_service";
    set req.backend_hint = eighth_service_dc1.backend();
}
sub use_director_ningth_director_without_backends {
    unset req.http.X-Accept-Proto;
    set req.http.X-Accept-Proto = "https";
    unset req.http.X-VaaS-Prefix;
    set req.http.X-VaaS-Prefix = "/ningth";
    unset req.http.x-action;
    set req.http.x-action = "nobackend";
    set req.http.x-director = "ningth_director_without_backends";
}

sub vcl_recv {
if (req.http.x-use-director) {
    if (req.http.x-use-director == "third_service") {
        call use_director_third_service;
    }
    if (req.http.x-use-director == "fourth_director_which_has_a_ridiculously_long_name") {
        call use_director_fourth_director_which_has_a_ridiculously_long_name;
    }
    if (req.http.x-use-director == "first_service") {
        call use_director_first_service;
    }
    if (req.http.x-use-director == "second_service") {
        call use_director_second_service;
    }
    if (req.http.x-use-director == "sixth_director_hashing_by_cookie") {
        call use_director_sixth_director_hashing_by_cookie;
    }
    if (req.http.x-use-director == "seventh_director_hashing_by_url") {
        call use_director_seventh_director_hashing_by_url;
    }
    if (req.http.x-use-director == "eighth_service") {
        call use_director_eighth_service;
    }
    if (req.http.x-use-director == "ningth_director_without_backends") {
        call use_director_ningth_director_without_backends;
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
        synthetic ( {"{ "vcl_version" : "c06bc", "varnish_status": "disabled" }"} );
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
    if (req.http.host ~ "^third.service.org") {
        call use_director_third_service;
    }
    else if (req.http.host ~ "^unusual.name.org") {
        call use_director_fourth_director_which_has_a_ridiculously_long_name;
    }
    else if (req.url ~ "^\/first([\/\?].*)?$") {
        call use_director_first_service;
    }
    else if (req.url ~ "^\/second([\/\?].*)?$") {
    set req.url = regsub(req.url, "^/second(/)?", "/");
        call use_director_second_service;
    }
    else if (req.url ~ "^\/sixth([\/\?].*)?$") {
        call use_director_sixth_director_hashing_by_cookie;
    }
    else if (req.url ~ "^\/seventh([\/\?].*)?$") {
        call use_director_seventh_director_hashing_by_url;
    }
    else if (req.url ~ "^\/eighth([\/\?].*)?$") {
        call use_director_eighth_service;
    }
    else if (req.url ~ "^\/ningth([\/\?].*)?$") {
        call use_director_ningth_director_without_backends;
    }

# Flexible ROUTER
    if (req.http.x-validation == "1") {
        set req.http.x-canary-random = 0;
    } else {
        set req.http.x-canary-random = std.random(0, 100);
    }
    if (req.url ~ "^\/flexible") {
        set req.http.X-Route = "1";
        set req.http.x-route-action = "pass";
        call use_director_first_service;
    }

    unset req.http.x-canary-random;

# Flexible REDIRECT
    if (req.http.host == "example.prod.com") {
    if (req.url ~ "/source") {
        set req.http.x-redirect = "2";
        set req.http.x-destination = "http://example.prod.com/new_destination";
        set req.http.x-response-code = "301";
        set req.http.x-action = "redirect";
    }
    else if (req.url ~ "/source") {
        set req.http.x-redirect = "1";
        set req.http.x-destination = "http://example.prod.com/destination";
        set req.http.x-response-code = "301";
        set req.http.x-action = "redirect";
    }
    }
    if (req.http.host == "example.prod.org") {
    if (req.url ~ "/source") {
        set req.http.x-redirect = "2";
        set req.http.x-destination = "http://example.prod.org/new_destination";
        set req.http.x-response-code = "301";
        set req.http.x-action = "redirect";
    }
    else if (req.url ~ "/source") {
        set req.http.x-redirect = "1";
        set req.http.x-destination = "http://example.prod.org/destination";
        set req.http.x-response-code = "301";
        set req.http.x-action = "redirect";
    }
    }


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
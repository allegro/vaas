# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

import std;
import directors;

## header vcl ###
## acl rules ##
## START director third_service ###
probe third_service_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend third_service_4_dc1_2_1_80 {
    .host = "127.8.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = third_service_test_probe_1;
}

## END director third_service ###
## START director fourth_director_which_has_a_ridiculously_long_name ###
probe fourth_director_which_has_a_ridiculously_long_name_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend fourth_director_which_has_a_ridiculously_lon_5_dc1_255_254_65535 {
    .host = "127.9.255.254";
    .port = "65535";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = fourth_director_which_has_a_ridiculously_long_name_test_probe_1;
}

## END director fourth_director_which_has_a_ridiculously_long_name ###
## START director first_service ###
probe first_service_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend first_service_1_dc2_1_1_80 {
    .host = "127.0.1.1";
    .port = "80";
    .max_connections = 1;
    .connect_timeout = 0.5s;
    .first_byte_timeout = 0.1s;
    .between_bytes_timeout = 1s;
    .probe = first_service_test_probe_1;
}

## END director first_service ###
## START director second_service ###
probe second_service_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend second_service_2_dc2_2_1_80 {
    .host = "127.0.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = second_service_test_probe_1;
}

backend second_service_3_dc1_2_1_80 {
    .host = "127.4.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = second_service_test_probe_1;
}

## END director second_service ###
## START director sixth_director_hashing_by_cookie ###
probe sixth_director_hashing_by_cookie_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend sixth_director_hashing_by_cookie_7_dc1_2_1_80 {
    .host = "127.10.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = sixth_director_hashing_by_cookie_test_probe_1;
}

## END director sixth_director_hashing_by_cookie ###
## START director seventh_director_hashing_by_url ###
probe seventh_director_hashing_by_url_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend seventh_director_hashing_by_url_8_dc1_2_1_80 {
    .host = "127.11.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = seventh_director_hashing_by_url_test_probe_1;
}

## END director seventh_director_hashing_by_url ###

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

    ## END director init second_service ###

    ## START director init sixth_director_hashing_by_cookie ###

    new sixth_director_hashing_by_cookie_dc1 = directors.hash();
    sixth_director_hashing_by_cookie_dc1.add_backend(sixth_director_hashing_by_cookie_7_dc1_2_1_80, 1);

    ## END director init sixth_director_hashing_by_cookie ###

    ## START director init seventh_director_hashing_by_url ###

    new seventh_director_hashing_by_url_dc1 = directors.hash();
    seventh_director_hashing_by_url_dc1.add_backend(seventh_director_hashing_by_url_8_dc1_2_1_80, 1);

    ## END director init seventh_director_hashing_by_url ###

}
sub vcl_recv {
    if (req.http.host ~ "^third.service.org") {
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "third.service.org";
        set req.http.X-VaaS-Director = "dc1/third_service";
        set req.backend_hint = third_service_dc1.backend();

    }
    else if (req.http.host ~ "^unusual.name.org") {
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "unusual.name.org";
        set req.http.X-VaaS-Director = "dc1/fourth_director_which_has_a_ridiculously_long_name";
        set req.backend_hint = fourth_director_which_has_a_ridiculously_long_name_dc1.backend();

    }
    else if (req.url ~ "^\/first([\/\?].*)?$") {
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/first";
        set req.http.X-Forwarded-Prefix = "/first";
        set req.http.X-VaaS-Director = "dc2/first_service";
        set req.backend_hint = first_service_dc2.backend();

    }
    else if (req.url ~ "^\/second([\/\?].*)?$") {
        set req.url = regsub(req.url, "^/second(/)?", "/");
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/second";
        set req.http.X-Forwarded-Prefix = "/second";
        set req.http.X-VaaS-Director = "dc2/second_service";
        set req.backend_hint = second_service_dc2.backend();
        if (!std.healthy(req.backend_hint)) {
            set req.http.X-VaaS-Director = "dc1/second_service";
            set req.backend_hint = second_service_dc1.backend();
        }

    }
    else if (req.url ~ "^\/sixth([\/\?].*)?$") {
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/sixth";
        set req.http.X-Forwarded-Prefix = "/sixth";
        set req.http.X-VaaS-Director = "dc1/sixth_director_hashing_by_cookie";
        set req.backend_hint = sixth_director_hashing_by_cookie_dc1.backend(req.http.cookie);

    }
    else if (req.url ~ "^\/seventh([\/\?].*)?$") {
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/seventh";
        set req.http.X-Forwarded-Prefix = "/seventh";
        set req.http.X-VaaS-Director = "dc1/seventh_director_hashing_by_url";
        set req.backend_hint = seventh_director_hashing_by_url_dc1.backend(req.url);

    }

    # POST, PUT, DELETE are passed directly to backend
    if (req.method != "GET") {
        return (pass);
    }
    return (hash);
}
## other functions ##
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

director third_service_dc1 random {
    {
      .backend = third_service_4_dc1_2_1_80;
      .weight = 1;
    }

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

director fourth_director_which_has_a_ridiculously_long_name_dc1 random {
    {
      .backend = fourth_director_which_has_a_ridiculously_lon_5_dc1_255_254_65535;
      .weight = 1;
    }

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

director first_service_dc2 round-robin {
    {
      .backend = first_service_1_dc2_1_1_80;
    }

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

director second_service_dc2 random {
    {
      .backend = second_service_2_dc2_2_1_80;
      .weight = 1;
    }

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

director second_service_dc1 random {
    {
      .backend = second_service_3_dc1_2_1_80;
      .weight = 1;
    }

}
## END director second_service ###
## START director fifth_director_only_cluster1_siteA_test ###
probe fifth_director_only_cluster1_siteA_test_test_probe_1 {
    .url = "/status";
    .expected_response = 200;
    .interval = 3s;
    .timeout = 1s;
    .window = 5;
    .threshold = 3;
}

backend fifth_director_only_cluster1_siteA_test_6_dc1_2_1_80 {
    .host = "127.9.2.1";
    .port = "80";
    .max_connections = 5;
    .connect_timeout = 0.3s;
    .first_byte_timeout = 5s;
    .between_bytes_timeout = 1s;
    .probe = fifth_director_only_cluster1_siteA_test_test_probe_1;
}

director fifth_director_only_cluster1_siteA_test_dc1 round-robin {
    {
      .backend = fifth_director_only_cluster1_siteA_test_6_dc1_2_1_80;
    }

}
## END director fifth_director_only_cluster1_siteA_test ###
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

# Directors hashing by req.http.cookie are not supported in varnish v3.
# Falling back to director hashing by req.url.
director sixth_director_hashing_by_cookie_dc1 hash {
    {
      .backend = sixth_director_hashing_by_cookie_7_dc1_2_1_80;
      .weight = 1;
    }

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

director seventh_director_hashing_by_url_dc1 hash {
    {
      .backend = seventh_director_hashing_by_url_8_dc1_2_1_80;
      .weight = 1;
    }

}
## END director seventh_director_hashing_by_url ###

sub vcl_recv {
    if (req.http.host ~ "^third.service.org") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "third.service.org";
        set req.http.X-VaaS-Director = "dc1/third_service";
        set req.backend = third_service_dc1;

    }
    else if (req.http.host ~ "^unusual.name.org") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "unusual.name.org";
        set req.http.X-VaaS-Director = "dc1/fourth_director_which_has_a_ridiculously_long_name";
        set req.backend = fourth_director_which_has_a_ridiculously_long_name_dc1;

    }
    else if (req.url ~ "^\/first([\/\?].*)?$") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/first";
        set req.http.X-Forwarded-Prefix = "/first";
        set req.http.X-VaaS-Director = "dc2/first_service";
        set req.backend = first_service_dc2;

    }
    else if (req.url ~ "^\/second([\/\?].*)?$") {
        set req.url = regsub(req.url, "^/second(/)?", "/");
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/second";
        set req.http.X-Forwarded-Prefix = "/second";
        set req.http.X-VaaS-Director = "dc2/second_service";
        set req.backend = second_service_dc2;
        if (!req.backend.healthy) {
            set req.http.X-VaaS-Director = "dc1/second_service";
            set req.backend = second_service_dc1;
        }

    }
    else if (req.url ~ "^\/fifth([\/\?].*)?$") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/fifth";
        set req.http.X-Forwarded-Prefix = "/fifth";
        set req.http.X-VaaS-Director = "dc1/fifth_director_only_cluster1_siteA_test";
        set req.backend = fifth_director_only_cluster1_siteA_test_dc1;

    }
    else if (req.url ~ "^\/sixth([\/\?].*)?$") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/sixth";
        set req.http.X-Forwarded-Prefix = "/sixth";
        set req.http.X-VaaS-Director = "dc1/sixth_director_hashing_by_cookie";
        set req.backend = sixth_director_hashing_by_cookie_dc1;

    }
    else if (req.url ~ "^\/seventh([\/\?].*)?$") {
        remove req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "/seventh";
        set req.http.X-Forwarded-Prefix = "/seventh";
        set req.http.X-VaaS-Director = "dc1/seventh_director_hashing_by_url";
        set req.backend = seventh_director_hashing_by_url_dc1;

    }

    # POST, PUT, DELETE are passed directly to backend
    if (req.request != "GET") {
        return (pass);
    }
    return (lookup);
}
## other functions ##
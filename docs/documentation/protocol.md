Proper Protocol Support
=======================

If your architecture utilizes Load Balancer (LB) server(s) which terminate SSL, you can notify your backend about it via
PROTOCOL flag in Director. The flag can be set to the following values:

* HTTP - Support only http protocol to backend
* HTTPS - Support only https protocol to backend
* BOTH - Support http and https protocol to backend

Default value is BOTH.

Workflow
--------

#### HTTPS request

A request arrives at a LB via HTTPS protocol. The LB terminates SSL and adds a header called 
[X-Forwarded-Proto](https://tools.ietf.org/html/rfc7239#section-5.4), set to "https". The LB passes the request to 
Varnish. If the header is set to https, Varnish will check whether you backend supports https communication (set per
director using appropriate flag: BOTH or HTTPS).

If the director supports supports https (PROTOCOL flag set to HTTPS or BOTH), Varnish will simply pass the request to
backend.

If the director does not support https (PROTOCOL flag set to HTTP), Varnish will send a response containing Location
header pointing to exactly the same location, but prefixed with http://.

```
https://example.com -> LB (X-Forwarded-Proto: https) -> Varnish (PROTOCOL flag set to HTTP) -> RES TO CLIENT Location: http://example.com
```

#### HTTP request

Conversely, if a request arrives at a LB via HTTP protocol, the LB adds appropriate X-Forwarded-Proto header, set to
"http". The LB passes the request to Varnish. If the header is set to http, Varnish will check whether your backend 
supports http communication (set per director using appropriate flag: HTTP or BOTH).  

If the director supports http (PROTOCOL flag set to HTTP or BOTH), Varnish will simply pass the request to backend.

If the director does not supprot http (PROTOCOL flag set to HTTPS), Varnish will send a response containing Location
header pointing to exactly the same location, but prefixed with https://.

```
http://example.com -> LB (X-Forwarded-Proto: http) -> Varnish (PROTOCOL flag set to HTTPS) -> RES TO CLIENT Location: https://example.com
```

Please note: if the X-Forwarded-Proto header is not set at all, Varnish will add it and set it to "http".

Implementation
--------------
If you just use the <VCL/> tag in VCL template, you don’t need to add anything. The feature is supported by default.
But if you use a custom VCL template, some extra tags will be required. The tag name is PROPER_PROTOCOL_REDIRECT and
its content looks as follows:

```
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
    if ((req.http.X-Accept-Proto != "both") && (req.http.X-Accept-Proto != req.http.X-Forwarded-Proto)) {
       return(synth(998, req.http.X-Accept-Proto + "://"));
    }

}
```

The PROPER_PROTOCOL_REDIRECT is called in RECV tag by default.

After the tag will generate the synth (redirect code). We need to call explicitly when using anything else but the
default VCL. To do that simply add:

```
call protocol_redirect;
```
in proper place.

For example, after selecting the backend:

```
sub vcl_recv {
    if (req.http.host ~ "^second.*") {
        unset req.http.X-Accept-Proto;
        set req.http.X-Accept-Proto = "both";
        unset req.http.X-VaaS-Prefix;
        set req.http.X-VaaS-Prefix = "second.*";
        set req.http.X-VaaS-Director = "dc1/second_service";
        set req.backend_hint = second_service_dc1.backend();

    }

    # Call protocol redirect sub
    call protocol_redirect;

    # POST, PUT, DELETE are passed directly to backend
    if (req.method != "GET") {
        return (pass);
    }
    return (hash);
}
```

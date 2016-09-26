Proper Protocol Support
=============

If you architecture have Load balancer (LB) server who terminate SSL you can support it to you backend via PROTOCOL flag in Director.
The flag can be:

* HTTP - Support only http protocol to backend
* HTTPS - Support only https protocol to backend
* BOTH - Support http and https protocol to backend

Default value is BOTH.

Workflow
--------
The request has came to LB via HTTPS protocol. The LB terminate SSL and add proper header called [X-Forwarded-Proto](https://tools.ietf.org/html/rfc7239#section-5.4).
The LB pass request to varnish. And if the header is set varnish will check that you backend support https communication (setup in director proper flag both/https).

If backend support it varnish send responce whit Location header with https://.
```
http://example.com -> LB(Add X-Forwarded-Proto: https) -> Varnish -> RES TO CLIENT Location: https://example.com
```

If backend support both protocol (http and https) the varnish will pass request to backend.
```
http://example.com -> LB -> Varnish (If no X-Forwarded-Proto will add) -> Backend -> RES TO CLIENT
https://example.com -> LB (add X-Forwarded-Proto) -> Varnish -> Backend -> RES TO CLIENT
```

Implementation
--------------
If we just use VCL tag we don't need to edit. The support is enable.
But if we use custom vcl template we need to add extra tags in our vcl template.
The tag name is PROPER_PROTOCOL_REDIRECT and the content looks like below:

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

The PROPER_PROTOCOL_REDIRECT is called in RECV tag for default.
After the tag generate the synth (redirect code) we need to call it. To do that simply add:
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

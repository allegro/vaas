VaaS API
========

You can use VaaS API to add, edit or remove backends in directors. VaaS Rest API is based on [tastypie](https://django-tastypie.readthedocs.org/en/latest/) python library. At the moment of this writing, only json format is supported.

Resources
---------

The following resources are available:

| Name                 | Description                                                                                               |Allowed actions               | Allowed commands       |
|----------------------|-----------------------------------------------------------------------------------------------------------|------------------------------|------------------------|
| *Backend*            | Represents a single node in a service (director)                                                          |preview, **add, edit, delete**|                        |
| *Director*           | A Varnish director; may represent a SOA service                                                           |preview, **add, edit, delete**|                        |
| *Probe*              | A health check used to determine backend status                                                           |preview, **add, edit, delete**|                        |
| *Dc*                 | Datacenter                                                                                                |preview, **add, edit, delete**|                        |
| *Logical Cluster*    | Cluster of Varnish servers                                                                                |preview, **add, edit, delete**| connect-command        |
| *Varnish Servers*    | A Varnish server                                                                                          |preview, **add, edit, delete**|                        |
| *VCL Template Block* | A VCL template block                                                                                      |preview, **add, edit, delete**|                        |
| *VCL Template*       | A VCL template                                                                                            |preview, **add, edit, delete**| vcl-validate-command   |
| *Time Profile*       | Default timeouts profile for director                                                                     |preview, **add, edit, delete**|                        |
| *Purger*             | Purge object from varnishes from a given cluster                                                          |                              |                        |
| *Outdated Server*    | Represents active varnish servers with outdated vcl                                                       |preview                       |                        |
| *Task*               | Represents state of reloading task - check [VaaS Request Flow](./flow.md)                                 |preview                       |                        |
| *Redirect*           | Represents conditional redirection to particular URL                                                      |preview, **add, edit, delete**| validate-command       |
| *Route*              | Represents conditional routing to desired Director                                                        |preview, **add, edit, delete**|                        |
| *RouteConfig*        | Represents possible request parameters, operators & actions, which can be used in Routes                  |preview|                        |
| *ValidationReport*   | Represents report of positive urls validation which checks if positive urls are handled by desired Routes |preview|                        |

VaaS resources can be previewed under http://<VaaS instance\>/api/v0.1/?format=json

Authentication methods
----------------------

Authentication is required for all requests except schema. There is only one method of authentication: api key. Credentials for this method (i.e. username and api key) can be passed as query params or as http headers. 

To access VaaS API, first generate API key. Click on *Welcome, <username> -> Api Key* to achieve that. 

![Api Key generation](img/api_change_api_key.png)

Sample API requests
===================

All examples below can be tested using [VaaS in Docker Compose](../quick-start/development.md).

###List directors

    curl "http://localhost:3030/api/v0.1/director/?username=admin&api_key=vagrant_api_key"

###List backends 
To list backends located in specified DC belonging to specified Director:

    curl "http://localhost:3030/api/v0.1/backend/?director__name=second_service&dc__symbol=dc1&username=admin&api_key=vagrant_api_key"

### Create a new Cluster

    curl -X POST \
    -d '{ "name": "cluster1" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/logical_cluster/?username=admin&api_key=vagrant_api_key" 

### Create a new DC

    curl -X POST \
    -d '{ "name": "dc1", "symbol": "dc1" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/dc/?username=admin&api_key=vagrant_api_key" 

### Create a new VCL template

    curl -X POST \
    -d '{ "version": "4.0", "content": "<VCL/>", "name": "vcl_template_4" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/vcl_template/?username=admin&api_key=vagrant_api_key"


### Call vcl validate command for a new template content

Important remark: the command id (in the below example: 7110e99e-453a-4078-843a-f6c36dd358d2) passed in url should be uniq.
The intention of the command is to render new vcl template content, load it into servers connect to vcl template and verify if it will be properly compiled.

    curl -X PUT \
    -d '{ "content": "<VCL/>"}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/vcl_template/2/vcl-validate-command/7110e99e-453a-4078-843a-f6c36dd358d2/?username=admin&api_key=vagrant_api_key"

expected output

    {
      "output": null,
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d2",
      "status": "PENDING",
      "content": "<VCL/>"
    }

### Verify command result

    curl "http://localhost:3030/api/v0.1/varnish_server/connect-command/7110e99e-453a-4078-843a-f6c36dd358d1/?username=admin&api_key=vagrant_api_key"
expected output

    {
      "output":  {"is_valid": true, "servers_num": 3},
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d1",
      "status": "SUCCESS",
      "content": "<VCL/>"
    }

It's worth mentioning that validation status is passed in output.is_valid, status (SUCCESS) means only that asynchronous validation was processed.

### Create a new Probe

    curl -X POST \
    -d '{ "name": "probe1", "url": "/ts.1", "expected_response": "200" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/probe/?username=admin&api_key=vagrant_api_key"

### Create a new Director

    curl -X POST \
    -d '{ "name": "director1", "service": "service1", "reachable_via_service_mesh": true, "service_mesh_label": "service1", "service_tag": "www", "probe": "/api/v0.1/probe/1/", "route_expression": "/abc", "cluster": ["/api/v0.1/logical_cluster/1/"], "mode": "round-robin", "time_profile": "/api/v0.1/time_profile/1/" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/director/?username=admin&api_key=vagrant_api_key"

### Create a new Backend and add it to a Director

    curl -X POST \
    -d '{ "address": "172.17.0.1", "director": "/api/v0.1/director/1/", "dc": "/api/v0.1/dc/1/", "inherit_time_profile": true }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/backend/?username=admin&api_key=vagrant_api_key"

### Fetch backend by id

    curl -i "http://localhost:3030/api/v0.1/backend/1/?username=admin&api_key=vagrant_api_key"

### Update whole backend

    curl -i -X PUT \
    -d '{
      "address": "192.168.199.34",
      "between_bytes_timeout": "1",
      "connect_timeout": "0.3",
      "dc": {
        "id": 1,
        "name": "First datacenter",
        "resource_uri": "/api/v0.1/dc/1/",
        "symbol": "dc1"
      },
      "director": "/api/v0.1/director/1/",
      "enabled": true,
      "first_byte_timeout": "5",
      "id": 1,
      "inherit_time_profile": true,
      "max_connections": 5,
      "port": 80,
      "resource_uri": "/api/v0.1/backend/1/",
      "status": "Unknown",
      "tags": [],
      "time_profile": {
        "between_bytes_timeout": "1",
        "connect_timeout": "0.3",
        "first_byte_timeout": "5",
        "max_connections": 5
      },
      "weight": 1
    }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/backend/1/?username=admin&api_key=vagrant_api_key"


### Partially update backend

    curl -X PATCH \
    -d '{"address": "192.168.199.33"}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/backend/1/?username=admin&api_key=vagrant_api_key"


### Create a new Varnish server

    curl -X POST \
    -d '{ "ip": "172.17.0.7", "hostname": "varnish3", "dc": "/api/v0.1/dc/1/", "port": "6082", "secret": "edcf6c52-6f93-4d0d-82b9-cd74239146b0", "template": "/api/v0.1/vcl_template/1/", "cluster": "/api/v0.1/logical_cluster/1/", "enabled": "True" }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/varnish_server/?username=admin&api_key=vagrant_api_key"

### Call connect command for a set of varnishes by passing varnish ids

Important remark: the command id (in the below example: 7110e99e-453a-4078-843a-f6c36dd358d1) passed in url should be uniq.
The intention of the command is to connect to each requested **active** varnish server and return a varnish version or error in the output map.
For inactive or maintenance varnishes, the appropriate status will be returned.

    curl -X PUT \
    -d '{ "varnish_ids": [2,3]}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/varnish_server/connect-command/7110e99e-453a-4078-843a-f6c36dd358d1/?username=admin&api_key=vagrant_api_key"

expected output

    {
      "output": null,
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d1",
      "status": "PENDING",
      "varnish_ids": [
        2,
        3
      ]
    }


### Verify command result

    curl "http://localhost:3030/api/v0.1/varnish_server/connect-command/7110e99e-453a-4078-843a-f6c36dd358d1/?username=admin&api_key=vagrant_api_key"
expected output

    {
      "output": {
        "2": "varnish-7.0.3",
        "3": "varnish-4.1.11"
      },
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d1",
      "status": "SUCCESS",
      "varnish_ids": [
        2,
        3
      ]
    }

### Delete a backend

    curl -i -X DELETE "http://localhost:3030/api/v0.1/backend/1/?username=admin&api_key=vagrant_api_key"
 
 
### Patch a list of backends

    curl -X PATCH \
    -d '{
        "objects": [
        {
          "address": "172.17.0.1",
          "between_bytes_timeout": "1",
          "connect_timeout": "0.5",
          "dc": "/api/v0.1/dc/1/",
          "director": "/api/v0.1/director/1/",
          "enabled": true,
          "first_byte_timeout": "5",
          "id": 1,
          "max_connections": 5,
          "port": 80,
          "resource_uri": "/api/v0.1/backend/1/",
          "status": "Healthy",
          "weight": 1
        },
        {
          "address": "172.17.0.2",
          "between_bytes_timeout": "1",
          "connect_timeout": "0.5",
          "dc": "/api/v0.1/dc/1/",
          "director": "/api/v0.1/director/1/",
          "enabled": true,
          "first_byte_timeout": "5",
          "id": 2,
          "max_connections": 5,
          "port": 80,
          "resource_uri": "/api/v0.1/backend/2/",
          "status": "Healthy",
          "weight": 1
        }
      ]
    }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/backend/?username=admin&api_key=vagrant_api_key"


### Purge object from varnishes from a given cluster

    curl -X POST \
    -d '{ "url": "http://example.com/contact", "clusters": "cluster1_siteA_test"  }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/purger/?username=admin&api_key=vagrant_api_key"

### Purge object from varnishes from a given cluster with additional request headers (in case of multiple objects in cache because of HTTP Vary header).
### VaaS will generate HTTP purge requests for all possible combinations from given headers.

    curl -X POST \
    -d '{ "url": "http://example.com/contact", "clusters": "cluster1_siteA_test", "headers": {"header1": ["val1", "val2"], "header2": ["val1", "val2"]}  }' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/purger/?username=admin&api_key=vagrant_api_key"


### List outdated servers from single logical cluster

    curl "http://localhost:3030/api/v0.1/outdated_server/?username=admin&api_key=vagrant_api_key&cluster=clusterA"


### Asynchronous create a new Backend and add it to a Director, check reload status

    curl -X POST \
    -d '{ "address": "172.17.0.1", "director": "/api/v0.1/director/1/", "dc": "/api/v0.1/dc/1/", "inherit_time_profile": true }' \
    -H "Content-Type: application/json" \
    -H "Prefer: respond-async" \
    -v \
    "http://localhost:3030/api/v0.1/backend/?username=admin&api_key=vagrant_api_key"

    ...
    < Location: /api/v0.1/task/578d87b6-4dd5-4786-961d-4b3717e616c8/
    ...

    curl -i "http://localhost:3030/api/v0.1/task/578d87b6-4dd5-4786-961d-4b3717e616c8/?username=admin&api_key=vagrant_api_key"


### List redirects

    curl "http://localhost:3030/api/v0.1/redirect/?username=admin&api_key=vagrant_api_key&format=json"

### Create new redirect

    curl -X POST \
    -d '{"action":"302", "condition": "/path", "destination":"/new-path", "preserve_query_params": false, "priority": 1, "assertions": [{"expected_location": "/new-path", "given_url": "http://mydomain.example/newpath"}]}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/redirect/?username=admin&api_key=vagrant_api_key&format=json"

### Delete single route

    curl -X DELETE \
    "http://localhost:3030/api/v0.1/redirect/1/?username=admin&api_key=vagrant_api_key&format=json"

### Partially update route

    curl -X PATCH \
    -d '{"priority":2}' -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/redirect/1/?username=admin&api_key=vagrant_api_key&format=json"


### List routes

    curl "http://localhost:3030/api/v0.1/route/?username=admin&api_key=vagrant_api_key&format=json"

### Create new route

    curl -X POST \
    -d '{"action":"pass", "cluster": ["/api/v0.1/logical_cluster/1/"], "positive_urls": [{"url": "https://example.com/path"}], "condition": "req.http.Host ~ \"example.com\" && req.url ~ \"\/path\"", "director":"/api/v0.1/director/1/", "priority":4}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/route/?username=admin&api_key=vagrant_api_key&format=json"

### Delete single route

    curl -X DELETE \
    "http://localhost:3030/api/v0.1/route/1/?username=admin&api_key=vagrant_api_key&format=json"

### Partially update route

    curl -X PATCH \
    -d '{"action":"pass", "cluster": ["/api/v0.1/logical_cluster/1/"], "condition": "req.http.Host ~ \"example.com\" && req.url ~ \"\/path\"", "director":"/api/v0.1/director/1/", "priority":4}' \
    -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/route/1/?username=admin&api_key=vagrant_api_key&format=json"

### Call validate-command for all redirects

    curl -X PUT \
    -d '{ }' -H "Content-Type: application/json" \
    "http://localhost:3030/api/v0.1/redirect/validate-command/7110e99e-453a-4078-843a-f6c36dd358d2/?username=admin&api_key=vagrant_api_key"

expected output

    {
      "output": null,
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d2",
      "status": "PENDING"
    }

### Verify command result

    curl "http://localhost:3030/api/v0.1/redirect/validate-command/7110e99e-453a-4078-843a-f6c36dd358d1/?username=admin&api_key=vagrant_api_key"

expected output

    {
      "output": {
        "pk": "7110e99e-453a-4078-843a-f6c36dd358d2",
        "task_status": "SUCCESS",
        "validation_results": [],
        "validation_status": "PASS"
      },
      "pk": "7110e99e-453a-4078-843a-f6c36dd358d2",
      "status": "SUCCESS"
    }

### Examine route config

    curl "http://localhost:3030/api/v0.1/route_config/?username=admin&api_key=vagrant_api_key&format=json"

### Trigger positive url validation (check if positive urls are routed via desired Routes)

    curl -XPOST "http://localhost:3030/api/v0.1/validate_routes/?username=admin&api_key=admin_api_key&format=json"  -H'Content-Type: application/json' -d'{}'

Above request is asynchronous, it means all checks are verified in background.
Response contains *Location* header which provides url to validation report.
Report will be available after validation is finished.

### Fetch positive url validation report

    curl "http://localhost:3030/api/v0.1/validation_report/<REPORT-ID>/?username=admin&api_key=admin_api_key&format=json"

If report is available, field status will be set to "SUCCESS".
Otherwise, please try again in a moment.
The validation report is available for 500 seconds after its ready.

Explore more
============

Detailed information about interaction with api based on tastypie can be found [here](http://django-tastypie.readthedocs.io/en/latest/interacting.html).
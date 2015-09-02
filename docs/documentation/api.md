VaaS API
========

You can use VaaS API to add, edit or remove backends in directors. VaaS Rest API is based on [tastypie](https://django-tastypie.readthedocs.org/en/latest/) python library. At the moment of this writing, only json format is supported.

Resources
---------

The following resources are available:

|Name      |Description                                     |Allowed actions               |
|----------|------------------------------------------------|------------------------------|
|*Backend* |Represents a single node in a service (director)|preview, **add, edit, delete**|
|*Dc*      |Datacentre                                      |preview                       |
|*Director*|A Varnish director; may represent a SOA service |preview                       |
|*Probe*   |A health check used to determine backend status |preview                       |

VaaS resources can be previewed under http://<VaaS instance\>/api/v0.1/?format=json

Authentication methods
----------------------

Authentication is required for all requests except schema. There is only one method of authentication: api key. Credentials for this method (i.e. username and api key) can be passed as query params or as http headers. 

To access VaaS API, first generate API key. Click on *Welcome, <username> -> Api Key* to achieve that. 

![Api Key generation](/img/api_change_api_key.png)

Sample API requests
===================

All examples below can be tested using [VaaS in Vagrant](../quick-start/vagrant.md).

List directors
--------------

    curl "http://192.168.200.11:3030/api/v0.1/director/?username=admin&api_key=vagrant_api_key"

List backends 
-------------
To list backends located in specified DC belonging to specified Director:

    curl "http://192.168.200.11:3030/api/v0.1/backend/?director__name=second_service&dc__symbol=dc1&username=admin&api_key=vagrant_api_key"

Add backend to director
---------------------------

    curl -i -H "Accept: application/json"  -H "Content-Type: application/json" -X POST \
        "http://192.168.200.11:3030/api/v0.1/backend/?username=admin&api_key=vagrant_api_key" \
        -d'{"address": "192.168.200.16", "between_bytes_timeout": "1", "connect_timeout": "0.3", "dc": "/api/v0.1/dc/1/", "director": "/api/v0.1/director/2/", "enabled": true, "first_byte_timeout": "5", "max_connections": 5, "port": 8085, "weight": 5}'
 
Delete backend
----------------

    curl -i -X DELETE "http://192.168.200.11:3030/api/v0.1/backend/5/?username=admin&api_key=vagrant_api_key"
 
 
Patch a list of backends
------------------------

    curl -i -H "Accept: application/json"  -H "Content-Type: application/json" -X PATCH \
        "http://192.168.200.11:3030/api/v0.1/backend/?username=admin&api_key=vagrant_api_key" \
        -d'{"objects": [{"resource_uri": "/api/v0.1/backend/6/", "address": "192.168.200.15", "between_bytes_timeout": "1", "connect_timeout": "0.3", "dc": "/api/v0.1/dc/1/", "director": "/api/v0.1/director/2/", "enabled": true, "first_byte_timeout": "5", "max_connections": 5, "port": 8085, "weight": 5}, {"resource_uri": "/api/v0.1/backend/5/", "address": "192.168.200.14", "between_bytes_timeout": "1", "connect_timeout": "0.3", "dc": "/api/v0.1/dc/1/", "director": "/api/v0.1/director/2/", "enabled": false, "first_byte_timeout": "5", "max_connections": 5, "port": 8085, "weight": 5}]}'
 

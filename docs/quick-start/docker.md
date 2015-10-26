VaaS in Docker
==============
VaaS in Docker is a preconfigured instance of VaaS varnish configuration tool. It is meant as a demo application that can help to understand how VaaS works. 

How to run VaaS in Docker
-------------------------
By default, the container starts with no data loaded and with admin user identified by admin password:

    sudo docker run -p 80:80 -d -t allegro/vaas

You will now be able to log in to your container pointing your browser to the IP of your docker host.
If you want, You can start container with selected username and password as folows:

    sudo docker run -p 80:80 -d -t allegro/vaas <username> <email> <password> <api_key>

The last argument is optional. If you don't specify api_key, a random key will be generated.

Starting VaaS in Docker with API access
---------------------------------------

First, create a data.yaml file that will only contain an admin user definition with a preconfigured password "admin" and api key "vagrant_api_key" (do not copy directly copy and paste the data.yaml file contents below, use cat to generate it):

    cat > /var/tmp/data.yaml <<EOF
    - fields:
        date_joined: 2014-12-08 09:23:38.799778+00:00
        email: admin@vaas.allegrogroup.com
        first_name: ''
        groups: []
        is_active: true
        is_staff: true
        is_superuser: true
        last_login: 2014-12-08 09:23:45.199983+00:00
        last_name: ''
        password: pbkdf2_sha256\$12000\$yxB95qHh91x5\$oYW0Jrsb8jLGVo0tKypOPRap/wr+n+3TjkOP6cT9G4o=
        user_permissions: []
        username: admin
      model: auth.user
      pk: 1
    - fields: {created: '2014-12-12 12:00:00+00:00', key: admin_api_key, user: 1}
      model: tastypie.apikey
      pk: 1
    EOF

Then, run the container as follows:

    sudo docker run -v /var/tmp/data.yaml:/data/data.yaml -p 80:80 -d -t allegro/vaas

You can now start populating VaaS database with data, as described in [VaaS API](../documentation/api.md)

Integration
===========

VaaS is ready to authorize users via ldap server. It requires only one configuration file to define all settings required by ldap. You can find more details about VaaS configuration [here](../quick-start/production.md)

Sample configuration file
-------------------------

ldap.yml:

    AUTH_LDAP_SERVER_URI: ldap://your-ldap.com:3268
    AUTH_LDAP_BIND_DN: COMPANY\ldapbind_vaas
    AUTH_LDAP_BIND_PASSWORD: 'password'
    AUTH_LDAP_USER_SEARCH_BASE: DC=yourcompany,DC=internal
    AUTH_LDAP_USER_USERNAME_ATTR: sAMAccountName
    AUTH_LDAP_USER_SEARCH_FILTER: (&(objectClass=*)({0}=%(user)s))
    AUTH_LDAP_USER_FILTER: |-
      '(|(memberOf=CN=_gr_common_access,OU=Other Resources,OU=Company-Restricted))'
    AUTH_LDAP_ALWAYS_UPDATE_USER: True
    AUTH_LDAP_USER_ATTR_MAP:
      first_name: givenName
      last_name: sn
      email: mail
    AUTH_LDAP_GROUP_SEARCH:
      - DC=yourcompany,DC=internal
      - (objectClass=group)
    AUTH_LDAP_GROUP_MAPPING:
      CN=_gr_vaas,OU=POL,OU=Corp-Restricted,DC=yourcompany,DC=internal: active
      CN=_gr_vaas_admin,OU=POL,OU=Corp-Restricted,DC=yourcompany,DC=internal: staff
      CN=_gr_vaas_superuser,OU=POL,OU=Corp-Restricted,DC=yourcompany,DC=internal: superuser
      CN=_gr_vaas_core,OU=POL,OU=Corp-Restricted,DC=yourcompany,DC=internal: has-all-rights
    AUTH_LDAP_MIRROR_GROUPS: False
    AUTH_LDAP_GROUP_TYPE: cn
    AUTH_LDAP_ALWAYS_UPDATE_USER: True
    AUTHENTICATION_BACKENDS:
      - django_auth_ldap.backend.LDAPBackend
      - django.contrib.auth.backends.ModelBackend
    AUTH_LDAP_MIRROR_GROUPS: True

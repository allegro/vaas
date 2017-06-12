# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from vaas.configuration.loader import YamlConfigLoader

ldap_config = YamlConfigLoader().get_config_tree('ldap.yml')
if ldap_config:
    for key, value in ldap_config.iteritems():
        globals()[key] = value

    import ldap
    from django_auth_ldap.config import LDAPSearch

    from vaas.external.ldap_config import MappedGroupOfNamesType

    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail"
    }

    AUTH_LDAP_GROUP_TYPE = MappedGroupOfNamesType(name_attr=AUTH_LDAP_GROUP_TYPE)
    AUTH_LDAP_USER_SEARCH_FILTER = AUTH_LDAP_USER_SEARCH_FILTER.format(AUTH_LDAP_USER_USERNAME_ATTR)
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        AUTH_LDAP_USER_SEARCH_BASE, ldap.SCOPE_SUBTREE, AUTH_LDAP_USER_SEARCH_FILTER
    )
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        AUTH_LDAP_GROUP_SEARCH[0], ldap.SCOPE_SUBTREE, AUTH_LDAP_GROUP_SEARCH[1]
    )

    import django
    django.setup()
    import vaas.external.ldap  # noqa

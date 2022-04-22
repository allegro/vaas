# -*- coding: utf-8 -*-
import os
from __future__ import unicode_literals, absolute_import

from vaas.configuration.loader import YamlConfigLoader
from vaas.settings.base import env, serialize

ldap_config = YamlConfigLoader(['/configuration']).get_config_tree('ldap.yaml')
if ldap_config:
    os.environ.update({k.upper(): serialize(v) for k, v in ldap_config.items()})

    import ldap
    from django_auth_ldap.config import LDAPSearch

    from vaas.external.ldap_config import MappedGroupOfNamesType

    AUTH_LDAP_USER_ATTR_MAP = {
        "first_name": "givenName",
        "last_name": "sn",
        "email": "mail"
    }

    AUTH_LDAP_GROUP_SEARCH = env.json('AUTH_LDAP_GROUP_SEARCH', default=['', ''])

    AUTH_LDAP_GROUP_TYPE = MappedGroupOfNamesType(name_attr=env.str('AUTH_LDAP_GROUP_TYPE', default=''))
    AUTH_LDAP_USER_SEARCH_FILTER = env.str('AUTH_LDAP_USER_SEARCH_FILTER', default='{}').format(
        env.str('AUTH_LDAP_USER_USERNAME_ATTR', default='user_attr'))
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        env.str('AUTH_LDAP_USER_SEARCH_BASE'), ldap.SCOPE_SUBTREE, AUTH_LDAP_USER_SEARCH_FILTER
    )
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
        AUTH_LDAP_GROUP_SEARCH[0], ldap.SCOPE_SUBTREE, AUTH_LDAP_GROUP_SEARCH[1]
    )

    import django
    django.setup()
    import vaas.external.ldap  # noqa

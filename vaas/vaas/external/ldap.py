# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging


logger = logging.getLogger(__name__)
try:
    from django_auth_ldap.backend import (
        populate_user,
        LDAPSettings,
        populate_user_profile
    )
except ImportError:
    logger.debug("django_auth_ldap package not provided")
else:
    from django.dispatch import receiver
    from django.conf import settings

    LDAPSettings.defaults['GROUP_MAPPING'] = {}

    @receiver(populate_user)
    def staff_superuser_populate(sender, user, ldap_user, **kwargs):
        user.is_superuser = 'superuser' in ldap_user.group_names
        user.is_staff = 'staff' in ldap_user.group_names
        user.is_active = 'active' in ldap_user.group_names

    @receiver(populate_user_profile)
    def manager_attribute_populate(sender, profile, ldap_user, **kwargs):
        try:
            profile_map = settings.AUTH_LDAP_PROFILE_ATTR_MAP
        except AttributeError:
            profile_map = {}
        if 'manager' in profile_map:
            if profile_map['manager'] in ldap_user.attrs:
                manager_ref = ldap_user.attrs[profile_map['manager']][0]
                # CN=John Smith,OU=TOR,OU=Corp-Users,DC=mydomain,DC=internal
                cn = manager_ref.split(',')[0][3:]
                profile.manager = cn

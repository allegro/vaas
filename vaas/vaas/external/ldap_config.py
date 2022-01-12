# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from django_auth_ldap.config import ActiveDirectoryGroupType
from django.utils.encoding import force_unicode

# Add default value to LDAPSetting dict. It will be replaced by
# django_auth_ldap with value in settings.py and visible for each
# ldap_user.
GROUP_CACHE_TIMEOUT = 1200


class MappedGroupOfNamesType(ActiveDirectoryGroupType):

    """Provide group mappings described in project settings."""

    def _get_group(self, group_dn, ldap_user, group_search):
        base_dn = group_search.base_dn
        group_search.base_dn = force_unicode(group_dn)
        group = group_search.execute(ldap_user.connection)[0]
        group_search.base_dn = base_dn
        return group

    def user_groups(self, ldap_user, group_search):
        """Get groups which user belongs to."""
        self._ldap_groups = ldap_user.settings.GROUP_MAPPING
        group_map = []

        try:
            group_dns = ldap_user.attrs['memberOf']
        except KeyError:
            group_dns = []
        # if mapping defined then filter groups to mapped only
        if self._ldap_groups:
            group_dns = filter(lambda x: x in self._ldap_groups, group_dns)
        for group_dn in group_dns:
            group = self._get_group(group_dn, ldap_user, group_search)
            group_map.append(group)

        return group_map

    def group_name_from_info(self, group_info):
        """Map ldap group names into vaas names if mapping defined."""
        if self._ldap_groups:
            for dn in group_info[1]['distinguishedname']:
                mapped = self._ldap_groups.get(dn)
                if mapped:
                    return mapped
        # return original name if mapping not defined
        else:
            return super(
                MappedGroupOfNamesType,
                self
            ).group_name_from_info(group_info)

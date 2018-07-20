import re
from vaas.cluster.models import Dc


class BaseHelpers:

    @staticmethod
    def dynamic_regex_with_datacenters():
        dcs = Dc.objects.all()
        dcs_regex_pattern = ''
        for idx, dc in enumerate(dcs):
            dcs_regex_pattern += '{}'.format(dc.symbol)
            if not idx == len(dcs) - 1:
                dcs_regex_pattern += '|'
        return re.compile("(\d+)_({})".format(dcs_regex_pattern))

from typing import List

from vaas.cluster.models import DomainMapping, LogicalCluster


class MappingProvider:
    def __init__(self, mappings: List[DomainMapping]):
        self.mappings = {
            'static': [],
            'dynamic': [],
        }
        for m in mappings:
            self.mappings[m.type].append(m)

    def provide_related_domains(self, cluster: LogicalCluster) -> List[str]:
        result = {m.domain for m in cluster.domainmapping_set.filter(type='static')}
        for m in self.mappings['dynamic']:
            if m.is_cluster_related_by_labels(cluster):
                result.add(m.domain)
        return sorted(list(result))

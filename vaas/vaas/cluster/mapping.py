from typing import List

from vaas.cluster.models import DomainMapping, LogicalCluster


class MappingProvider:
    def __init__(self, mappings: List[DomainMapping]):
        self.mappings = {
            'static': [],
            'dynamic': [],
        }
        for m in mappings:
            self.mappings[m.type].append(
                {
                    'cluster_keys': [c.pk for c in m.clusters.all()],
                    'mapping': m
                }
            )

    def provide_related_domains(self, cluster: LogicalCluster) -> List[str]:
        print(cluster.name)
        result = {m['mapping'].domain for m in self.mappings['static'] if cluster.pk in m['cluster_keys']}
        cluster_labels = set(list(cluster.parsed_labels().keys()))
        for m in self.mappings['dynamic']:
            if m['mapping'].has_matching_labels(cluster_labels):
                result.add(m['mapping'].domain)
        return sorted(list(result))

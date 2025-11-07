from typing import List

from vaas.cluster.models import DomainMapping, LogicalCluster


class MappingProvider:
    def __init__(self, mappings: List[DomainMapping]):
        self.mappings: dict[str, list[dict]] = {
            'static': [],
            'static_regex': [],
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
        all_static_mappings = self.mappings['static'] + self.mappings['static_regex']
        result = {m['mapping'].domain for m in all_static_mappings if cluster.pk in m['cluster_keys']}
        cluster_labels = set(list(cluster.parsed_labels().keys()))
        for m in self.mappings['dynamic']:
            if m['mapping'].has_matching_labels(cluster_labels):
                result.add(m['mapping'].domain)
        return sorted(list(result))

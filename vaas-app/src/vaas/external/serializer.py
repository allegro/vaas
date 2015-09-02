import json
from django.core.serializers.json import DjangoJSONEncoder
from tastypie.serializers import Serializer


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)

        return json.dumps(
            data, cls=DjangoJSONEncoder, sort_keys=True, ensure_ascii=False, indent=self.json_indent
        )

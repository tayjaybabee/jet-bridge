from jet_bridge_base import fields
from jet_bridge_base.messages import get_handler
from jet_bridge_base.serializers.serializer import Serializer


class MessageSerializer(Serializer):
    name = fields.CharField()
    params = fields.JSONField(required=False)

    def save(self):
        if handler := get_handler(self.validated_data['name']):
            return handler(self.validated_data['name'], self.validated_data.get('params', {}))
        else:
            return

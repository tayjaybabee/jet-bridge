from jet_bridge_base.db import get_connection_tunnel
from jet_bridge_base.db_types import discover_connection
from jet_bridge_base.exceptions.validation_error import ValidationError
from jet_bridge_base.permissions import HasProjectPermissions
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.utils.conf import get_conf
from jet_bridge_base.views.base.api import BaseAPIView


class DiscoverConnectionView(BaseAPIView):
    permission_classes = (HasProjectPermissions,)

    def required_project_permission(self, request):
        return {
            'permission_type': 'project',
            'permission_object': 'project_customization',
            'permission_actions': ''
        }

    def get(self, request, *args, **kwargs):
        conf = get_conf(request)

        try:
            tunnel = get_connection_tunnel(conf)
            status = discover_connection(conf, tunnel)

            return JSONResponse({
                'status': status
            })
        except Exception as e:
            raise ValidationError(str(e))

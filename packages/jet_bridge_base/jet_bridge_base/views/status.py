import time

from jet_bridge_base.configuration import configuration
from jet_bridge_base.db import connections, pending_connections
from jet_bridge_base.permissions import AdministratorPermissions
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.utils.classes import issubclass_safe
from jet_bridge_base.utils.graphql import ModelFiltersType, ModelFiltersFieldType, ModelFiltersRelationshipType, \
    ModelLookupsType, ModelLookupsFieldType, ModelLookupsRelationshipType
from jet_bridge_base.views.base.api import BaseAPIView
from sqlalchemy import inspect


class StatusView(BaseAPIView):
    permission_classes = (AdministratorPermissions,)

    def map_connection_graphql_schema(self, schema):
        if not schema:
            return {'status': 'no_schema'}

        if not (instance := schema.get('instance')):
            return {'status': 'pending'}
        types_count = len(instance._type_map.values())
        filters_count = 0
        filters_fields_count = 0
        filters_relationships_count = 0
        lookups_count = 0
        lookups_fields_count = 0
        lookups_relationships_count = 0
        get_schema_time = schema.get('get_schema_time')

        for item in instance._type_map.values():
            if not hasattr(item, 'graphene_type'):
                continue

            if issubclass_safe(item.graphene_type, ModelFiltersType):
                filters_count += 1
            elif issubclass_safe(item.graphene_type, ModelFiltersFieldType):
                filters_fields_count += 1
            elif issubclass_safe(item.graphene_type, ModelFiltersRelationshipType):
                filters_relationships_count += 1
            elif issubclass_safe(item.graphene_type, ModelLookupsType):
                lookups_count += 1
            elif issubclass_safe(item.graphene_type, ModelLookupsFieldType):
                lookups_fields_count += 1
            elif issubclass_safe(item.graphene_type, ModelLookupsRelationshipType):
                lookups_relationships_count += 1

        return {
            'status': 'ok',
            'types': types_count,
            'filters': filters_count,
            'filters_fields': filters_fields_count,
            'filters_relationships': filters_relationships_count,
            'lookups': lookups_count,
            'lookups_fields': lookups_fields_count,
            'lookups_relationships': lookups_relationships_count,
            'get_schema_time': get_schema_time
        }

    def map_tunnel(self, tunnel):
        if not tunnel:
            return

        return {
            'is_active': tunnel.is_active,
            'local_address': f'{tunnel.local_bind_host}:{tunnel.local_bind_port}',
            'remote_address': f'{tunnel.ssh_host}:{tunnel.ssh_port}',
        }

    def map_connection(self, connection):
        cache = connection['cache']
        MappedBase = connection['MappedBase']
        column_count = 0
        relationships_count = 0

        for Model in MappedBase.classes:
            mapper = inspect(Model)
            column_count += len(mapper.columns)
            relationships_count += len(mapper.relationships)

        graphql_schema = self.map_connection_graphql_schema(cache.get('graphql_schema'))
        graphql_schema_draft = self.map_connection_graphql_schema(cache.get('graphql_schema_draft'))
        tunnel = self.map_tunnel(connection.get('tunnel'))

        return {
            'name': connection['name'],
            'project': connection.get('project'),
            'token': connection.get('token'),
            'tables': len(MappedBase.classes),
            'columns': column_count,
            'relationships': relationships_count,
            'graphql_schema': graphql_schema,
            'graphql_schema_draft': graphql_schema_draft,
            'init_start': connection.get('init_start'),
            'connect_time': connection.get('connect_time'),
            'reflect_time': connection.get('reflect_time'),
            'tunnel': tunnel
        }

    def map_pending_connection(self, pending_connection):
        tunnel = self.map_tunnel(pending_connection.get('tunnel'))

        return {
            'name': pending_connection['name'],
            'project': pending_connection.get('project'),
            'token': pending_connection.get('token'),
            'init_start': pending_connection.get('init_start'),
            'tables_processed': pending_connection.get('tables_processed'),
            'tables_total': pending_connection.get('tables_total'),
            'tunnel': tunnel
        }

    def get(self, request, *args, **kwargs):
        now = time.time()
        uptime = round(now - configuration.init_time)

        return JSONResponse({
            'total_pending_connections': len(pending_connections.keys()),
            'total_connections': len(connections.keys()),
            'pending_connections': map(lambda x: self.map_pending_connection(x), pending_connections.values()),
            'connections': map(lambda x: self.map_connection(x), connections.values()),
            'uptime': uptime
        })

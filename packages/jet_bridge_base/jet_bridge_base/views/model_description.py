import json
import re

from jet_bridge_base.models.model_relation_override import ModelRelationOverrideModel
from jet_bridge_base.store import store
from jet_bridge_base.utils.relations import relationship_direction_to_str
from sqlalchemy import inspect, String, Enum, Date
from sqlalchemy.orm import MANYTOONE, ONETOMANY
from sqlalchemy.sql.elements import TextClause

from jet_bridge_base.db import get_mapped_base, get_request_connection
from jet_bridge_base.models import data_types
from jet_bridge_base.permissions import HasProjectPermissions
from jet_bridge_base.responses.json import JSONResponse
from jet_bridge_base.serializers.model_description import ModelDescriptionSerializer
from jet_bridge_base.utils.common import merge, get_set_first
from jet_bridge_base.utils.db_types import sql_to_map_type, sql_to_db_type
from jet_bridge_base.views.base.api import APIView


def is_column_optional(column):
    return column.autoincrement or column.default or column.server_default or column.nullable


def map_column_default(column):
    if column.server_default is None:
        return
    if hasattr(column.server_default, 'arg') and isinstance(column.server_default.arg, TextClause):
        value = column.server_default.arg.text
        if value.lower() == 'now()':
            return {
                'default_type': 'datetime_now'
            }
        elif value.lower() == 'uuid_generate_v4()':
            return {
                'default_type': 'uuid'
            }
        elif value.lower() == 'true':
            return {
                'default_type': 'value',
                'default_value': True
            }
        elif value.lower() == 'false':
            return {
                'default_type': 'value',
                'default_value': False
            }

        if value_regex := re.search("^'(?P<value>.+)'::(?P<type>.+)$", value):
            match = value_regex.groupdict()
            return {
                'default_type': 'value',
                'default_value': match['value']
            }

        if nextval_regex := re.search("^nextval\((?P<value>.+)\)$", value):
            match = nextval_regex.groupdict()
            return {
                'default_type': 'sequence',
                'default_value': match['value']
            }


def map_column(column, editable):
    params = {}
    data_source_field = None
    data_source_name = None
    data_source_params = None
    data_source_order_after = None
    data_source_hidden = None

    try:
        map_type = sql_to_map_type(column.type)
    except:
        map_type = 'NullType'

    try:
        db_type = sql_to_db_type(column.type)
    except:
        db_type = 'NullType'

    if column.foreign_keys:
        foreign_key = next(iter(column.foreign_keys))
        map_type = data_types.FOREIGN_KEY
        params['related_model'] = {
            'model': foreign_key.column.table.name
        }

        table_primary_keys = foreign_key.column.table.primary_key.columns.keys()
        table_primary_key = table_primary_keys[0] if len(table_primary_keys) > 0 else None

        if not table_primary_key or foreign_key.column.name != table_primary_key:
            params['custom_primary_key'] = foreign_key.column.name

    if isinstance(column.type, Date):
        params['date'] = True
        params['time'] = False

    if isinstance(column.type, Enum):
        params['options'] = map(lambda x: {'name': x, 'value': x}, column.type.enums)

    if isinstance(column.type, String):
        params['length'] = column.type.length

    optional = is_column_optional(column)

    if column.comment:
        try:
            data_source_meta = json.loads(column.comment)

            if not isinstance(data_source_meta, dict):
                raise ValueError

            meta_field = data_source_meta.get('field')
            meta_name = data_source_meta.get('name')
            meta_params = data_source_meta.get('params')
            meta_order_after = data_source_meta.get('order_after')
            meta_hidden = data_source_meta.get('hidden')

            if meta_field is not None:
                data_source_field = meta_field
            if meta_name is not None:
                data_source_name = meta_name
            if meta_params is not None and isinstance(meta_params, dict):
                data_source_params = meta_params
            if meta_order_after is not None:
                data_source_order_after = meta_order_after
            if meta_hidden is not None:
                data_source_hidden = meta_hidden
        except ValueError:
            pass

    result = {
        'name': column.name,
        'db_column': column.name,
        'field': map_type,
        'db_field': db_type,
        'filterable': True,
        'required': not optional,
        'null': column.nullable,
        'editable': editable,
        'params': params,
        'data_source_field': data_source_field,
        'data_source_name': data_source_name,
        'data_source_params': data_source_params,
        'data_source_order_after': data_source_order_after,
        'data_source_hidden': data_source_hidden
    }

    if server_default := map_column_default(column):
        result['default_type'] = server_default['default_type']
        if 'default_value' in server_default:
            result['default_value'] = server_default['default_value']

    return result


def map_relationship(relationship):
    local_field = get_set_first(relationship.local_columns)
    related_field = get_set_first(relationship.remote_side)
    direction = relationship_direction_to_str(relationship.direction)

    return {
        'name': relationship.key,
        'direction': direction,
        'local_field': local_field.name,
        'related_model': relationship.target.name,
        'related_field': related_field.name,
    }


def map_relationship_override(override):
    return {
        'name': override.name,
        'direction': override.direction,
        'local_field': override.local_field,
        'related_model': override.related_model,
        'related_field': override.related_field,
    }


# def map_relation(relation):
#     field = None
#
#     if relation.direction == ONETOMANY:
#         field = 'ManyToOneRel'
#
#     return {
#         'name': relation.key,
#         'related_model': {
#             'model': relation.table.name
#         },
#         'field': field,
#         'related_model_field': relation.primaryjoin.right.name,
#         'through': None
#     }
#
# def table_relations(mapper):
#     return list(map(map_relation, filter(lambda x: x.direction == ONETOMANY and hasattr(x, 'table'), mapper.relationships)))
#
# def table_m2m_relations(mapper):
#     result = []
#     name = mapper.selectable.name
#
#     for relation in mapper.relationships:
#         if relation.direction != ONETOMANY or not hasattr(relation, 'table'):
#             continue
#
#         m2m_relationships = relation.mapper.relationships.values()
#
#         if len(m2m_relationships) != 2:
#             continue
#
#         if len(relation.table.columns) > 5:
#             continue
#
#         self_relationship = m2m_relationships[1] if m2m_relationships[1].table.name == name else \
#         m2m_relationships[0]
#         other_relationship = m2m_relationships[0] if self_relationship == m2m_relationships[1] else \
#         m2m_relationships[1]
#
#         result.append({
#             'name': 'M2M {} {}'.format(self_relationship.table.name, other_relationship.table.name),
#             'related_model': {
#                 'model': other_relationship.table.name
#             },
#             'field': 'ManyToManyField',
#             'related_model_field': self_relationship.table.name,
#             'through': {'model': relation.table.name}
#         })
#
#     return result

def map_table(cls, relationships_overrides, hidden):
    mapper = inspect(cls)
    table = mapper.tables[0]
    name = mapper.selectable.name
    primary_key = mapper.primary_key[0]
    primary_key_auto = getattr(table, '__jet_auto_pk__', False) if table is not None else None
    non_editable = []
    model_relationships_overrides = relationships_overrides.get(name)

    from jet_bridge_base.configuration import configuration
    additional = configuration.get_model_description(name)

    data_source_name = None
    data_source_name_plural = None
    data_source_order_after = None
    data_source_hidden = None

    if table.comment:
        try:
            data_source_meta = json.loads(table.comment)

            if not isinstance(data_source_meta, dict):
                raise ValueError

            meta_name = data_source_meta.get('name')
            meta_name_plural = data_source_meta.get('name_plural')
            meta_order_after = data_source_meta.get('order_after')
            meta_hidden = data_source_meta.get('hidden')

            if meta_name is not None:
                data_source_name = meta_name
            if meta_name_plural is not None:
                data_source_name_plural = meta_name_plural
            if meta_order_after is not None:
                data_source_order_after = meta_order_after
            if meta_hidden is not None:
                data_source_hidden = meta_hidden
        except ValueError:
            pass

    result = {
        'model': name,
        'db_table': name,
        'fields': list(map(lambda x: map_column(x, x.name not in non_editable), mapper.columns)),
        'relations': list(map(lambda x: map_relationship(x), filter(lambda x: x.direction in [MANYTOONE, ONETOMANY], mapper.relationships))),
        'relation_overrides': list(map(lambda x: map_relationship_override(x), model_relationships_overrides)) if model_relationships_overrides else None,
        'hidden': name in hidden or name in configuration.get_hidden_model_description(),
        # 'relations': table_relations(mapper) + table_m2m_relations(mapper),
        'primary_key_field': primary_key.name if primary_key is not None else None,
        'primary_key_auto': primary_key_auto,
        'data_source_name': data_source_name,
        'data_source_name_plural': data_source_name_plural,
        'data_source_order_after': data_source_order_after,
        'data_source_hidden': data_source_hidden
    }

    if additional:
        result = merge(result, additional)

    return result


class ModelDescriptionView(APIView):
    serializer_class = ModelDescriptionSerializer
    permission_classes = (HasProjectPermissions,)

    def get_queryset(self, request):
        hidden = ['__jet__token']
        MappedBase = get_mapped_base(request)
        relationships_overrides = {}
        draft = bool(request.get_argument('draft', False))

        if store.is_ok():
            connection = get_request_connection(request)

            with store.session() as session:
                overrides = (
                    session.query(ModelRelationOverrideModel)
                    .filter(
                        ModelRelationOverrideModel.connection_id
                        == connection['id'],
                        True,
                    )
                    .all()
                )

                for override in overrides:
                    if override.model not in relationships_overrides:
                        relationships_overrides[override.model] = []
                    relationships_overrides[override.model].append(override)

        return list(map(lambda x: map_table(x, relationships_overrides, hidden), MappedBase.classes))

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset(request)
        serializer = self.serializer_class(instance=queryset, many=True)
        return JSONResponse(serializer.representation_data)

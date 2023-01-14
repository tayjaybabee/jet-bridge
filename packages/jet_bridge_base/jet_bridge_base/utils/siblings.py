from sqlalchemy import inspect, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import load_only

from jet_bridge_base.utils.queryset import apply_default_ordering, queryset_count_optimized, get_queryset_order_by


def get_row_number(Model, queryset, instance):
    mapper = inspect(Model)
    pk = mapper.primary_key[0].name
    ordering = get_queryset_order_by(queryset)

    subqquery = queryset.with_entities(
        mapper.primary_key[0].label('__inner__pk'),
        func.row_number().over(order_by=ordering).label('__inner__row')
    ).subquery()

    try:
        rest = queryset.session.query(subqquery.c.__inner__row).filter(subqquery.c.__inner__pk == getattr(instance, pk))
        return rest.scalar()
    except SQLAlchemyError:
        queryset.session.rollback()
        raise


def get_row_siblings(Model, queryset, row_number):
    mapper = inspect(Model)
    pk = mapper.primary_key[0].name

    has_prev = row_number > 1
    offset = row_number - 2 if has_prev else row_number - 1
    limit = 3 if has_prev else 2

    try:
        rows = queryset.options(load_only(pk)).limit(limit).offset(offset).all()
    except SQLAlchemyError:
        queryset.session.rollback()
        raise

    next_index = 2 if has_prev else 1
    if next_index >= len(rows):
        next_index = None

    prev_index = 0 if has_prev else None
    def map_row(row):
        return dict(((pk, getattr(row, pk)),))

    return {
        'prev': map_row(rows[prev_index]) if prev_index is not None else None,
        'next': map_row(rows[next_index]) if next_index is not None else None
    }


def get_model_siblings(request, Model, instance, queryset):
    count = queryset_count_optimized(request, queryset)

    if count > 10000:
        return {}

    queryset = apply_default_ordering(Model, queryset)
    row_number = get_row_number(Model, queryset, instance)

    return get_row_siblings(Model, queryset, row_number) if row_number else {}

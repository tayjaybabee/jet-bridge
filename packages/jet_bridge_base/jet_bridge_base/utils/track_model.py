import json

import requests

from jet_bridge_base import settings
from jet_bridge_base.encoders import JSONEncoder
from jet_bridge_base.utils.async_exec import as_future


def track_model(request, model, action, uid, model_data):
    if not settings.TRACK_MODELS_ENDPOINT:
        return

    if request.project is None or request.environment is None or request.resource_token is None:
        return

    url = f'{settings.TRACK_MODELS_ENDPOINT}/model_change'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'project': request.project,
        'environment': request.environment,
        'resource_token': request.resource_token,
        'model': model,
        'action': action,
        'data': model_data
    }

    if uid is not None:
        data['id'] = uid

    if settings.TRACK_MODELS_AUTH:
        headers['Authorization'] = settings.TRACK_MODELS_AUTH

    data_str = json.dumps(data, cls=JSONEncoder)
    requests.post(url, data=data_str, headers=headers)


def track_model_async(request, model, action, uid, data):
    if not settings.TRACK_MODELS_ENDPOINT:
        return

    try:
        import asyncio
    except:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    as_future(lambda: track_model(request, model, action, uid, data))

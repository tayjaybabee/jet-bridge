import requests
from requests import RequestException

from jet_bridge_base import settings
from jet_bridge_base.configuration import configuration
from jet_bridge_base.logger import logger


def api_method_url(method):
    return f'{settings.API_BASE_URL}/{method}'


def is_project_token_activated(project_token):
    if not project_token:
        return False

    url = api_method_url(f'project_tokens/{project_token}/')
    headers = {
        'User-Agent': f'{configuration.get_type()} v{configuration.get_version()}'
    }

    r = requests.request('GET', url, headers=headers)
    success = 200 <= r.status_code < 300

    if not success:
        return False

    result = r.json()

    return bool(result.get('activated'))


def is_resource_token_activated(project_name, resource_token):
    if not project_name or not resource_token:
        return False

    url = api_method_url('check_resource_token/')
    headers = {
        'User-Agent': f'{configuration.get_type()} v{configuration.get_version()}'
    }
    data = {
        'project': project_name,
        'token': resource_token
    }

    r = requests.request('POST', url, headers=headers, data=data)

    if 200 <= r.status_code < 300:
        result = r.json()
        return bool(result.get('activated'))
    elif 400 <= r.status_code < 500:
        return False
    else:
        raise RequestException()


def project_auth(token, project_token, permission=None, params=None):
    if not project_token:
        return {
            'result': False
        }

    url = api_method_url('project_auth/')
    data = {
        'project_token': project_token,
        'token': token
    }
    headers = {
        'User-Agent': f'{configuration.get_type()} v{configuration.get_version()}'
    }

    if permission:
        data |= permission

    if params and 'project_child' in params:
        data['project_child'] = params['project_child']

    r = requests.request('POST', url, data=data, headers=headers)
    success = 200 <= r.status_code < 300

    if not success:
        logger.error('Project Auth request error: %d %s %s', r.status_code, r.reason, r.text)
        return {
            'result': False
        }

    result = r.json()

    if result.get('access_disabled'):
        return {
            'result': False,
            'warning': result.get('warning')
        }

    return {
        'result': True,
        'warning': result.get('warning')
    }


def get_resource_secret_tokens(project, resource, token):
    if not token:
        return []

    url = api_method_url(f'projects/{project}/resources/{resource}/secret_tokens/')
    headers = {
        'Authorization': f'ProjectToken {token}',
        'User-Agent': f'{configuration.get_type()} v{configuration.get_version()}',
    }

    r = requests.request('GET', url, headers=headers)
    success = 200 <= r.status_code < 300

    return r.json() if success else []


def get_secret_tokens(project_name, environment_name, resource, draft, token, user_token):
    if not token:
        return []

    if environment_name:
        method_url = f'projects/{project_name}/{environment_name}/secret_tokens/'
    else:
        method_url = f'projects/{project_name}/secret_tokens/'

    url = api_method_url(method_url)
    headers = {
        'Authorization': f'ProjectToken {token}',
        'User-Agent': f'{configuration.get_type()} v{configuration.get_version()}',
    }
    data = {
        'resource': resource,
        'user_token': user_token
    }

    if draft:
        data['draft'] = 1

    r = requests.request('POST', url, headers=headers, data=data)
    success = 200 <= r.status_code < 300

    return r.json() if success else []

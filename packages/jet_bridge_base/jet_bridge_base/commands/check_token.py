import webbrowser

from requests import RequestException

from jet_bridge_base import settings
from jet_bridge_base.utils.backend import is_resource_token_activated
from jet_bridge_base.logger import logger


def check_token_command(api_url):
    try:
        if not is_resource_token_activated(settings.PROJECT, settings.TOKEN):
            logger.warning('[!] Your resource token is not activated')
            logger.warning(f'[!] Project: {settings.PROJECT}')
            logger.warning(f'[!] Token: {settings.TOKEN}')

            if settings.DATABASE_ENGINE != 'none' and settings.AUTO_OPEN_REGISTER and api_url.startswith('http'):
                register_url = f'{api_url}register/'

                if settings.TOKEN:
                    register_url += f'?token={settings.TOKEN}'

                if webbrowser.open(register_url):
                    logger.warning(
                        f'[!] Activation page was opened in your browser - {register_url}'
                    )
            else:
                register_url = f'{api_url}register/'
                logger.warning(f'[!] Go to {register_url} to activate it')
    except RequestException:
        logger.error('[!] Can\'t connect to Jet Admin API')
        logger.error('[!] Token verification failed')

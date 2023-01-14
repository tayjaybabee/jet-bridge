import os
from datetime import datetime
import sys

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from jet_bridge_base import configuration
from jet_bridge.configuration import JetBridgeConfiguration

conf = JetBridgeConfiguration()
configuration.set_configuration(conf)

from jet_bridge_base.commands.check_token import check_token_command
from jet_bridge_base.db import connect_database_from_settings
from jet_bridge_base.logger import logger

from jet_bridge import settings, VERSION
from jet_bridge.settings import missing_options, required_options_without_default


def main():
    args = os.environ['ARGS'].split(' ') if 'ARGS' in os.environ else sys.argv[1:]
    logger.info(datetime.now().strftime('%B %d, %Y - %H:%M:%S %Z'))
    logger.info(f'Jet Bridge version {VERSION}')

    if (len(args) >= 1 and args[0] == 'config') or missing_options == required_options_without_default:
        from jet_bridge.utils.create_config import create_config
        create_config(missing_options == required_options_without_default)
        return
    elif missing_options and len(missing_options) < len(required_options_without_default):
        logger.info(
            f"Required options are not specified: {', '.join(missing_options)}"
        )
        return

    address = 'localhost' if settings.ADDRESS == '0.0.0.0' else settings.ADDRESS
    url = f'http://{address}:{settings.PORT}/'
    api_url = f'{url}api/'

    if len(args) >= 1 and args[0] == 'check_token':
        check_token_command(api_url)
        return

    connect_database_from_settings()

    from jet_bridge.app import make_app

    app = make_app()
    workers = 1 if settings.DEBUG else settings.WORKERS
    server = HTTPServer(app)
    server.bind(settings.PORT, settings.ADDRESS)
    server.start(workers)

    if settings.WORKERS > 1 and settings.DEBUG:
        logger.warning('Multiple workers are not supported in DEBUG mode')

    logger.info(f'Starting server at {url} (WORKERS: {workers})')

    if settings.DEBUG:
        logger.warning('Server is running in DEBUG mode')

    logger.info('Quit the server with CONTROL-C')

    check_token_command(api_url)

    IOLoop.current().start()

if __name__ == '__main__':
    main()

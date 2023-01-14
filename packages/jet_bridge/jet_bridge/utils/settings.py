import os
from six.moves import configparser

from tornado.options import Error


def parse_environment(self, final=True):
    for name in os.environ:
        normalized = self._normalize_name(name)
        normalized = normalized.lower()
        if normalized in self._options:
            option = self._options[normalized]
            if option.multiple and not isinstance(
                os.environ[name], (list, str)
            ):
                raise Error("Option %r is required to be a list of %s "
                            "or a comma-separated string" %
                            (option.name, option.type.__name__))

            if type(os.environ[name]) == str and option.type != str:
                option.parse(os.environ[name])
            else:
                option.set(os.environ[name])


def parse_config_file(self, path, section, final=True):
    try:
        config_parser = configparser.ConfigParser(interpolation=None)
    except TypeError:
        config_parser = configparser.ConfigParser()

    if not config_parser.read(path):
        raise IOError(f'Config file at path "{path}" not found')

    try:
        config = config_parser.items(section)
    except KeyError:
        raise ValueError(f'Config file does not have [{section}] section]')

    for (name, value) in config:
        normalized = self._normalize_name(name)
        normalized = normalized.lower()
        if normalized in self._options:
            option = self._options[normalized]
            if option.multiple and not isinstance(value, (list, str)):
                raise Error("Option %r is required to be a list of %s "
                            "or a comma-separated string" %
                            (option.name, option.type.__name__))

            if type(value) == str and option.type != str:
                option.parse(value)
            else:
                option.set(value)

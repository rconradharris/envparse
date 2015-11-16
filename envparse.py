"""
envparse is a simple utility to parse environment variables.
"""
from __future__ import unicode_literals
import inspect
import json as pyjson
import logging
import os
import re
import shlex
import warnings
try:
    import urllib.parse as urlparse
except ImportError:
    # Python 2
    import urlparse


__version__ = '0.2.0'


logger = logging.getLogger(__file__)


class ConfigurationError(Exception):
    pass


# Cannot rely on None since it may be desired as a return value.
NOTSET = type(str('NoValue'), (object,), {})


def shortcut(cast):
    def method(self, var, **kwargs):
        return self.__call__(var, cast=cast, **kwargs)
    return method


class Env(object):
    """
    Lookup and cast environment variables with optional schema.

    Usage:::

        env = Env()
        env('foo')
        env.bool('bar')

        # Create env with a schema
        env = Env(MAIL_ENABLED=bool, SMTP_LOGIN=(str, 'DEFAULT'))
        if env('MAIL_ENABLED'):
            ...
    """
    BOOLEAN_TRUE_STRINGS = ('true', 'on', 'ok', 'y', 'yes', '1')

    def __init__(self, **schema):
        self.schema = schema

    def __call__(self, var, default=NOTSET, cast=None, subcast=None,
                 force=False, preprocessor=None, postprocessor=None):
        """
        Return value for given environment variable.

        :param var: Name of variable.
        :param default: If var not present in environ, return this instead.
        :param cast: Type or callable to cast return value as.
        :param subcast: Subtype or callable to cast return values as (used for
                        nested structures).
        :param force: force to cast to type even if default is set.
        :param preprocessor: callable to run on pre-casted value.
        :param postprocessor: callable to run on casted value.

        :returns: Value from environment or default (if set).
        """
        logger.debug("Get '%s' casted as '%s'/'%s' with default '%s'", var,
                     cast, subcast, default)

        if var in self.schema:
            params = self.schema[var]
            if isinstance(params, dict):
                if cast is None:
                    cast = params.get('cast', cast)
                if subcast is None:
                    subcast = params.get('subcast', subcast)
                if default == NOTSET:
                    default = params.get('default', default)
            else:
                if cast is None:
                    cast = params
        # Default cast is `str` if it is not specified. Most types will be
        # implicitly strings so reduces having to specify.
        cast = str if cast is None else cast

        try:
            value = os.environ[var]
        except KeyError:
            if default is NOTSET:
                error_msg = "Environment variable '{}' not set.".format(var)
                raise ConfigurationError(error_msg)
            else:
                value = default

        # Resolve any proxied values
        if hasattr(value, 'startswith') and value.startswith('{{'):
            value = self.__call__(value.lstrip('{{}}'), default, cast, subcast,
                                  default, force, preprocessor, postprocessor)

        if preprocessor:
            value = preprocessor(value)
        if value != default or force:
            value = self.cast(value, cast, subcast)
        if postprocessor:
            value = postprocessor(value)
        return value

    @classmethod
    def cast(cls, value, cast=str, subcast=None):
        """
        Parse and cast provided value.

        :param value: Stringed value.
        :param cast: Type or callable to cast return value as.
        :param subcast: Subtype or callable to cast return values as (used for
                        nested structures).

        :returns: Value of type `cast`.
        """
        if cast is bool:
            value = value.lower() in cls.BOOLEAN_TRUE_STRINGS
        elif cast is float:
            # Clean string
            float_str = re.sub(r'[^\d,\.]', '', value)
            # Split to handle thousand separator for different locales, i.e.
            # comma or dot being the placeholder.
            parts = re.split(r'[,\.]', float_str)
            if len(parts) == 1:
                float_str = parts[0]
            else:
                float_str = "{0}.{1}".format(''.join(parts[0:-1]), parts[-1])
            value = float(float_str)
        elif type(cast) is type and (issubclass(cast, list) or
                                     issubclass(cast, tuple)):
            value = (subcast(i.strip()) if subcast else i.strip() for i in
                     value.split(',') if i)
        elif cast is dict:
            value = {k.strip(): subcast(v.strip()) if subcast else v.strip()
                     for k, v in (i.split('=') for i in value.split(',') if
                     value)}
        try:
            return cast(value)
        except ValueError as error:
            raise ConfigurationError(*error.args)

    # Shortcuts
    bool = shortcut(bool)
    dict = shortcut(dict)
    float = shortcut(float)
    int = shortcut(int)
    list = shortcut(list)
    set = shortcut(set)
    str = shortcut(str)
    tuple = shortcut(tuple)
    json = shortcut(pyjson.loads)
    url = shortcut(urlparse.urlparse)

    @staticmethod
    def read_envfile(path=None, **overrides):
        """
        Read a .env file (line delimited KEY=VALUE) into os.environ.

        If not given a path to the file, recurses up the directory tree until
        found.

        Uses code from Honcho (github.com/nickstenning/honcho) for parsing the
        file.
        """
        if path is None:
            frame = inspect.currentframe().f_back
            caller_dir = os.path.dirname(frame.f_code.co_filename)
            path = os.path.join(os.path.abspath(caller_dir), '.env')

        try:
            with open(path, 'r') as f:
                content = f.read()
        except getattr(__builtins__, 'FileNotFoundError', IOError):
            logger.debug('envfile not found at %s, looking in parent dir.',
                         path)
            filedir, filename = os.path.split(path)
            pardir = os.path.abspath(os.path.join(filedir, os.pardir))
            path = os.path.join(pardir, filename)
            if filedir != pardir:
                Env.read_envfile(path, **overrides)
            else:
                # Reached top level directory.
                warnings.warn('Could not any envfile.')
            return

        logger.debug('Reading environment variables from: %s', path)
        for line in content.splitlines():
            tokens = list(shlex.shlex(line, posix=True))
            # parses the assignment statement
            if len(tokens) < 3:
                continue
            name, op = tokens[:2]
            value = ''.join(tokens[2:])
            if op != '=':
                continue
            if not re.match(r'[A-Za-z_][A-Za-z_0-9]*', name):
                continue
            value = value.replace(r'\n', '\n').replace(r'\t', '\t')
            os.environ.setdefault(name, value)

        for name, value in overrides.items():
            os.environ.setdefault(name, value)

# Convenience object if no schema is required.
env = Env()

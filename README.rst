envparse
========
``envparse`` is a simple utility to parse environment variables.

If you use Heroku and/or subscribe to the tenets of the
`12 Factor App <http://www.12factor.net/>`_
you'll be using a lot of environment variable-based configuration in your app.
``os.environ`` is a great choice to start off with but over time you'll find
yourself duplicating quite a bit of code around handling raw environment
variables.

``envparse`` aims to eliminate this duplicated, often inconsistent parsing
code and instead provide a single, easy-to-use wrapper.

Ideas, and code portions, have been taken from `django-environ
<https://github.com/joke2k/django-environ>`_ project but made framework
agnostic.


Installing
----------
Through PyPI::

    $ pip install envparse

Manually::

    $ pip install git+https://github.com/rconradharris/envparse.git
    OR
    $ git clone https://github.com/rconradharris/envparse && cd envparse
    $ python setup.py install


Usage
-----
In your settings or configuration module, first either import the standard
parser or one with a schema:

.. code-block:: python

    # Standard
    from envparse import env

    # Schema
    from envparse import Env
    env = Env(BOOLEAN_VAR=bool, LIST_VAR=dict(cast=list, subcast=int))


``env`` can then be called in two ways:

* Type explicit: ``env('ENV_VAR_NAME', cast=TYPE, ...)``
* Type implicit (for Python builtin types only): ``env.TYPE('ENV_VAR_NAME', ...)``
  If type is not specified, explicitly or implicitly, then the default
  type is ``str``.


Casting to a specified type:

.. code-block:: python

    # Environment variable: MAIL_ENABLED=1

    mail_enabled = env('MAIL_ENABLED', cast=bool)
    # OR mail_enabled = env.bool('MAIL_ENABLED')
    assert mail_enabled is True

Casting nested types:

.. code-block:: python

    # Environment variable: FOO=1,2,3
    foo = env('FOO'), subcast=int)
    # OR: foo = env('FOO', cast=list, subcast=int)
    # Note that there is no way to implicitly call subcast.
    assert foo == [1, 2, 3]

Specifying defaults:

.. code-block:: python

    # Environment variable MAX_ROWS has not been defined

    max_rows = env.int('MAX_ROWS', default=100)
    assert max_rows == 100

Proxying values, useful in Heroku for wiring up the environment variables they
provide to the ones that your app actually uses:

.. code-block:: python

    # Environment variables: MAILGUN_SMTP_LOGIN=foo,
    # SMTP_LOGIN='{{MAILGUN_SMTP_LOGIN}}'

    smtp_login = env('SMTP_LOGIN')
    assert smtp_login == 'foo'

Now if you switch to using Mandrill as an email provider, instead of having to
modify your app, you can simply make a configuration change:

.. code-block:: bash

    SMTP_LOGIN='{{MANDRILL_UESRNAME}}'

There are also a few convenience methods:

* ``env.json``: parses JSON and returns a dict.
* ``env.url``: parses a url and returns a ``urlparse.ParseResult`` object.


Type specific notes:

* list: the expected environment variable format is ``FOO=1,2,3`` and may
  contain spaces between the commas as well as preceding or trailing whitespace.
* dict: the expected environment variable format is ``FOO='key1=val1,
  key2=val2``. Spaces are also allowed.
* json: a regular JSON string such as ``FOO='{"foo": "bar"}'`` is expected.


Schemas
~~~~~~~
Define a schema so you can only need to provide the cast, subcast, and defaults
once:

.. code-block:: python

    # Environment variables: MAIL_ENABLED=0, LIST_INT='1,2,3'

    # Bind schema to Env object to get schema-based lookups
    env = Env(MAIL_ENABLED=bool, SMTP_LOGIN=dict(cast=str, default='foo'),
              LIST_INT=dict(cast=list, subcast=int))
    assert env('MAIL_ENABLED') is False
    assert env('SMTP_LOGIN') == 'foo' # Not defined so uses default
    assert env('LIST_INT') == [1, 2, 3]

The ``Env`` constructor takes values in the form of either: ``VAR_NAME=type``
or ``VAR_NAME=dict`` where ``dict`` is a dictionary with either one or more of
the following keys specified: ``cast``, ``subcast``, ``default``.


Pre- and Postprocessors
~~~~~~~~~~~~~~~~~~~~~~~
Preprocessors are callables that are run on the environment variable string
before any type casting takes place:

.. code-block:: python

    # Environment variables: FOO=bar

    # Preprocessor to change variable to uppercase
    to_upper = lambda v: v.upper()
    foo = env('FOO', preprocessor=to_upper)
    assert foo == 'BAR'

Postprocessors are callables that are run after the type casting takes place.
An example of one might be returning a datastructure expected by a framework:

.. code-block:: python

    # Environment variable: REDIS_URL='redis://:redispass@127.0.0.1:6379/0'
    def django_redis(url):
      return {'BACKEND': 'django_redis.cache.RedisCache',
          'LOCATION': '{}:{}:{}'.format(url.hostname, url.port, url.path.strip('/')),
          'OPTIONS': {'PASSWORD': url.password}}

    redis_config = env('REDIS_URL', postprocessor=django_redis)
    assert redis_config == {'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:0', 'OPTIONS': {'PASSWORD': 'redispass'}}


Environment File
~~~~~~~~~~~~~~~~
Read from a .env file (line delimited KEY=VALUE):

.. code-block:: python

    # This recurses up the directory tree until a file called '.env' is found.
    env.read_envfile()

    # Manually specifying a path
    env.read_envfile('/config/.myenv')

    # Values can be read as normal
    env.int('FOO')

Contributing
------------

Clone the repo, create a virtualenv then run:

    $ make install

which will install the package as well any dependencies required for running the
tests.

Tests
~~~~~

.. image:: https://secure.travis-ci.org/rconradharris/envparse.png?branch=master

To run the tests install tox::

    pip install tox

Then run them with::

    make test

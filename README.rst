========
envparse
========

If you use Heroku and/or subscribe to the tenets of
`_12 Factor App <http://www.12factor.net/>`_
you'll be using a lot of environment variable-based configuration in your app.
``os.environ`` is a great choice to start off with, but as your app grows,
you'll find yourself duplicating quite a bit of around parsing these
environment variables.

``envparse`` aims to solves these problems once, in a consistent way.
Specifically:

* Casting environment variables to a type::

    MAIL_ENABLED=1

    mail_enabled = env('MAIL_ENABLED', cast=bool)
    if mail_enabled:
        send_mail(...)

* Specifying defaults::

    max_rows = env('MAX_ROWS', cast=int, default=100)
    rows = query(limit=max_rows)

* Proxying values, useful in Heroku for wiring up the environment
  variables they provide with the ones that your app actually uses::

    MAILGUN_SMTP_LOGIN=foo
    SMTP_LOGIN=$MAILGUN_SMTP_LOGIN # This variable is proxied

    smtp_login = env('SMTP_LOGIN')
    assert smtp_login == 'foo'

* Schema-tized lookups: define the cast and default parameters once and use
  multiple places::

    MAIL_ENABLED=0
    SMTP_LOGIN=bar

    env = Env(MAIL_ENABLED=bool, SMTP_LOGIN=(str, 'foo'))
    assert env('MAIL_ENABLED') is False
    assert env('SMTP_LOGIN') == 'bar'

    ...later in the code...

    if env('MAIL_ENABLED'):
        send_email(...)

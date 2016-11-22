import os

from envparse import env


def test_existing_env_vars_can_be_overwritten():
    os.environ['STR'] = 'bar'

    # The value of STR is 'foo' in the sample file. Without the overwrite param, the env var should
    # not be altered...
    env.read_envfile("tests/envfile")
    assert env.str("STR") == 'bar'

    # ...but with the overwrite param it should.
    env.read_envfile("tests/envfile", _overwrite=True)
    assert env.str("STR") == 'foo'

# Copyright (c) 2012 Rick Harris
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import os
import types
import unittest


NOTSET = object()


def env(var, cast=None, default=NOTSET):
    """Return value for given environment variable.

    :param cast: Type to cast return value as.
    :param default: If var not present in environ, return this instead.

    :returns: Value from environment or default (if set)
    """
    try:
        value = os.environ[var]
    except KeyError:
        if default is NOTSET:
            raise

        value = default

    # Resolve any proxied values
    if hasattr(value, 'startswith') and value.startswith('$'):
        value = value.lstrip('$')
        value = env(value, cast=cast, default=default)

    # Don't cast if we're returning a default value
    if value != default:
        if cast is bool:
            value = int(value) != 0
        elif isinstance(cast, list):
            value = map(cast[0], [x for x in value.split(',') if x])
        elif cast:
            value = cast(value)

    return value


class Env(object):
    """Provide schema-based lookups of environment variables so that each
    caller doesn't have to pass in `cast` and `default` parameters.

    Usage:

        env = Env(MAIL_ENABLED=bool, SMTP_LOGIN=(str, 'DEFAULT'))
        if env('MAIL_ENABLED'):
            ...
    """
    def __init__(self, **schema):
        self.schema = schema

    def __call__(self, var, cast=None, default=NOTSET):
        if var in self.schema:
            var_info = self.schema[var]

            try:
                has_default = len(var_info) == 2
            except TypeError:
                has_default = False

            if has_default:
                if not cast:
                    cast = var_info[0]

                if default is NOTSET:
                    try:
                        default = var_info[1]
                    except IndexError:
                        pass
            else:
                if not cast:
                    cast = var_info

        return env(var, cast=cast, default=default)


class EnvTests(unittest.TestCase):
    def setUp(self):
        self.environ = dict(STR_VAR='bar',
                            INT_VAR='42',
                            FLOAT_VAR='33.3',
                            UNICODE_VAR='ubar',
                            BOOL_TRUE_VAR='1',
                            BOOL_FALSE_VAR='0',
                            PROXIED_VAR='$STR_VAR',
                            INT_LIST='42,33',
                            STR_LIST_WITH_SPACES=' foo,  bar',
                            EMPTY_LIST='')
        self._orig_environ = os.environ
        os.environ = self.environ

    def tearDown(self):
        os.environ = self._orig_environ

    def assertTypeAndValue(self, type_, expected, actual):
        self.assertEqual(type_, type(actual))
        self.assertEqual(expected, actual)

    def test_not_present_with_default(self):
        self.assertEqual(3, env('not_present', default=3))

    def test_not_present_without_default(self):
        with self.assertRaises(KeyError):
            env('not_present')

    def test_str(self):
        self.assertTypeAndValue(str, 'bar', env('STR_VAR'))

    def test_int(self):
        self.assertTypeAndValue(int, 42, env('INT_VAR', cast=int))

    def test_int_with_none_default(self):
        self.assertTypeAndValue(types.NoneType, None,
                                env('NOT_PRESENT_VAR', cast=int, default=None))

    def test_float(self):
        self.assertTypeAndValue(float, 33.3, env('FLOAT_VAR', cast=float))

    def test_unicode(self):
        self.assertTypeAndValue(unicode, u'ubar', env('UNICODE_VAR',
                                cast=unicode))

    def test_bool_true(self):
        self.assertTypeAndValue(bool, True, env('BOOL_TRUE_VAR', cast=bool))

    def test_bool_false(self):
        self.assertTypeAndValue(bool, False, env('BOOL_FALSE_VAR', cast=bool))

    def test_proxied_value(self):
        self.assertTypeAndValue(str, 'bar', env('PROXIED_VAR'))

    def test_int_list(self):
        self.assertTypeAndValue(list, [42, 33], env('INT_LIST', cast=[int]))

    def test_str_list_with_spaces(self):
        self.assertTypeAndValue(list, [' foo', '  bar'],
                                env('STR_LIST_WITH_SPACES', cast=[str]))

    def test_empty_list(self):
        self.assertTypeAndValue(list, [], env('EMPTY_LIST', cast=[int]))

    def test_schema(self):
        env = Env(INT_VAR=int, NOT_PRESENT_VAR=(float, 33.3), STR_VAR=str,
                  INT_LIST=[int], DEFAULT_LIST=([int], [2]))

        self.assertTypeAndValue(int, 42, env('INT_VAR'))
        self.assertTypeAndValue(float, 33.3, env('NOT_PRESENT_VAR'))

        self.assertTypeAndValue(str, 'bar', env('STR_VAR'))
        self.assertTypeAndValue(str, 'foo', env('NOT_PRESENT2', default='foo'))

        self.assertTypeAndValue(list, [42, 33], env('INT_LIST'))
        self.assertTypeAndValue(list, [2], env('DEFAULT_LIST'))

        # Override schema in this one case
        self.assertTypeAndValue(str, '42', env('INT_VAR', cast=str))


if __name__ == "__main__":
    unittest.main()

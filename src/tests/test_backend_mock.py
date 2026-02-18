# -*- coding: utf-8 -*-
from __future__ import annotations

from server.parts.backend import MockBackend


class TestMockBackendStrip:
    def test_strip_normalizes_whitespace(self):
        """Verifies _strip produces identical results regardless of indentation,
        which matters for Python 3.13+ docstring dedent behavior."""
        mb = MockBackend.__new__(MockBackend)

        deeply_indented = '''
                query($token: String!) {
                    login {
                        token(token: $token) {
                            userPermissions { codename }
                        }
                    }
                }
            '''

        minimally_indented = '''
        query($token: String!) {
            login {
                token(token: $token) {
                    userPermissions { codename }
                }
            }
        }
        '''

        dedented = 'query($token: String!) {\n    login {\n        token(token: $token) {\n            userPermissions { codename }\n        }\n    }\n}'

        result1 = mb._strip(deeply_indented)
        result2 = mb._strip(minimally_indented)
        result3 = mb._strip(dedented)

        assert result1 == result2 == result3
        assert result1 == 'query($token: String!) { login { token(token: $token) { userPermissions { codename } } } }'

    def test_all_mocked_queries_are_reachable(self):
        """Smoke test: every registered mock query key looks properly normalized."""
        for key in MockBackend.MOCKED:
            assert '\n' not in key
            assert '\r' not in key
            assert '  ' not in key
            assert key == key.strip()

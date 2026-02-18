# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from unittest.mock import patch
import logging

# -- third party --
import sentry_sdk

# -- own --
import utils.log


class TestSentryInit:
    def test_init_sentry_with_dsn(self):
        with patch.object(sentry_sdk, 'init') as mock_init:
            utils.log._init_sentry('https://examplePublicKey@o0.ingest.sentry.io/0', 'v1.0.0')
            mock_init.assert_called_once()
            kwargs = mock_init.call_args
            assert kwargs[1]['dsn'] == 'https://examplePublicKey@o0.ingest.sentry.io/0'
            assert kwargs[1]['release'] == 'v1.0.0'
            integrations = kwargs[1]['integrations']
            assert any(
                isinstance(i, sentry_sdk.integrations.logging.LoggingIntegration)
                for i in integrations
            )

    def test_init_sentry_without_dsn(self):
        with patch.object(sentry_sdk, 'init') as mock_init:
            utils.log._init_sentry(None, 'v1.0.0')
            mock_init.assert_not_called()

        with patch.object(sentry_sdk, 'init') as mock_init:
            utils.log._init_sentry('', 'v1.0.0')
            mock_init.assert_not_called()


class TestServerLogFormatter:
    def test_format_basic(self):
        formatter = utils.log.ServerLogFormatter(use_color=False)
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='test.py',
            lineno=1, msg='hello %s', args=('world',), exc_info=None,
        )
        result = formatter.format(record)
        assert 'hello world' in result
        assert '[I ' in result

    def test_format_with_exception(self):
        formatter = utils.log.ServerLogFormatter(use_color=False)
        try:
            raise ValueError('test error')
        except ValueError:
            import sys
            record = logging.LogRecord(
                name='test', level=logging.ERROR, pathname='test.py',
                lineno=1, msg='failed', args=(), exc_info=sys.exc_info(),
            )
        result = formatter.format(record)
        assert '>>>>>>---' in result
        assert '<<<<<<---' in result
        assert 'ValueError' in result

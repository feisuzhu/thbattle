from gevent import monkey
monkey.patch_all()
import gevent

gevent.getcurrent().gr_name = 'MAIN'

import utils.log
utils.log.patch_gevent_hub_print_exception()

import _pytest.logging


def _create_formatter(self, log_format, log_date_format, auto_indent):
    return utils.log.ServerLogFormatter()


_pytest.logging.LoggingPlugin._create_formatter = _create_formatter

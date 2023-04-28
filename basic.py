import configparser
import json
import logging
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler

import colorlog
import requests
from influxdb import InfluxDBClient

# config
config = configparser.RawConfigParser()
config.read('config.ini')


# log
BASIC_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s'
COLOR_FORMAT = '%(log_color)s%(asctime)s - %(levelname)s - %(lineno)d - %(funcName)s - %(message)s'
DATE_FORMAT = None
basic_formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
color_formatter = colorlog.ColoredFormatter(COLOR_FORMAT, DATE_FORMAT)


class MaxFilter:
    def __init__(self, max_level):
        self.max_level = max_level

    def filter(self, record):
        if record.levelno <= self.max_level:
            return True


logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

chlr = logging.StreamHandler(stream=sys.stdout)
chlr.setFormatter(color_formatter)
chlr.setLevel('INFO')
chlr.addFilter(MaxFilter(logging.INFO))
logger.addHandler(chlr)

ehlr = logging.StreamHandler(stream=sys.stderr)
ehlr.setFormatter(color_formatter)
ehlr.setLevel('WARNING')
logger.addHandler(ehlr)


def add_file_handler(filename):
    fhlr = RotatingFileHandler(filename, maxBytes=1024000, backupCount=10)
    fhlr.setFormatter(basic_formatter)
    fhlr.setLevel('DEBUG')
    logger.addHandler(fhlr)


# dbClient
db = InfluxDBClient(host='localhost', port=8086,
                    username=config['DB'].get('username'),
                    password=config['DB'].get('password'))


# test mode
testmode = False


def set_testmode():
    global testmode
    testmode = True


# heartbeat
def heartbeat(server):
    try:
        requests.get(server, timeout=(5, 10))
        if testmode:
            print("HEARTBEAT OK")
    except Exception as e:
        logger.debug(e)


# describe exception
def exception_desc(e: Exception) -> str:
    if str(e) != '':
        return f'{e.__class__.__module__}.{e.__class__.__name__} ({e})'
    return f'{e.__class__.__module__}.{e.__class__.__name__}'


def eprint(e: Exception, level: int = logging.WARNING, msg: str = None, stacklevel: int = 2) -> None:
    """
    Print exception with traceback.
    """
    if not (isinstance(level, int) and level in logging._levelToName):
        level = logging.WARNING

    if msg is not None:
        logger.log(level, msg, stacklevel=stacklevel)

    exception_str = f'Exception: {exception_desc(e)}'
    logger.log(level, exception_str, stacklevel=stacklevel)

    logger.debug(traceback.format_exc(), stacklevel=stacklevel)


def archive(content: str, suffix: str = None) -> str:
    now = str(datetime.now()).replace(' ', '_').replace(':', '-')
    filepath = f'log/archive/{now}' + (f'.{suffix}' if suffix else '')
    if isinstance(content, str):
        open(filepath, 'w').write(content)
    elif isinstance(content, bytes):
        open(filepath, 'wb').write(content)
    elif isinstance(content, dict):
        open(filepath, 'w').write(json.dumps(content))
    else:
        raise TypeError('content must be str or bytes')
    return filepath

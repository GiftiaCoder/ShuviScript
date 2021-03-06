import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler('shuvi.log')
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s [%(filename)s:%(lineno)d] %(message)s',
    '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# method define
warning = logger.warning

info = logger.info

debug = logger.debug


def error(msg):
    logger.error(msg)
    raise Exception(msg)

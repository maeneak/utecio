import logging

logger = logging.getLogger('utecio')

logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(ch)


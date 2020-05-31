import logging
from traceback import format_exc

logger = logging.getLogger(__file__)
logging.basicConfig(level=logging.DEBUG)

try:
    raise Exception()
except Exception:
    logger.info("test", exc_info=True)
    print(f"test\n{format_exc()}")

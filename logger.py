import logging
from pytz import timezone
from datetime import datetime

def Shanghai(sec, what):
    tz = timezone('Asia/Shanghai')
    timenow = datetime.now(tz)
    return timenow.timetuple()

logging.Formatter.converter = Shanghai

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s]:  %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
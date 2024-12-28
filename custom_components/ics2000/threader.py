""""""
import logging
import time
import threading

from enum import Enum

_LOGGER = logging.getLogger(__name__)

def repeat(tries: int, sleep: int, callable_function, **kwargs):
    _LOGGER.info(f'Function repeat called in thread {threading.current_thread().name}')
    qualname = getattr(callable_function, '__qualname__')
    for i in range(0, tries):
        _LOGGER.info(f'Try {i + 1} of {tries} on {qualname}')
        callable_function(**kwargs)
        time.sleep(sleep if i != tries - 1 else 0)

def single_result(callable_function, **kwargs):
    _LOGGER.info(f'Function single_result called in thread {threading.current_thread().name}')
    return callable_function(**kwargs)

class KlikAanKlikUitAction(Enum):
    TURN_ON = 'on'
    TURN_OFF = 'off'
    DIM = 'dim'
    TEMPERATURE = 'temp'
    HUMIDITY = 'humid'

class KlikAanKlikUitThread(threading.Thread):

    def __init__(self, action: KlikAanKlikUitAction, device_id, target, kwargs):
        super().__init__(
            # Thread name may be 15 characters max
            name=f'kaku{action.value}{device_id}',
            target=target,
            kwargs=kwargs
        )

    @staticmethod
    def has_running_threads(device_id) -> bool:
        running_threads = [thread.name for thread in threading.enumerate() if thread.name in 
                           [f'kaku{member.value}{device_id}' for member in KlikAanKlikUitAction]
                           ]
        if running_threads:
            _LOGGER.info(f'Running KlikAanKlikUit threads: {",".join(running_threads)}')
            return True
        return False
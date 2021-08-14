import sys
import time
import zmq

from typing import Callable

class EddnListener:

    def __init__(self, url: str, timeout: int, callback: Callable[[str], None] = None):
        self.url = url
        self.timeout = timeout
        self.callback = callback

        self._continue = False

        context = zmq.Context()
        self._subscriber = context.socket(zmq.SUB)

        self._subscriber.setsockopt(zmq.SUBSCRIBE, b"")
        self._subscriber.setsockopt(zmq.RCVTIMEO, self.timeout)
    
    def _connection_loop(self):
        while self._continue:
            try:
                self._subscriber.connect(self.url)

                while self._continue:
                    message = self._subscriber.recv()

                    if message == False:
                        self._subscriber.disconnect(self.url)
                        break

                    self.callback(message)

            except zmq.ZMQError as e:
                print("ZMQSocketException: " + str(e))
                sys.stdout.flush()
                self._subscriber.disconnect(self.url)
                time.sleep(5)

    def start(self):
        self._continue = True
        self._connection_loop()

    def stop(self, sig, frame) -> None:
        self._continue = False
    
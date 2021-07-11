import zlib
import zmq
import signal
import simplejson
import sys
import time

from eddn.schema import CommodityV3Schema
from summary import storage
from summary.adapter.commodity_v3 import Adapter


__relayEDDN = 'tcp://eddn.edcd.io:9500'
__timeoutEDDN = 600000
__continue = True
__autosave_wait = 100


def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)
    commodity_v3_schema = CommodityV3Schema()

    summary = storage.load()
    adapter = Adapter(summary)
    save_counter = __autosave_wait

    while __continue:
        try:
            subscriber.connect(__relayEDDN)
            
            while __continue:
                message   = subscriber.recv()
                
                if message == False:
                    subscriber.disconnect(__relayEDDN)
                    break
                
                message = zlib.decompress(message)
                json = simplejson.loads(message)
                
                # Handle commodity v3
                if json['$schemaRef'] == 'https://eddn.edcd.io/schemas/commodity/3' :

                    commodity_v3 = commodity_v3_schema.load(json)
                    adapter.update(commodity_v3)
                    print(f"{commodity_v3.header.uploader_id}:{commodity_v3.message.system_name}/{commodity_v3.message.station_name}")
                    sys.stdout.flush()

                    if save_counter <= 0:
                        storage.save(summary)
                        save_counter = __autosave_wait

                    save_counter -= 1

                
        except zmq.ZMQError as e:
            print ('ZMQSocketException: ' + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)
    
    storage.save(summary)


def signal_handler(sig, frame):
    global __continue
    __continue = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()

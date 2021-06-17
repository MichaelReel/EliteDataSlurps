import zlib
import zmq
import signal
import simplejson
import sys
import time

from eddn.domain import CommodityV3Schema


__relayEDDN = 'tcp://eddn.edcd.io:9500'
__timeoutEDDN = 600000
__continue = True


def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)
    commodity_v3_schema = CommodityV3Schema()

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

                    # # call dumps() to ensure double quotes in output
                    # print(simplejson.dumps(json))
                    print(commodity_v3_schema.load(json))
                    sys.stdout.flush()

                
        except zmq.ZMQError as e:
            print ('ZMQSocketException: ' + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)


def signal_handler(sig, frame):
    global __continue
    __continue = False


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()

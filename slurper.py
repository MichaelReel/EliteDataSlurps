from eddn.journal_v1.schema import JournalV1Schema
from eddn import journal_v1
import zlib
import zmq
import signal
import simplejson
import sys
import time

from eddn.commodity_v3.schema import CommodityV3Schema
from summary import storage
from summary.update_handler.commodity_v3 import UpdateHandler


__relayEDDN = "tcp://eddn.edcd.io:9500"
__timeoutEDDN = 600000
__continue = True
__autosave_wait = 100


def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    
    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)
    commodity_v3_schema = CommodityV3Schema()
    journal_v1_schema = JournalV1Schema()

    summary = storage.load()
    adapter = UpdateHandler(summary)
    save_counter = __autosave_wait

    # Dev extension analysis
    received_schemas = {}
    journal_events = {}

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
                schema_name = json["$schemaRef"]
                if schema_name == "https://eddn.edcd.io/schemas/commodity/3" :

                    commodity_v3 = commodity_v3_schema.load(json)
                    adapter.update(commodity_v3)
                    print(f"{commodity_v3.header.uploader_id}:{commodity_v3.message.system_name}/{commodity_v3.message.station_name}")
                    sys.stdout.flush()

                    if save_counter <= 0:
                        storage.save(summary)
                        save_counter = __autosave_wait

                    save_counter -= 1
                
                
                if schema_name == "https://eddn.edcd.io/schemas/journal/1":

                    journal_v1 = journal_v1_schema.load(json)

                    # Dev analysis
                    event = journal_v1.message.event
                    if event in journal_events:
                        journal_events[event] += 1
                    else:
                        journal_events[event] = 1

                    if event == "Docked" or event == "Location":
                        uploader = journal_v1.header.uploader_id
                        system = journal_v1.message.system_name
                        station = journal_v1.message.station_name
                        station_type = journal_v1.message.station_type
                        print(f"    {uploader}:{system}/{station}({station_type}) : {event}")
                        # print(json)


                # Dev analysis
                if schema_name in received_schemas:
                    received_schemas[schema_name] += 1
                else:
                    received_schemas[schema_name] = 1

        except zmq.ZMQError as e:
            print ("ZMQSocketException: " + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)
    
    storage.save(summary)
    print(received_schemas)
    print(journal_events)


def signal_handler(sig, frame):
    global __continue
    __continue = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

from eddn.commodity_v3.model import CommodityV3
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

commodity_v3_schema = CommodityV3Schema()
journal_v1_schema = JournalV1Schema()


def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)

    summary = storage.load()
    adapter = UpdateHandler(summary)

    # Dev extension analysis
    received_schemas = {}
    journal_events = {}

    while __continue:
        try:
            subscriber.connect(__relayEDDN)

            while __continue:
                message = subscriber.recv()

                if message == False:
                    subscriber.disconnect(__relayEDDN)
                    break

                message = zlib.decompress(message)
                json = simplejson.loads(message)

                # Handle commodity v3
                schema_name = json["$schemaRef"]
                if schema_name == "https://eddn.edcd.io/schemas/commodity/3":

                    handle_commodity_v3(adapter, json=json)

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
                        print(
                            f"    {uploader}:{system}/{station}({station_type}) : {event}"
                        )
                        # print(json)

                # Dev analysis
                if schema_name in received_schemas:
                    received_schemas[schema_name] += 1
                else:
                    received_schemas[schema_name] = 1

        except zmq.ZMQError as e:
            print("ZMQSocketException: " + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)

    storage.save(summary)
    print(received_schemas)
    print(journal_events)


def handle_commodity_v3(
    update_handler: UpdateHandler, json: dict
) -> None:
    commodity_v3 = commodity_v3_schema.load(json)
    uploader_id = commodity_v3.header.uploader_id
    system_name = commodity_v3.message.system_name
    station_name = commodity_v3.message.station_name
    time_to_save = update_handler.update(commodity_v3)

    print(f"{uploader_id}:{system_name}/{station_name}")
    sys.stdout.flush()

    if time_to_save:
        storage.save(update_handler.summary)


def signal_handler(sig, frame):
    global __continue
    __continue = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

import signal
import simplejson
import sys
import time
import zlib
import zmq

from datetime import datetime

from eddn.commodity_v3.model import Commodity, CommodityV3
from eddn.commodity_v3.schema import CommodityV3Schema
from eddn.journal_v1.model import JournalV1
from eddn.journal_v1.schema import JournalV1Schema
from summary.commodity_handler import storage as commodity_storage
from summary.commodity_handler.commodity_v3 import SummaryHandler
from summary.journal_handler import storage as journal_storage
from summary.journal_handler.journal_v1 import JournalHandler
from summary.model import CostSnapshot, StockSummary
from summary.output_handler.cmd_line import Output as CmdLineOutput


__relayEDDN = "tcp://eddn.edcd.io:9500"
__timeoutEDDN = 600000
__continue = True
__print_wait = 20  # Print per messages parsed

commodity_v3_schema = CommodityV3Schema()
journal_v1_schema = JournalV1Schema()


def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    subscriber.setsockopt(zmq.SUBSCRIBE, b"")
    subscriber.setsockopt(zmq.RCVTIMEO, __timeoutEDDN)

    journal_summary = journal_storage.load()
    journal_handler = JournalHandler(target=journal_summary)
    print(f"Journal loaded with {len(journal_summary.stations)} stations")

    commodity_summary = commodity_storage.load()
    commodity_handler = SummaryHandler(
        target=commodity_summary, journal_handler=journal_handler
    )
    print(f"Stock list loaded with {len(commodity_summary.commodities)} commodities")

    print_counter = __print_wait
    print_handler = CmdLineOutput(commodity_summary)

    # Dev extension analysis
    received_schemas = {}
    journal_events = {}
    station_types = {}

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

                # Handle schemas
                schema_name = json["$schemaRef"]
                if schema_name == "https://eddn.edcd.io/schemas/commodity/3":
                    handle_commodity_v3(update_handler=commodity_handler, json=json)

                if schema_name == "https://eddn.edcd.io/schemas/journal/1":
                    journal_v1 = handle_journal_v1(
                        update_handler=journal_handler, json=json
                    )

                    # Dev analysis
                    event = journal_v1.message.event
                    if event in journal_events:
                        journal_events[event] += 1
                    else:
                        journal_events[event] = 1

                    # Dev analysis
                    event = journal_v1.message.event
                    station = journal_v1.message.station_name
                    if (event == "Docked" or event == "Location") and station:
                        station_type = journal_v1.message.station_type or "None"
                        if station_type in station_types:
                            station_types[station_type] += 1
                        else:
                            station_types[station_type] = 1

                # Dev analysis
                if schema_name in received_schemas:
                    received_schemas[schema_name] += 1
                else:
                    received_schemas[schema_name] = 1

                # Print after print_counter messages parsed
                if print_counter <= 0:
                    print_counter = __print_wait
                    print(print_handler.get_highest_trade_diffs_str())
                    sys.stdout.flush()
                else:
                    print_counter -= 1

        except zmq.ZMQError as e:
            print("ZMQSocketException: " + str(e))
            sys.stdout.flush()
            subscriber.disconnect(__relayEDDN)
            time.sleep(5)

    commodity_storage.save(commodity_summary)
    journal_storage.save(journal_summary)
    print(received_schemas)
    print(journal_events)
    print(station_types)

    print(print_handler.get_highest_trade_diffs_str())


def handle_commodity_v3(update_handler: SummaryHandler, json: dict) -> CommodityV3:
    commodity_v3 = commodity_v3_schema.load(json)
    time_to_save = update_handler.update(commodity_v3)

    if time_to_save:
        commodity_storage.save(update_handler.stock_summary)

    return commodity_v3


def handle_journal_v1(update_handler: JournalHandler, json: dict) -> JournalV1:
    journal_v1 = journal_v1_schema.load(json)

    event = journal_v1.message.event
    station = journal_v1.message.station_name

    # We only care about ships docking or reporting location at a dock
    if (event == "Docked" or event == "Location") and station:

        time_to_save = update_handler.update(journal_v1)

        if time_to_save:
            journal_storage.save(update_handler.journal)

    return journal_v1


def signal_handler(sig, frame) -> None:
    global __continue
    __continue = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

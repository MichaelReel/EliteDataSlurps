import numpy
import signal
import simplejson
import sys
import time
import zlib
import zmq

from eddn.commodity_v3.model import Commodity, CommodityV3
from eddn.commodity_v3.schema import CommodityV3Schema
from eddn.journal_v1.model import JournalV1
from eddn.journal_v1.schema import JournalV1Schema
from summary.commodity_handler import storage as commodity_storage
from summary.commodity_handler.commodity_v3 import SummaryHandler
from summary.journal_handler import storage as journal_storage
from summary.journal_handler.journal_v1 import JournalHandler
from summary.model import CostSnapshot, StockSummary


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

    journal_summary = journal_storage.load()
    journal_handler = JournalHandler(target=journal_summary)

    commodity_summary = commodity_storage.load()
    commodity_handler = SummaryHandler(
        target=commodity_summary, journal_handler=journal_handler
    )

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

    print_best_trades(commodity_summary)


def handle_commodity_v3(update_handler: SummaryHandler, json: dict) -> CommodityV3:
    commodity_v3 = commodity_v3_schema.load(json)
    time_to_save = update_handler.update(commodity_v3)

    uploader_id = commodity_v3.header.uploader_id
    system_name = commodity_v3.message.system_name
    station_name = commodity_v3.message.station_name
    print(f"{uploader_id}:{system_name}/{station_name}")
    sys.stdout.flush()

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

        uploader = journal_v1.header.uploader_id
        system = journal_v1.message.system_name
        station = journal_v1.message.station_name
        station_type = journal_v1.message.station_type

        print(f"    {uploader}:{system}/{station}({station_type}) : {event}")

        if time_to_save:
            journal_storage.save(update_handler.journal)

    return journal_v1


def print_best_trades(commodity_summary: StockSummary) -> None:
    best_trades = {}
    for commodity in commodity_summary.commodities:
        if commodity.best_buys and commodity.best_sales:
            key = float(
                commodity.best_sales[0].sell_price - commodity.best_buys[0].buy_price
            )
            while key in best_trades:
                key -= 0.001
            best_trades[key] = commodity

    top_five_keys = sorted(best_trades.keys(), reverse=True)[:5]

    for key in top_five_keys:
        commodity: Commodity = best_trades[key]
        buy_from: CostSnapshot = commodity.best_buys[0]
        sell_to: CostSnapshot = commodity.best_sales[0]
        distance: float = get_trade_distance(buy_from, sell_to)
        print(
            f"{commodity.name} (Profit per unit: {key}, Distance: {distance:.2f} ly):"
        )
        print(
            f"  Buy at {buy_from.buy_price} from {buy_from.system_name} / {buy_from.station_name} ({buy_from.station_type})"
        )
        print(
            f"  Sell at {sell_to.sell_price} from {sell_to.system_name} / {sell_to.station_name} ({sell_to.station_type})"
        )


def get_trade_distance(_from: CostSnapshot, _to: CostSnapshot) -> float:
    a = numpy.array(_from.star_pos)
    b = numpy.array(_to.star_pos)
    return numpy.linalg.norm(a - b)


def signal_handler(sig, frame) -> None:
    global __continue
    __continue = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    main()

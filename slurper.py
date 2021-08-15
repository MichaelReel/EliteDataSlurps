import signal
import simplejson
import sys
import zlib

from config import config
from eddn.commodity_v3.model import CommodityV3
from eddn.commodity_v3.schema import CommodityV3Schema
from eddn.connection.eddn import EddnListener
from eddn.journal_v1.model import JournalV1, Message
from eddn.journal_v1.schema import JournalV1Schema
from summary.commodity_handler import storage as commodity_storage
from summary.commodity_handler.commodity_v3 import SummaryHandler
from summary.journal_handler import storage as journal_storage
from summary.journal_handler.journal_v1 import JournalHandler
from summary.model import DockSummary, StockSummary
from summary.output_handler.cmd_line import Output as CmdLineOutput


class Slurper:
    def __init__(
        self,
        journal_summary: DockSummary,
        commodity_summary: StockSummary,
        print_wait: int,
    ):

        self.journal_handler = JournalHandler(target=journal_summary)
        self.commodity_handler = SummaryHandler(
            target=commodity_summary, journal_handler=self.journal_handler
        )
        self.print_handler = CmdLineOutput(commodity_summary)
        self.__print_wait = print_wait
        self.print_counter = self.__print_wait

        print(
            f"Journal loaded with {len(journal_summary.stations)} stations\n"
            f"Stock list loaded with {len(commodity_summary.commodities)} commodities"
        )

        self.commodity_v3_schema = CommodityV3Schema()
        self.journal_v1_schema = JournalV1Schema()
        self._setup_dev_analysis()

    def get_highest_trade_diffs_str(self) -> str:
        return self.print_handler.get_highest_trade_diffs_str()

    def handle_eddn_message(self, message: str) -> None:
        message = zlib.decompress(message)
        json = simplejson.loads(message)

        # Handle schemas
        schema_name = json["$schemaRef"]
        self._update_dev_analysis_received_schemas(schema_name)

        if schema_name == "https://eddn.edcd.io/schemas/commodity/3":
            self._handle_commodity_v3(update_handler=self.commodity_handler, json=json)
        if schema_name == "https://eddn.edcd.io/schemas/journal/1":
            self._handle_journal_v1(update_handler=self.journal_handler, json=json)

        # Print after print_counter messages parsed
        if self.print_counter <= 0:
            self.print_counter = self.__print_wait
            print(self.get_highest_trade_diffs_str())
            sys.stdout.flush()
        else:
            self.print_counter -= 1

    def _handle_commodity_v3(
        self, update_handler: SummaryHandler, json: dict
    ) -> CommodityV3:
        commodity_v3 = self.commodity_v3_schema.load(json)
        time_to_save = update_handler.update(commodity_v3)
        if time_to_save:
            commodity_storage.save(update_handler.stock_summary)
        return commodity_v3

    def _handle_journal_v1(
        self, update_handler: JournalHandler, json: dict
    ) -> JournalV1:
        journal_v1 = self.journal_v1_schema.load(json)

        event = journal_v1.message.event
        station = journal_v1.message.station_name
        station_type = journal_v1.message.station_type or "None"
        self._update_dev_analysis_journal_events(event=event)

        # We only care about ships docking or reporting location at a dock
        if (event == "Docked" or event == "Location") and station:
            self._update_dev_analysis_station_types(station_type=station_type)

            time_to_save = update_handler.update(journal_v1)
            if time_to_save:
                journal_storage.save(update_handler.journal)

        return journal_v1

    # The dev analysis methods below are probably temporary
    # Just gathering stats that might be relevant for development

    def _setup_dev_analysis(self):
        self._received_schemas = {}
        self._journal_events = {}
        self._station_types = {}

    def _update_dev_analysis_journal_events(self, event: str):
        if event in self._journal_events:
            self._journal_events[event] += 1
        else:
            self._journal_events[event] = 1

    def _update_dev_analysis_station_types(self, station_type: str):
        if station_type in self._station_types:
            self._station_types[station_type] += 1
        else:
            self._station_types[station_type] = 1

    def _update_dev_analysis_received_schemas(self, schema_name: str):
        if schema_name in self._received_schemas:
            self._received_schemas[schema_name] += 1
        else:
            self._received_schemas[schema_name] = 1

    def get_dev_analysis(self) -> dict:
        return {
            "received_schemas": self._received_schemas,
            "journal_events": self._journal_events,
            "station_types": self._station_types,
        }


def main() -> None:

    print("Loading last saved dock descriptions...")
    journal_summary = journal_storage.load()
    print("Loading last saved stock history...")
    commodity_summary = commodity_storage.load()

    print("Setting up network listener...")
    slurper = Slurper(
        journal_summary=journal_summary,
        commodity_summary=commodity_summary,
        print_wait=config.cmd_line_print_wait,
    )
    listener = EddnListener(
        url=config.eddn_relay_url,
        timeout=config.eddn_timeout,
        callback=slurper.handle_eddn_message,
    )
    signal.signal(signal.SIGINT, listener.stop)

    print("Listening!")
    listener.start()

    print("Closing listener...")
    print("Saving current stock history...")
    commodity_storage.save(commodity_summary)
    print("Saving current dock descriptions...")
    journal_storage.save(journal_summary)

    print(slurper.get_dev_analysis())


if __name__ == "__main__":
    main()

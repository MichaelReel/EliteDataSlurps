import signal
import simplejson
import zlib

from sys import stdout

from config import config
from eddn.commodity_v3.model import CommodityV3
from eddn.commodity_v3.schema import CommodityV3Schema
from eddn.connection.eddn import EddnListener
from eddn.journal_v1.model import JournalV1, Message
from eddn.journal_v1.schema import JournalV1Schema
from summary.stock_handler import storage as commodity_storage
from summary.stock_handler.commodity_v3 import StockHandler
from summary.dock_handler import storage as journal_storage
from summary.dock_handler.journal_v1 import DockHandler
from summary.model import DockSummary, StockSummary
from summary.output_handler.cmd_line import Output as CmdLineOutput


class Slurper:
    def __init__(
        self,
        journal_summary: DockSummary,
        commodity_summary: StockSummary,
        print_wait: int,
    ):

        self.dock_handler = DockHandler(config=config.dock, target=journal_summary)
        self.stock_handler = StockHandler(
            config=config.stock,
            target=commodity_summary,
            dock_handler=self.dock_handler,
        )
        self.print_handler = CmdLineOutput(config.cmd_line, commodity_summary)
        self._print_wait = print_wait
        self.print_counter = self._print_wait

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
        """
        This function is called by the EDDN listener for each message received.
        This could be considered to be the main-loop
        """
        message = zlib.decompress(message)
        json = simplejson.loads(message)

        # Handle schemas
        schema_name = json["$schemaRef"]
        self._update_dev_analysis_received_schemas(schema_name)

        if schema_name == "https://eddn.edcd.io/schemas/commodity/3":
            self._handle_commodity_v3(json=json)
        if schema_name == "https://eddn.edcd.io/schemas/journal/1":
            self._handle_journal_v1(json=json)

        self._print_on_messages_counted()

    def _print_on_messages_counted(self):
        """Print after `_print_wait` messages received"""
        if self.print_counter <= 0:
            self.print_counter = self._print_wait
            print(self.get_highest_trade_diffs_str())
            stdout.flush()
        else:
            self.print_counter -= 1

    def _handle_commodity_v3(self, json: dict) -> CommodityV3:
        commodity_v3 = self.commodity_v3_schema.load(json)
        time_to_save = self.stock_handler.update(commodity_v3)
        if time_to_save:
            commodity_storage.save(
                stock_file=config.stock.file_path,
                summary=self.stock_handler.stock_summary,
            )
        return commodity_v3

    def _handle_journal_v1(self, json: dict) -> JournalV1:
        journal_v1 = self.journal_v1_schema.load(json)
        event = journal_v1.message.event
        station = journal_v1.message.station_name
        station_type = journal_v1.message.station_type or "None"
        self._update_dev_analysis_journal_events(event=event)

        # We only care about ships docking or reporting location at a dock
        if (event == "Docked" or event == "Location") and station:
            self._update_dev_analysis_station_types(station_type=station_type)

            time_to_save = self.dock_handler.update(journal_v1)
            if time_to_save:
                journal_storage.save(
                    dock_file=config.dock.file_path,
                    summary=self.dock_handler.journal,
                )

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
    journal_summary = journal_storage.load(dock_file=config.dock.file_path)

    print("Loading last saved stock history...")
    commodity_summary = commodity_storage.load(stock_file=config.stock.file_path)

    print("Setting up network listener...")
    slurper = Slurper(
        journal_summary=journal_summary,
        commodity_summary=commodity_summary,
        print_wait=config.cmd_line.print_wait,
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
    commodity_storage.save(stock_file=config.stock.file_path, summary=commodity_summary)

    print("Saving current dock descriptions...")
    journal_storage.save(dock_file=config.dock.file_path, summary=journal_summary)

    print(slurper.get_dev_analysis())


if __name__ == "__main__":
    main()

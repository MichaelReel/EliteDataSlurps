import signal
import simplejson
import sys
import zlib

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


__relayEDDN = "tcp://eddn.edcd.io:9500"
__timeoutEDDN = 600000
__print_wait = 20  # Print per messages parsed


class Slurper:

    def __init__(self, journal_summary: DockSummary, commodity_summary: StockSummary, print_wait: int):

        self.journal_handler = JournalHandler(target=journal_summary)
        self.commodity_handler = SummaryHandler(
            target=commodity_summary, journal_handler=self.journal_handler
        )
        self.print_handler = CmdLineOutput(commodity_summary)
        self.__print_wait = print_wait
        self.print_counter = self.__print_wait

        print(f"Journal loaded with {len(journal_summary.stations)} stations")
        print(f"Stock list loaded with {len(commodity_summary.commodities)} commodities")
        
        self.commodity_v3_schema = CommodityV3Schema()
        self.journal_v1_schema = JournalV1Schema()
        
        self._setup_dev_analysis()

    def message_callback(self, message: str) -> None:
        self.handle_eddn_message(
            message,
        )

    def get_highest_trade_diffs_str(self) -> str:
        return self.print_handler.get_highest_trade_diffs_str()

    def handle_eddn_message(
        self,
        message,
    ):
        message = zlib.decompress(message)
        json = simplejson.loads(message)

        # Handle schemas
        schema_name = json["$schemaRef"]
        if schema_name == "https://eddn.edcd.io/schemas/commodity/3":
            self.handle_commodity_v3(update_handler=self.commodity_handler, json=json)

        if schema_name == "https://eddn.edcd.io/schemas/journal/1":
            journal_v1 = self.handle_journal_v1(update_handler=self.journal_handler, json=json)

            # Dev analysis
            jv1_message : Message = journal_v1.message
            self._update_dev_analysis_journal_events(jv1_message)
            self._update_dev_analysis_station_types(jv1_message)
           
        # Dev analysis
        self._update_dev_analysis_received_schemas(schema_name)

        # Print after print_counter messages parsed
        if self.print_counter <= 0:
            self.print_counter = self.__print_wait
            print(self.get_highest_trade_diffs_str())
            sys.stdout.flush()
        else:
            self.print_counter -= 1


    def handle_commodity_v3(self, update_handler: SummaryHandler, json: dict) -> CommodityV3:
        commodity_v3 = self.commodity_v3_schema.load(json)
        time_to_save = update_handler.update(commodity_v3)

        if time_to_save:
            commodity_storage.save(update_handler.stock_summary)

        return commodity_v3

    def handle_journal_v1(self, update_handler: JournalHandler, json: dict) -> JournalV1:
        journal_v1 = self.journal_v1_schema.load(json)

        event = journal_v1.message.event
        station = journal_v1.message.station_name

        # We only care about ships docking or reporting location at a dock
        if (event == "Docked" or event == "Location") and station:

            time_to_save = update_handler.update(journal_v1)

            if time_to_save:
                journal_storage.save(update_handler.journal)

        return journal_v1

    # The dev analysis below is probably temporary
    # Just gathering stats that might be relevant for development

    def _setup_dev_analysis(self):
        self._received_schemas = {}
        self._journal_events = {}
        self._station_types = {}
    
    def _update_dev_analysis_journal_events(self, message: Message):
        event = message.event
        if event in self._journal_events:
            self._journal_events[event] += 1
        else:
            self._journal_events[event] = 1

    def _update_dev_analysis_station_types(self, message: Message):
        event = message.event
        station = message.station_name
        if (event == "Docked" or event == "Location") and station:
            station_type = message.station_type or "None"
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
    slurper = Slurper(journal_summary=journal_summary, commodity_summary=commodity_summary, print_wait=__print_wait)
    listener = EddnListener(url=__relayEDDN, timeout=__timeoutEDDN, callback=slurper.message_callback)
    signal.signal(signal.SIGINT, listener.stop)

    print("Listening!")    
    listener.start()

    print("Closing listener...")
    print("Saving current stock history...")
    commodity_storage.save(commodity_summary)
    print("Saving current dock descriptions...")
    journal_storage.save(journal_summary)

    print(slurper.get_dev_analysis())
    print(slurper.get_highest_trade_diffs_str())


if __name__ == "__main__":
    main()

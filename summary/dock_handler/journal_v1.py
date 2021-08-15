from typing import Optional

from config.model import DockConfig
from eddn.journal_v1.model import JournalV1 as EddnJournalV1
from summary.model import DockSummary, Station


class DockHandler:
    def __init__(self, config: DockConfig, target: DockSummary) -> None:
        self.config = config
        self.journal = target
        self.save_counter = self.config.autosave_wait

    def update(self, journal_v1: EddnJournalV1) -> bool:
        """Updates the summary and returns true if it's time to save"""
        system = journal_v1.message.system_name
        station = journal_v1.message.station_name
        if dock_entry := self.get_dock_entry(system=system, station=station):
            if not dock_entry.station_type:
                self._set_dock_entry(
                    system=system, station=station, journal_v1=journal_v1
                )
                print(
                    f"    Updating existing dock entry {system}/{station} ({journal_v1.message.station_type})"
                )
        else:
            self._set_dock_entry(system=system, station=station, journal_v1=journal_v1)

        if self.save_counter <= 0:
            self.save_counter = self.config.autosave_wait
            return True
        else:
            self.save_counter -= 1
            return False

    def _dock_details(self, journal_v1: EddnJournalV1) -> Station:
        return Station(
            dist_from_star_ls=journal_v1.message.dist_from_star_ls,
            market_id=journal_v1.message.market_id,
            star_pos=journal_v1.message.star_pos,
            station_allegiance=journal_v1.message.station_allegiance,
            station_name=journal_v1.message.station_name,
            station_type=journal_v1.message.station_type,
            system_address=journal_v1.message.system_address,
            system_name=journal_v1.message.system_name,
            timestamp=journal_v1.message.timestamp,
        )

    def get_dock_entry(self, system: str, station: str) -> Optional[Station]:
        key = f"{system}/{station}"
        return self.journal.stations.get(key, None)

    def _set_dock_entry(
        self, system: str, station: str, journal_v1: EddnJournalV1
    ) -> None:
        key = f"{system}/{station}"
        self.journal.stations[key] = self._dock_details(journal_v1=journal_v1)

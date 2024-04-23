from typing import Literal
from model import StationModel, StationNameType, Vector
from model.plant import BasePlant
from model.tools import SystemSpecification


class RearrangmentPlant(BasePlant):

    def move_coord_to_another_coord(self, x1: int, y1: int, x2: int, y2):
        """Moves a station from one position to another

        It will check if the movement is possible and then move the station to the new position
        """
        for x in range(self._grid_params.size.x - 1, x2, -1):
            if self.get_station_name_or_null_coord(x, y2) is None:
                continue
            raise UnsolvableError(f"Station at {x2},{y2} is not None")

        station = self.get_and_remove_coord(x1, y1)
        self.set_location(Vector(x2, y2), station.name)

        return station.name


class RearrangmentPlantV1(RearrangmentPlant):
    def __init__(self, system_spec: SystemSpecification) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationModel | None] = []

    def move_station_to_storage_buffer_coord(self, x: int, y: int):
        """Moves a station from the plant to the storage buffer

        Returns the number of stations in the storage buffer
        """
        station = self.get_and_remove_coord(x, y)

        self.storage_buffer.append(station)
        self._stations[station.name] = len(self.storage_buffer)

        return station.name, len(self.storage_buffer)

    def move_station_from_buffer_to_coord(
        self, station_name: StationNameType, x: int, y: int
    ):

        assert self.is_empty_coord(x, y), f"Station at {x},{y} is not None"

        for index, station in enumerate(self.storage_buffer):
            if station is not None and station.name == station_name:
                self.set_location(Vector(x, y), station.name)
                self.storage_buffer[index] = None
                return index
        raise UnsolvableError(f"Station {station_name} not found in storage buffer")


class RearrangmentPlantV2(RearrangmentPlant):
    def __init__(self, system_spec: SystemSpecification, buffer_size: int) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationModel | None] = [
            None for _ in range(buffer_size)
        ]

        self.storage_buffer_cursor: int = 0

    def move_station_to_storage_buffer_coord(self, x: int, y: int):
        """Moves a station from the plant to the storage buffer

        Returns the number of stations in the storage buffer
        """
        if self.storage_buffer_cursor >= len(self.storage_buffer):
            raise UnsolvableError("Storage buffer is not big enough")

        station = self.get_and_remove_coord(x, y)

        result = station.name, self.storage_buffer_cursor + 1

        self.storage_buffer[self.storage_buffer_cursor] = station

        self.storage_buffer_cursor += 1

        while True:
            if self.storage_buffer_cursor == len(self.storage_buffer):
                break

            if self.storage_buffer[self.storage_buffer_cursor] is not None:
                self.storage_buffer_cursor += 1
            else:
                break

        return result

    def move_station_from_buffer_to_coord(
        self, station_name: StationNameType, x: int, y: int
    ):
        assert self.is_empty_coord(x, y), f"Station at {x},{y} is not None"

        for index, station in enumerate(self.storage_buffer):
            if station is not None and station.name == station_name:
                self.set_location(Vector(x, y), station.name)
                self.storage_buffer[index] = None
                self.storage_buffer_cursor = index
                return index

        raise UnsolvableError(f"Station {station_name} not found in storage buffer")


class RearrangmentPlantV3(RearrangmentPlantV2):

    def move_station(
        self, station_name: StationNameType, destiny: Vector[int] | Literal["storage"]
    ):
        if isinstance(destiny, Vector):
            actual_position = self._stations[station_name]
            self._stations[station_name] = destiny


class UnsolvableError(Exception):
    pass

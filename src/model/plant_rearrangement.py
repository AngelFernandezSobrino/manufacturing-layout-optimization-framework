import stat
from typing import Literal
from model import StationNameType, Vector
from model.plant import BasePlant
from model.tools import SystemSpecification


class RearrangmentPlant(BasePlant):

    def move_station(
        self, station_name: StationNameType, destiny: Vector[int] | Literal["store"]
    ):
        """Moves a station to a new position

        It will check if the movement is possible and then move the station to the new position. If it's doing a store operation it will move the station to the storage buffer. Then, the storage place will be returned.

        If it's doing a move operation, it will return the previous position of the station.
        """

        # print(
        #     f"move_station: Moving {station_name} from {self._station_locations[station_name]} to {destiny}"
        # )

        if destiny == "store":
            return (self._station_locations[station_name], self.store(station_name))

        else:
            return (self.move(station_name, destiny), destiny)

    def store(self, station_name: StationNameType) -> int:
        raise NotImplementedError()

    def move(
        self, station_name: StationNameType, destiny: Vector[int]
    ) -> Vector[int] | int:
        raise NotImplementedError()


class RearrangmentPlantStorage(RearrangmentPlant):
    def __init__(self, system_spec: SystemSpecification) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationNameType | None] = []
        self.storage_buffer_cursor: int = 0

    def store(self, station_name: StationNameType) -> int:
        """Moves a station from the plant to the storage buffer

        Returns the storage index
        """
        actual_position = self._station_locations[station_name]

        if isinstance(actual_position, int):
            raise UnsolvableError(
                f"Station {station_name} is already in the storage buffer"
            )

        self._grid[actual_position.y][actual_position.x] = None

        if self.storage_buffer_cursor >= len(self.storage_buffer):
            self.storage_buffer.append(station_name)
        else:
            self.storage_buffer[self.storage_buffer_cursor] = station_name

        self._station_locations[station_name] = self.storage_buffer_cursor

        result = self.storage_buffer_cursor

        while True:
            if self.storage_buffer_cursor == len(self.storage_buffer):
                break

            if self.storage_buffer[self.storage_buffer_cursor] is not None:
                self.storage_buffer_cursor += 1
            else:
                break

        return result

    def move(self, station_name: StationNameType, destiny: Vector[int]):
        """Moves a station to some location in the plant"""
        assert self.is_empty_by_coord(
            destiny.x, destiny.y
        ), f"Station at {destiny} is not None"

        previous_position = self._station_locations[station_name]

        self._grid[destiny.y][destiny.x] = self._station_models[station_name]
        self._station_locations[station_name] = destiny

        # If the station is on the storage buffer we have to clean the storage buffer, otherwise we have to clean the grid position
        if isinstance(previous_position, int):
            self.storage_buffer[previous_position] = None
            self.storage_buffer_cursor = previous_position
        else:
            self._grid[previous_position.y][previous_position.x] = None

        return previous_position

    def is_storage_buffer_not_empty(self) -> bool:
        for station in self.storage_buffer:
            if station is not None:
                return True

        return False

    def render_storage_buffer(self, width: int = 20):
        result = "|"
        for station in self.storage_buffer:
            station = station if station is not None else ""
            result += f"{station:^{width}}|"

        return result


class RearrangmentPlantLimitedStorage(RearrangmentPlantStorage):
    def __init__(self, system_spec: SystemSpecification, buffer_size: int) -> None:
        super().__init__(system_spec)
        self.storage_buffer: list[StationNameType | None] = [
            None for _ in range(buffer_size)
        ]

        self.storage_buffer_cursor: int = 0

    def is_storage_buffer_full(self):
        return self.storage_buffer_cursor == len(self.storage_buffer)

    def store(self, station_name: StationNameType) -> int:
        """Moves a station from the plant to the storage buffer

        Returns the storage index
        """
        actual_position = self._station_locations[station_name]

        if isinstance(actual_position, int):
            raise UnsolvableError(
                f"Station {station_name} is already in the storage buffer"
            )

        self._grid[actual_position.y][actual_position.x] = None

        if self.is_storage_buffer_full():
            raise UnsolvableError(f"Storage buffer is full, can't store {station_name}")

        self.storage_buffer[self.storage_buffer_cursor] = station_name

        self._station_locations[station_name] = self.storage_buffer_cursor

        result = self.storage_buffer_cursor

        while True:
            if self.storage_buffer_cursor == len(self.storage_buffer):
                break

            if self.storage_buffer[self.storage_buffer_cursor] is not None:
                self.storage_buffer_cursor += 1
            else:
                break

        return result


class UnsolvableError(Exception):
    pass

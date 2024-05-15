""" Plant module


Plant description

Coordinates

    ┌────► x
    │
    │
    ▼
    y

Station coordinates

    ┌───────┐ ──▲
    │       │   │
    │       │   │x length
    │       │   │
    └───────┘ ──▼

    │       │
    ◄───────►
    y length

    ───────► x
    0,0
    │  ┌───────┐
    │  │       │
    │  │       │
    │  │       │
    ▼  └───────┘
    y

Grid coordinates

    0,0 ───────► x
      ┌──────┬──────┬──────┐
    │ │      │      │      │
    │ │ 0,0  │ 1,0  │ 2,0  │
    │ ├──────┼──────┼──────┤
    │ │      │      │      │
    │ │ 0,1  │ 1,1  │ 2,1  │
    ▼ ├──────┼──────┼──────┤
    y │      │      │      │
      │ 0,2  │ 1,2  │ 2,2  │
      └──────┴──────┴──────┘

Grid first row is reserved for the conveyor, the stations are placed in the following rows.



"""

from __future__ import annotations

import copy
import itertools
from typing import Any, Mapping, Optional, overload
import prettytable

from model import StationModel, StationNameType, Vector
from model.tools import SystemSpecification


class BasePlant(object):
    """_summary_

    Args:
        object (_type_): _description_
    """

    def __init__(self, system_spec: SystemSpecification) -> None:
        """Model of the 2D distribution of the stations in the plant

        It requires to be associated to a system specification to configure the plant data structure. Furthermore, the spec models are referenced in the plant distribution data structure, so the stations models can be directly accessed from the plant data structure. Until all the stations are placed in the plant, the plant is not ready and other methods other than placing stations should not be used.

        It implements the iterator protocol to iterate over the plant stations. The iterator returns a tuple with the position of the station and the station model.
        """
        self._system_spec = system_spec
        self._grid_params = system_spec.model.stations.grid
        self._station_models = system_spec.model.stations.models

        # To export and import plant configurations
        self.__config: list[tuple[Vector[int], StationNameType]] = []
        self.__config_formated: list[tuple[str, StationNameType]] = []

        self._grid: list[list[Optional[StationModel]]] = [
            [None for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        self._station_locations: dict[StationNameType, Vector[int] | int] = {
            station_name: Vector(-1, -1)
            for station_name in self._system_spec.model.stations.models.keys()
        }

        self._not_ready = True

    # pylint: disable=missing-function-docstring

    def grid_iterator(self):
        return iter(GridIterator(self._grid))

    def stations(self) -> Mapping[StationNameType, Vector[int] | int]:
        return self._station_locations

    def stations_without_storage(self) -> Mapping[StationNameType, Vector[int]]:
        """Get stations with only vector positions

        WARNING: This method should be used only when the plant stations are already placed in the grid, otherwise the type of the station location could be an integer, which is used to store the station in the storage buffer. This is not guaranteed by the code, is up to the deveoper to ensure that.
        """
        return self._station_locations  # type: ignore

    def ready(self):
        self._not_ready = False

    @overload
    def __getitem__(self, key: Vector[int]) -> Optional[StationModel]: ...

    @overload
    def __getitem__(self, key: int) -> list[Optional[StationModel]]: ...

    def __getitem__(
        self, key: int | Vector[int]
    ) -> Optional[StationModel] | list[Optional[StationModel]]:
        if isinstance(key, int):
            return self._grid[key]
        return self._grid[key.y][key.x]

    def set_station_location_by_name(
        self, name: StationNameType, position: Vector[int]
    ):

        station_location = self._station_locations[name]

        assert (
            self._grid[position.y][position.x] is None
        ), f"Station at {position} is occupied by {self._grid[position.y][position.x]}, {name} can't be placed there"

        assert not isinstance(
            station_location, int
        ), f"Station {name} is in storage buffer, this method can't be used"

        assert (
            station_location.x == -1
        ), f"Station {name} has been already placed. Moving methods should be used instead"

        self._grid[position.y][position.x] = self._station_models[name]
        self._station_locations[name] = position

    def get_station_location_by_name(self, name: StationNameType):
        return copy.copy(self._station_locations[name])

    def get_station_by_coord(self, x: int, y: int) -> StationModel:
        station = self._grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        return station

    def get_adjacent_positions(self) -> list[Vector[int]]:

        available_positions: list[Vector] = []

        for x, y in itertools.product(
            range(self._grid_params.size.x), range(1, self._grid_params.size.y)
        ):
            if self._grid[y][x] is None:
                if (
                    (y > 1 and self._grid[y - 1][x] is not None)
                    or (x > 0 and self._grid[y][x - 1] is not None)
                    or (
                        x < self._grid_params.size.x - 1
                        and self._grid[y][x + 1] is not None
                    )
                    or (
                        y < self._grid_params.size.x - 1
                        and self._grid[y + 1][x] is not None
                    )
                ):
                    available_positions.append(Vector(x, y))

        return available_positions

    def get_stations_with_transport_positions(self) -> list[Vector]:

        transport_vectors: list[Vector] = []

        for station in self._station_models.values():
            station_location = self._station_locations[station.name]
            if station.transports is not None and isinstance(station_location, Vector):
                transport_vectors.append(copy.deepcopy(station_location))

        if len(transport_vectors) > 0:
            return transport_vectors

        return []

    def is_empty_by_coord(self, x: int, y: int):
        return self._grid[y][x] is None

    def is_empty_by_vector(self, position: Vector[int]):
        return self._grid[position.y][position.x] is None

    def grid_compare(self, other: BasePlant):
        """Gets another plant and compares it with the current plant

        It returns a grid array with the comparison of the two plants. If the two plants have the same content at an specific position, the value at that position is True, otherwise it is False.
        """
        result: list[list[bool]] = [
            [True for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            own_station = self._grid[y][x]

            other_station_name = (
                None
                if other.is_empty_by_coord(x, y)
                else other.get_station_by_coord(x, y).name
            )

            if own_station is None and other_station_name is None:
                continue

            if own_station is None or other_station_name is None:
                result[y][x] = False
                continue

            if own_station.name == other_station_name:
                continue

            result[y][x] = False

        return result

    def get_config_set(self):
        """Get a set with string of the plant configuration, containing the station name and the position

        It can be used to fast compare two plant configurations for equality, to check if a plant configuration is already existing in a set.
        """

        hash_set: set[str] = set()

        for station_name, location in self._station_locations.items():
            if isinstance(location, Vector) and location.x == -1:
                continue

            hash_set.add(
                f"{station_name}" + f"({location.x},{location.y})"
                if isinstance(location, Vector)
                else f"({str(location)}"
            )

        return hash_set

    def export_config(self):
        self.__config = []
        for station_name, position in self._station_locations.items():
            self.__config.append((position, station_name))  # type: ignore
        return self.__config

    def import_config(self, config: PlantConfigType):
        self.__config = copy.deepcopy(config)
        for position, station_name in self.__config:
            self.set_station_location_by_name(
                self._system_spec.model.stations.models[station_name].name, position
            )

    def export_config_formated(self):
        self.__config_formated = []
        for station_name, position in self._station_locations.items():
            self.__config_formated.append((map_location(position), station_name))
        return self.__config_formated

    def render(self, width=15):
        table = prettytable.PrettyTable()
        column_names = list(
            map(str, reversed(range(1, self._grid_params.size.x + 1)))
        ) + [""]
        table_width: dict[str, int] = {}

        for name in column_names:
            table_width[name] = width
        table.field_names = column_names
        table._min_width = table_width  # pylint: disable=protected-access
        grid_iterator = iter(self._grid)
        conveyor_row = next(grid_iterator)
        shown_row = [value if value is not None else "" for value in conveyor_row]
        table.add_row([*shown_row, "Conveyor"])

        for row_index, row in enumerate(grid_iterator):
            shown_row = [value if value is not None else "" for value in row]
            table.add_row([*shown_row, chr(ord("@") + row_index + 1)])

        return table


class GridIterator:
    def __init__(self, grid: list[list[Any]]) -> None:
        self._grid = grid
        self._iter_x = -1
        self._iter_y = -1

    def __iter__(self):
        self._iter_x = -1
        self._iter_y = -1
        return self

    def __next__(self) -> tuple[Vector[int], StationModel]:
        self._iter_x += 1
        if self._iter_x == len(self._grid[0]):
            self._iter_x = 0
            self._iter_y += 1
            if self._iter_y == len(self._grid):
                raise StopIteration

        actual = self._grid[self._iter_y][self._iter_x]

        return (
            (Vector(self._iter_x, self._iter_y), actual)
            if actual is not None
            else self.__next__()
        )


PlantConfigType = list[tuple[Vector[int], StationNameType]]


def map_location(value: Vector[int] | int) -> str:
    if isinstance(value, Vector):
        return f"{chr(ord('@') + value.y)}{value.x}"
    else:
        return f"SP{value + 1}"


def format_location_to_render(
    value: Vector[int] | int, spec: SystemSpecification
) -> Vector[int] | int:
    if isinstance(value, Vector):
        # Invert the x value to match the formated direction
        return Vector(spec.model.stations.grid.size.x - value.x, value.y)
    else:
        return value


# Errors

# Destiny location not empty


class NonEmptyLocationError(Exception):
    pass

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


"""

from __future__ import annotations

import copy
import itertools
from typing import Any, Optional
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

        It requires to be associated to a system specification to configure the plant data structure. Furthermore, the spec models are referenced in the plant distribution data structure, so the stations models can be directly accessed from the plant data structure.

        It implements the iterator protocol to iterate over the plant stations. The iterator returns a tuple with the position of the station and the station model.

        It can't be used until the ready method is called, as it is used to signal that the plant modelsg

        """
        self._grid_params = system_spec.model.stations.grid
        self._system_spec = system_spec

        # To export and import plant configurations
        self.__config: list[tuple[Vector[int], StationNameType]] = []

        self.__grid: list[list[Optional[StationModel]]] = [
            [None for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        self._stations: dict[StationNameType, Vector[int] | int] = {
            station_name: Vector(-1, -1)
            for station_name in self._system_spec.model.stations.models.keys()
        }

        self._not_ready = True

    # pylint: disable=missing-function-docstring

    def __iter__(self):
        return GridIterator(self.__grid).__iter__()

    def station_position(self, name: StationNameType):
        return copy.copy(self._stations[name])

    def set_location(self, position: Vector[int], name: StationNameType):
        self.__grid[position.y][position.x] = self._system_spec.model.stations.models[
            name
        ]
        self._stations[name] = position

    def get_and_remove(self, position: Vector[int]) -> StationModel:
        """
        Retrieves the station at the specified position in the grid and removes it from the grid.

        Args:
            position (Vector[int]): The position of the station in the grid.

        Returns:
            StationModel: The station object at the specified position.

        Raises:
            AssertionError: If the station at the specified position is None.
        """
        station = self.__grid[position.y][position.x]
        self.__grid[position.y][position.x] = None
        assert station is not None
        return station

    def get_and_remove_coord(self, x: int, y: int) -> StationModel:
        station = self.__grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        self.__grid[y][x] = None
        self._stations[station.name] = Vector(-1, -1)
        return station

    def get_location(self, position: Vector[int]) -> Optional[StationModel]:
        return self.__grid[position.y][position.x]

    def ready(self):
        self._not_ready = False

    def search_by_name(self, station_name: StationNameType):
        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):
            station = self.__grid[y][x]
            if station is None:
                continue

            if station.name == station_name:
                return Vector(x, y)

        raise ValueError(f"Station {station_name} not found")

    def get_station_or_null_coord(self, x: int, y: int) -> Optional[StationModel]:
        return self.__grid[y][x]

    def get_station_coord(self, x: int, y: int) -> StationModel:
        station = self.__grid[y][x]
        assert station is not None, f"Station at {x},{y} is None"
        return station

    def is_empty_coord(self, x: int, y: int):
        return self.__grid[y][x] is None

    def is_empty(self, position: Vector[int]):
        return self.__grid[position.y][position.x] is None

    def get_station_name_coord(self, x: int, y: int):
        station = self.__grid[y][x]
        if station is None:
            raise ValueError(f"Station at {x},{y} is None")
        return station.name

    def get_station_name_or_null_coord(self, x: int, y: int):
        station = self.__grid[y][x]
        return station.name if station is not None else None

    def grid_compare(self, other: BasePlant):
        """Gets another plant and compares it with the current plant

        It returns a grid array with the comparison of the two plants. If the two plants have the same content at an specific position, the value at that position is True, otherwise it is False.

        Args:
            other (Plant): _description_

        Returns:
            bool: _description_
        """
        result: list[list[bool]] = [
            [True for x in range(self._grid_params.size.x)]
            for y in range(self._grid_params.size.y)
        ]

        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            own_station = self.__grid[y][x]
            other_station_name = other.get_station_name_or_null_coord(x, y)

            if own_station is None and other_station_name is None:
                continue

            if own_station is None or other_station_name is None:
                result[y][x] = False
                continue

            if own_station.name == other_station_name:
                continue

            result[y][x] = False

        return result

    def get_flat_config_set(self):
        """_summary_

        Returns:
            _type_: _description_
        """

        hash_set: set[str] = set()

        for x, y in itertools.product(
            range(self._grid_params.size.x), range(self._grid_params.size.y)
        ):
            if self.__grid[y][x] is None:
                continue

            hash_set.add(f"{self.__grid[y][x].name}({x},{y})")

        return hash_set

    def _update_config(self):
        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            if self.__grid[y][x] is None:
                continue
            self.__config.append((Vector(x, y), self.__grid[y][x].name))  # type: ignore

    def export_config(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        self._update_config()
        return self.__config

    def import_config(self, config: PlantConfigType):
        """_summary_

        Args:
            config (PlantConfigType): _description_
        """
        self.__config = copy.deepcopy(config)
        for position, station_name in self.__config:
            self.set_location(
                position, self._system_spec.model.stations.models[station_name].name
            )

    def hash(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        plant_hash = ""

        for y, x in itertools.product(
            range(self._grid_params.size.y), range(self._grid_params.size.x)
        ):
            if self.__grid[y][x] is None:
                continue
            plant_hash += f"{self.__grid[y][x].name}({x},{y})"  # type: ignore

        return plant_hash

    def print(self, width=15):
        """_summary_

        Args:
            width (int, optional): _description_. Defaults to 15.
        """
        table = prettytable.PrettyTable()
        column_names = ["", "A", "B", "C", "D", "E"]
        table_width: dict[str, int] = {}

        for name in column_names:
            table_width[name] = width

        table.field_names = column_names
        # table.max_width = table_width
        table._min_width = table_width  # pylint: disable=protected-access

        for row_index, row in enumerate(self.__grid):
            shown_row = [value for value in row if value is not None]
            table.add_row([row_index, *row])

        print(table)


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

from __future__ import annotations

# import library to read a yaml file
from io import StringIO, TextIOWrapper
from pathlib import Path
import yaml


from . import (
    ModelSpecification,
    ModelSpecificationDict,
)


class SystemSpecification:
    """Wrapper class for the system specification model.

    This class is used to parse the model specification and to store the parsed model.
    """

    def __init__(
        self, model_string: str = "", model_stream: TextIOWrapper | None = None
    ) -> None:
        self.model_string = model_string
        self.model_stream = model_stream

        if model_string != "":
            self.yaml_parsed: ModelSpecificationDict = yaml.full_load(
                StringIO(model_string)
            )
        elif model_stream is not None:
            self.yaml_parsed: ModelSpecificationDict = yaml.full_load(model_stream)
        else:
            raise ValueError("No model source provided")

        self.model: ModelSpecification = ModelSpecification(self.yaml_parsed)

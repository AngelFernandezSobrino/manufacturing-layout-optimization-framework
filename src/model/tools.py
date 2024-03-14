from __future__ import annotations

# import library to read a yaml file
from io import StringIO
from pathlib import Path
import yaml


from . import (
    ModelSpecification,
    ModelSpecificationDict,
)


class SystemSpecification:

    def __init__(self) -> None:

        self.model: ModelSpecification

    def read_model_from_string(self, model_string: str) -> ModelSpecification:
        # Read the model from the string
        try:
            if self.model is not None:
                pass
        except AttributeError:
            yaml_parsed: ModelSpecificationDict = yaml.full_load(StringIO(model_string))
            self.model: ModelSpecification = ModelSpecification(yaml_parsed)

        return self.model

    def read_model_from_source(self, model_path: Path) -> ModelSpecification:
        # Read the model from the yaml file
        try:
            if self.model is not None:
                pass
        except AttributeError:
            model_file = open(model_path, "r")
            yaml_parsed: ModelSpecificationDict = yaml.full_load(model_file)
            self.model: ModelSpecification = ModelSpecification(yaml_parsed)

        return self.model

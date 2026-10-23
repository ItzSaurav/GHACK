"""Scheme Catalogue repository loading versioned scheme definitions."""

import json
from pathlib import Path

from backend.app.schemes.models import SchemeDefinition


class SchemeCatalogue:
    def __init__(self, data_path: Path | None = None):
        if data_path is None:
            data_path = Path(__file__).parent / "schemes_data.json"
        self.data_path = data_path
        self._schemes: dict[str, SchemeDefinition] = {}
        self.reload()

    def reload(self) -> None:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Scheme data file not found at {self.data_path}")
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._schemes = {item["id"]: SchemeDefinition.model_validate(item) for item in data}

    def get_all(self) -> list[SchemeDefinition]:
        return list(self._schemes.values())

    def get_by_id(self, scheme_id: str) -> SchemeDefinition | None:
        return self._schemes.get(scheme_id)

    def count(self) -> int:
        return len(self._schemes)


# Global singleton instance
catalogue = SchemeCatalogue()

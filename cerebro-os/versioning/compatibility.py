from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class VersionContract:
    engine_id: str
    current: str
    minimum_compatible: str
    environment: str
    company_id: str = ""

    @staticmethod
    def _parse(value: str) -> tuple[int, int, int]:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise ValueError("semantic version required")
        return tuple(int(part) for part in parts)

    def validate(self) -> None:
        if not all((self.engine_id.strip(), self.current.strip(), self.minimum_compatible.strip(), self.environment, self.company_id.strip())):
            raise ValueError("version contract fields and company_id are required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        current = self._parse(self.current)
        minimum = self._parse(self.minimum_compatible)
        if current[0] != minimum[0] or minimum > current:
            raise ValueError("minimum compatible version must be within current major and not newer than current")

    def compatible_with(self, candidate: str) -> bool:
        self.validate()
        parsed = self._parse(candidate)
        current = self._parse(self.current)
        minimum = self._parse(self.minimum_compatible)
        return parsed[0] == current[0] and parsed >= minimum

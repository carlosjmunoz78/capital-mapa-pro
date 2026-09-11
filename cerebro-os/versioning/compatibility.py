from dataclasses import dataclass

@dataclass(frozen=True)
class VersionContract:
    engine_id: str
    current: str
    minimum_compatible: str
    environment: str

    def validate(self) -> None:
        if not all((self.engine_id, self.current, self.minimum_compatible, self.environment)):
            raise ValueError("version contract fields are required")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")

    def compatible_with(self, candidate: str) -> bool:
        self.validate()
        def parse(value: str) -> tuple[int, int, int]:
            parts = value.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                raise ValueError("semantic version required")
            return tuple(int(part) for part in parts)
        return parse(candidate) >= parse(self.minimum_compatible)

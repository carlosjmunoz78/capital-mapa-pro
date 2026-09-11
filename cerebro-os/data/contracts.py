from dataclasses import dataclass

@dataclass(frozen=True)
class DataContract:
    engine_id: str
    contract_name: str
    version: str
    company_scoped: bool
    schema_ref: str
    producer: str
    consumers: tuple[str, ...]

    def validate(self) -> None:
        if not all((self.engine_id, self.contract_name, self.version, self.schema_ref, self.producer)):
            raise ValueError("data contract missing required field")
        if not self.consumers:
            raise ValueError("at least one consumer must be declared")

    def safe_for_multicompany(self) -> bool:
        self.validate()
        return self.company_scoped

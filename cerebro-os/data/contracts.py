from dataclasses import dataclass

CANONICAL_SCOPE_FIELDS = {"company_id", "engine_id", "environment", "version"}


@dataclass(frozen=True)
class DataContract:
    engine_id: str
    contract_name: str
    version: str
    company_scoped: bool
    schema_ref: str
    producer: str
    consumers: tuple[str, ...]
    scope_fields: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all((self.engine_id, self.contract_name, self.version, self.schema_ref, self.producer)):
            raise ValueError("data contract missing required field")
        if not self.consumers:
            raise ValueError("at least one consumer must be declared")
        if len(set(self.scope_fields)) != len(self.scope_fields):
            raise ValueError("duplicate scope field")

    def safe_for_multicompany(self) -> bool:
        self.validate()
        return self.company_scoped and CANONICAL_SCOPE_FIELDS.issubset(set(self.scope_fields))

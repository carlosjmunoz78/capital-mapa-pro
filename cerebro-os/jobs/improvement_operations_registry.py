from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from jobs.continuous_improvement_schedule import ImprovementSchedule


@dataclass(frozen=True)
class ImprovementCompanyConfig:
    company_id: str
    legal_name: str
    autonomy_profile: str
    environment: str = "LAB"
    version: str = "1.0.0"
    interval_hours: int = 24
    enabled: bool = True

    def validate(self) -> None:
        ImprovementSchedule(
            self.company_id, self.autonomy_profile, self.environment,
            self.version, self.interval_hours, self.enabled,
        ).validate()
        if not self.legal_name.strip():
            raise ValueError("legal_name required")


class ImprovementOperationsRegistry:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_companies(
              company_id TEXT NOT NULL,
              environment TEXT NOT NULL,
              version TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              PRIMARY KEY(company_id, environment, version)
            )
            """
        )
        self.conn.commit()

    def upsert(self, config: ImprovementCompanyConfig) -> None:
        config.validate()
        payload = json.dumps(asdict(config), sort_keys=True)
        self.conn.execute(
            "INSERT INTO improvement_companies(company_id,environment,version,payload_json) VALUES(?,?,?,?) "
            "ON CONFLICT(company_id,environment,version) DO UPDATE SET payload_json=excluded.payload_json",
            (config.company_id, config.environment, config.version, payload),
        )
        self.conn.commit()

    def active(self) -> tuple[ImprovementCompanyConfig, ...]:
        rows = self.conn.execute("SELECT payload_json FROM improvement_companies ORDER BY company_id,environment,version").fetchall()
        items = tuple(ImprovementCompanyConfig(**json.loads(row[0])) for row in rows)
        return tuple(item for item in items if item.enabled)

    def close(self) -> None:
        self.conn.close()

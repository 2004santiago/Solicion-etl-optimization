from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass
class QualityEvent:
    table: str
    source_system: str
    source_id: str
    action: str
    reason: str
    field: str = ""
    original_value: str = ""
    new_value: str = ""


class QualityReport:
    def __init__(self) -> None:
        self.events: list[QualityEvent] = []
        self.decisions: list[dict[str, str]] = [
            {
                "topic": "Duplicados entre fuentes",
                "decision": "No se fusionan tax_id/RFC/NIT iguales entre sistemas; se conservan source_system y source_id para trazabilidad.",
            },
            {
                "topic": "Productos sin interseccion directa",
                "decision": "Cada producto de SOURCE_A, SOURCE_B y SOURCE_C se carga como registro independiente.",
            },
            {
                "topic": "Pagos duplicados",
                "decision": "Se deduplican solo si coinciden factura, fecha, monto, metodo y referencia dentro de la misma fuente.",
            },
        ]

    def add(
        self,
        table: str,
        source_system: str,
        source_id: object,
        action: str,
        reason: str,
        field: str = "",
        original_value: object = "",
        new_value: object = "",
    ) -> None:
        self.events.append(
            QualityEvent(
                table=table,
                source_system=source_system,
                source_id="" if pd.isna(source_id) else str(source_id),
                action=action,
                reason=reason,
                field=field,
                original_value="" if pd.isna(original_value) else str(original_value),
                new_value="" if pd.isna(new_value) else str(new_value),
            )
        )

    def write(self, output_dir: Path) -> dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        events = [asdict(event) for event in self.events]
        csv_path = output_dir / "quality_report.csv"
        json_path = output_dir / "quality_report.json"
        pd.DataFrame(events).to_csv(csv_path, index=False, encoding="utf-8")
        summary = {
            "totals_by_action": pd.DataFrame(events).groupby("action").size().to_dict() if events else {},
            "totals_by_table": pd.DataFrame(events).groupby("table").size().to_dict() if events else {},
            "decisions": self.decisions,
            "events": events,
        }
        json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"quality_csv": str(csv_path), "quality_json": str(json_path)}

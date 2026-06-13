from __future__ import annotations

import pandas as pd

from etl.config import Settings
from etl.quality import QualityReport
from etl import source_a, source_b, source_c


def build_transformed_dataset(settings: Settings) -> dict[str, str]:
    report = QualityReport()
    settings.transformed_dir.mkdir(parents=True, exist_ok=True)
    frames = {}
    # Orden funcional: dimensiones primero, luego hechos que dependen de esas llaves de negocio.
    frames["customers"] = pd.concat([source_a.customers(settings, report), source_b.customers(settings, report)], ignore_index=True)
    frames["suppliers"] = pd.concat([source_a.suppliers(settings, report), source_b.suppliers(settings, report)], ignore_index=True)
    frames["products"] = pd.concat([source_a.products(settings, report), source_b.products(settings, report), source_c.products(settings, report)], ignore_index=True)
    frames["invoices"] = pd.concat([source_a.invoices(settings, frames["customers"], report), source_b.invoices(settings, frames["customers"], report)], ignore_index=True)
    frames["invoice_lines"] = pd.concat([source_a.invoice_lines(settings, frames["invoices"], report), source_b.invoice_lines(settings, frames["invoices"], report)], ignore_index=True)
    frames["payments"] = pd.concat([source_a.payments(settings, frames["invoices"], report), source_b.payments(settings, frames["invoices"], report)], ignore_index=True)
    manifest = {}
    for name, frame in frames.items():
        path = settings.transformed_dir / f"{name}.pkl"
        frame.to_pickle(path)
        manifest[name] = str(path)
    manifest.update(report.write(settings.output_dir))
    return manifest

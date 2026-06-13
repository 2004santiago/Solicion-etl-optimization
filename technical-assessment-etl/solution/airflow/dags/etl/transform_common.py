from __future__ import annotations

from decimal import Decimal, InvalidOperation

import pandas as pd

from etl.quality import QualityReport

EMAIL_DEFAULT = "no_disponible@placeholder.com"
TEXT_DEFAULT = "NO DISPONIBLE"
DATE_DEFAULT = pd.Timestamp("1900-01-01").date()


def _clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    # Tolerancia media: se normalizan espacios sin rechazar el registro.
    return " ".join(str(value).strip().split())


def _required_text(value: object, table: str, field: str, source: str, source_id: object, report: QualityReport) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        # Tolerancia alta: textos obligatorios vacios se cargan con valor por defecto trazable.
        report.add(table, source, source_id, "default_applied", "Texto obligatorio vacio", field, value, TEXT_DEFAULT)
        return TEXT_DEFAULT
    if cleaned != str(value):
        report.add(table, source, source_id, "cleaned", "Whitespace normalizado", field, value, cleaned)
    return cleaned


def _optional_text(value: object, table: str, field: str, source: str, source_id: object, report: QualityReport) -> str | None:
    cleaned = _clean_text(value)
    if cleaned != str(value) and str(value) != "":
        report.add(table, source, source_id, "cleaned", "Whitespace normalizado", field, value, cleaned)
    return cleaned or None


def _email(value: object, table: str, source: str, source_id: object, report: QualityReport) -> str:
    cleaned = _clean_text(value).lower()
    if not cleaned:
        # Tolerancia alta: el correo sustituto permite cargar el registro sin ocultar el hallazgo.
        report.add(table, source, source_id, "default_applied", "Email vacio", "email", value, EMAIL_DEFAULT)
        return EMAIL_DEFAULT
    return cleaned


def _date(value: object, fmt: str | None, table: str, field: str, source: str, source_id: object, report: QualityReport, required: bool = True):
    cleaned = _clean_text(value)
    if not cleaned:
        if required:
            # Tolerancia alta: fechas requeridas nulas se reemplazan por la fecha centinela documentada.
            report.add(table, source, source_id, "default_applied", "Fecha vacia", field, value, DATE_DEFAULT)
            return DATE_DEFAULT
        return None
    parsed = pd.to_datetime(cleaned, format=fmt, errors="coerce")
    if pd.isna(parsed):
        if required:
            report.add(table, source, source_id, "default_applied", "Fecha invalida", field, value, DATE_DEFAULT)
            return DATE_DEFAULT
        report.add(table, source, source_id, "cleaned", "Fecha opcional invalida convertida a NULL", field, value, "")
        return None
    return parsed.date()


def _decimal(value: object, source: str, table: str, field: str, source_id: object, report: QualityReport, default: str = "0") -> Decimal:
    raw = _clean_text(value)
    # Tolerancia media: cada fuente trae convenciones numericas distintas y se estandarizan a Decimal.
    if source == "SOURCE_B":
        raw = raw.replace(".", "").replace(",", ".") if "," in raw else raw
    raw = raw.replace("$", "").replace(",", "").strip()
    try:
        return Decimal(raw or default)
    except InvalidOperation:
        report.add(table, source, source_id, "default_applied", "Decimal invalido", field, value, default)
        return Decimal(default)


def _bool(value: object) -> bool:
    return _clean_text(value).lower() in {"1", "true", "t", "yes", "y", "si", "activo"}


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else TEXT_DEFAULT


def _exclude_missing_id(df: pd.DataFrame, id_col: str, table: str, source: str, report: QualityReport) -> pd.DataFrame:
    mask = df[id_col].map(_clean_text).eq("")
    for _, row in df[mask].iterrows():
        # Tolerancia cero: sin ID de origen no hay trazabilidad ni carga segura.
        report.add(table, source, row.get(id_col, ""), "excluded", "Registro sin ID de origen", id_col)
    return df[~mask].copy()

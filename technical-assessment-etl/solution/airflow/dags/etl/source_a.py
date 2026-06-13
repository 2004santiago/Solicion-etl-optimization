from __future__ import annotations

from decimal import Decimal

import pandas as pd

from etl.config import Settings
from etl.extract import read_csv
from etl.quality import QualityReport
from etl.transform_common import (
    _bool,
    _clean_text,
    _date,
    _decimal,
    _email,
    _exclude_missing_id,
    _optional_text,
    _required_text,
)


def customers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_a/customers.csv", "SOURCE_A"), "customer_id", "Customers", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["customer_id"])
        rows.append({
            "customer_code": sid, "first_name": _required_text(r["first_name"], "Customers", "first_name", "SOURCE_A", sid, report),
            "last_name": _required_text(r["last_name"], "Customers", "last_name", "SOURCE_A", sid, report), "full_name": None,
            "email": _email(r["email"], "Customers", "SOURCE_A", sid, report), "phone": _optional_text(r["phone"], "Customers", "phone", "SOURCE_A", sid, report),
            "address": _optional_text(r["address"], "Customers", "address", "SOURCE_A", sid, report), "city": _optional_text(r["city"], "Customers", "city", "SOURCE_A", sid, report),
            "country": _optional_text(r["country"], "Customers", "country", "SOURCE_A", sid, report), "tax_id": _optional_text(r["tax_id"], "Customers", "tax_id", "SOURCE_A", sid, report),
            "registration_date": _date(r["registration_date"], "%Y-%m-%d", "Customers", "registration_date", "SOURCE_A", sid, report),
            "credit_limit": _decimal(r["credit_limit"], "SOURCE_A", "Customers", "credit_limit", sid, report), "is_active": _bool(r["is_active"]),
            "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)


def suppliers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_a/suppliers.csv", "SOURCE_A"), "supplier_id", "Suppliers", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["supplier_id"])
        rows.append({
            "supplier_code": sid, "company_name": _required_text(r["company_name"], "Suppliers", "company_name", "SOURCE_A", sid, report),
            "contact_name": _optional_text(r["contact_name"], "Suppliers", "contact_name", "SOURCE_A", sid, report),
            "email": _email(r["email"], "Suppliers", "SOURCE_A", sid, report), "phone": _optional_text(r["phone"], "Suppliers", "phone", "SOURCE_A", sid, report),
            "address": _optional_text(r["address"], "Suppliers", "address", "SOURCE_A", sid, report), "city": _optional_text(r["city"], "Suppliers", "city", "SOURCE_A", sid, report),
            "country": _optional_text(r["country"], "Suppliers", "country", "SOURCE_A", sid, report),
            "tax_id": _optional_text(r["tax_id"], "Suppliers", "tax_id", "SOURCE_A", sid, report), "payment_terms": _optional_text(r["payment_terms"], "Suppliers", "payment_terms", "SOURCE_A", sid, report),
            "is_active": _bool(r["is_active"]), "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)


def products(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_a/products.csv", "SOURCE_A"), "product_id", "Products", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["product_id"])
        rows.append({
            "product_code": sid, "product_name": _required_text(r["product_name"], "Products", "product_name", "SOURCE_A", sid, report),
            "category": _optional_text(r["category"], "Products", "category", "SOURCE_A", sid, report),
            "unit_price": _decimal(r["unit_price"], "SOURCE_A", "Products", "unit_price", sid, report),
            "supplier_id": None, "supplier_code": _optional_text(r["supplier_id"], "Products", "supplier_code", "SOURCE_A", sid, report),
            "sku": _optional_text(r["sku"], "Products", "sku", "SOURCE_A", sid, report),
            "description": _optional_text(r["description"], "Products", "description", "SOURCE_A", sid, report),
            "uom": "UNIDAD",
            "is_active": _bool(r["is_active"]), "created_date": _date(r["created_date"], "%Y-%m-%d", "Products", "created_date", "SOURCE_A", sid, report, required=False),
            "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)


def invoices(settings: Settings, customers_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_customers = [], set(zip(customers_frame.source_system, customers_frame.source_id))
    df = _exclude_missing_id(read_csv(settings, "source_a/invoices.csv", "SOURCE_A"), "invoice_id", "Invoices", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid, customer_code = _clean_text(r["invoice_id"]), _clean_text(r["customer_id"])
        if ("SOURCE_A", customer_code) not in valid_customers:
            # Tolerancia cero: facturas con cliente inexistente violan integridad referencial.
            report.add("Invoices", "SOURCE_A", sid, "excluded", "Factura con cliente inexistente", "customer_code", customer_code)
            continue
        total = _decimal(r["total_amount"], "SOURCE_A", "Invoices", "total_amount", sid, report)
        tax = _decimal(r["tax_amount"], "SOURCE_A", "Invoices", "tax_amount", sid, report)
        rows.append({
            "invoice_number": sid, "customer_id": None, "customer_code": customer_code,
            "invoice_date": _date(r["invoice_date"], "%Y-%m-%d", "Invoices", "invoice_date", "SOURCE_A", sid, report),
            "due_date": _date(r["due_date"], "%Y-%m-%d", "Invoices", "due_date", "SOURCE_A", sid, report, required=False),
            "subtotal": total - tax, "tax_amount": tax, "total_amount": total, "status": _clean_text(r["status"]) or "PENDING",
            "payment_method": _optional_text(r["payment_method"], "Invoices", "payment_method", "SOURCE_A", sid, report),
            "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)


def invoice_lines(settings: Settings, invoices_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices_frame.source_system, invoices_frame.source_id))
    df = _exclude_missing_id(read_csv(settings, "source_a/invoice_lines.csv", "SOURCE_A"), "line_id", "InvoiceLines", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid, invoice_code = _clean_text(r["line_id"]), _clean_text(r["invoice_id"])
        if ("SOURCE_A", invoice_code) not in valid_invoices:
            # Tolerancia cero: las lineas dependen de una factura valida ya aceptada.
            report.add("InvoiceLines", "SOURCE_A", sid, "excluded", "Linea con factura inexistente", "invoice_code", invoice_code)
            continue
        rows.append({
            "invoice_id": None, "invoice_code": invoice_code, "product_id": None, "product_code": _clean_text(r["product_id"]) or None,
            "quantity": _decimal(r["quantity"], "SOURCE_A", "InvoiceLines", "quantity", sid, report),
            "unit_price": _decimal(r["unit_price"], "SOURCE_A", "InvoiceLines", "unit_price", sid, report),
            "discount_pct": _decimal(r["discount_pct"], "SOURCE_A", "InvoiceLines", "discount_pct", sid, report),
            "line_total": _decimal(r["line_total"], "SOURCE_A", "InvoiceLines", "line_total", sid, report),
            "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)


def payments(settings: Settings, invoices_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices_frame.source_system, invoices_frame.source_id))
    invoice_totals = {(r.source_system, r.source_id): r.total_amount for r in invoices_frame.itertuples()}
    paid: dict[tuple[str, str], Decimal] = {}
    seen = set()
    df = _exclude_missing_id(read_csv(settings, "source_a/payments.csv", "SOURCE_A"), "payment_id", "Payments", "SOURCE_A", report)
    for _, r in df.iterrows():
        sid, invoice_code = _clean_text(r["payment_id"]), _clean_text(r["invoice_id"])
        invoice_key = ("SOURCE_A", invoice_code)
        if invoice_key not in valid_invoices:
            # Tolerancia cero: no se cargan pagos para facturas inexistentes o excluidas.
            report.add("Payments", "SOURCE_A", sid, "excluded", "Pago con factura inexistente", "invoice_code", invoice_code)
            continue
        amount = _decimal(r["amount"], "SOURCE_A", "Payments", "amount", sid, report)
        payment_date = _date(r["payment_date"], "%Y-%m-%d", "Payments", "payment_date", "SOURCE_A", sid, report)
        method = _clean_text(r["payment_method"])
        reference = _clean_text(r["reference_number"])
        dupe_key = ("SOURCE_A", invoice_code, str(payment_date), amount, method, reference)
        if dupe_key in seen:
            # Criterio candidato: se deduplican pagos solo con coincidencia exacta de llave de negocio.
            report.add("Payments", "SOURCE_A", sid, "excluded", "Pago duplicado exacto", "dedupe_key", dupe_key)
            continue
        seen.add(dupe_key)
        cumulative = paid.get(invoice_key, Decimal("0")) + amount
        if cumulative > invoice_totals[invoice_key]:
            # Tolerancia cero: el acumulado pagado no puede superar el total de la factura.
            report.add("Payments", "SOURCE_A", sid, "excluded", "Pago excede el total acumulado de la factura", "amount", amount)
            continue
        paid[invoice_key] = cumulative
        rows.append({
            "payment_number": sid, "invoice_id": None, "invoice_code": invoice_code, "payment_date": payment_date,
            "amount": amount, "payment_method": method or None, "reference_number": reference or None,
            "status": _clean_text(r["status"]) or "COMPLETED",
            "source_system": "SOURCE_A", "source_id": sid})
    return pd.DataFrame(rows)

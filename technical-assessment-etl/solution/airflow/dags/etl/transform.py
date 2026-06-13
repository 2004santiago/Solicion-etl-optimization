from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from etl.config import Settings
from etl.extract import read_csv
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


def _customers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    a = _exclude_missing_id(read_csv(settings, "source_a/customers.csv", "SOURCE_A"), "customer_id", "Customers", "SOURCE_A", report)
    for _, r in a.iterrows():
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
    b = _exclude_missing_id(read_csv(settings, "source_b/clientes.csv", "SOURCE_B"), "IdCliente", "Customers", "SOURCE_B", report)
    for _, r in b.iterrows():
        sid = _clean_text(r["IdCliente"])
        full_name = _required_text(r["NombreCompleto"], "Customers", "full_name", "SOURCE_B", sid, report)
        first, last = _split_name(full_name)
        rows.append({
            "customer_code": sid, "first_name": first, "last_name": last, "full_name": full_name,
            "email": _email(r["CorreoElectronico"], "Customers", "SOURCE_B", sid, report), "phone": _optional_text(r["Telefono"], "Customers", "phone", "SOURCE_B", sid, report),
            "address": _optional_text(r["Direccion"], "Customers", "address", "SOURCE_B", sid, report), "city": _optional_text(r["Ciudad"], "Customers", "city", "SOURCE_B", sid, report),
            "country": _optional_text(r["Pais"], "Customers", "country", "SOURCE_B", sid, report), "tax_id": _optional_text(r["RFC"], "Customers", "tax_id", "SOURCE_B", sid, report),
            "registration_date": _date(r["FechaRegistro"], "%d/%m/%Y", "Customers", "registration_date", "SOURCE_B", sid, report),
            "credit_limit": _decimal(r["LimiteCredito"], "SOURCE_B", "Customers", "credit_limit", sid, report), "is_active": _bool(r["Activo"]),
            "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)


def _suppliers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    specs = [
        ("SOURCE_A", "source_a/suppliers.csv", "supplier_id", {"name": "company_name", "contact": "contact_name", "mail": "email", "addr": "address", "tax": "tax_id", "terms": "payment_terms"}),
        ("SOURCE_B", "source_b/proveedores.csv", "IdProveedor", {"name": "RazonSocial", "contact": "NombreContacto", "mail": "Correo", "addr": "DireccionCompleta", "tax": "NIT", "terms": "TerminosPago"}),
    ]
    for source, path, id_col, c in specs:
        df = _exclude_missing_id(read_csv(settings, path, source), id_col, "Suppliers", source, report)
        for _, r in df.iterrows():
            sid = _clean_text(r[id_col])
            rows.append({
                "supplier_code": sid, "company_name": _required_text(r[c["name"]], "Suppliers", "company_name", source, sid, report),
                "contact_name": _optional_text(r[c["contact"]], "Suppliers", "contact_name", source, sid, report),
                "email": _email(r[c["mail"]], "Suppliers", source, sid, report), "phone": _optional_text(r["Telefono" if source == "SOURCE_B" else "phone"], "Suppliers", "phone", source, sid, report),
                "address": _optional_text(r[c["addr"]], "Suppliers", "address", source, sid, report), "city": _optional_text(r["Ciudad" if source == "SOURCE_B" else "city"], "Suppliers", "city", source, sid, report),
                "country": _optional_text(r["Pais" if source == "SOURCE_B" else "country"], "Suppliers", "country", source, sid, report),
                "tax_id": _optional_text(r[c["tax"]], "Suppliers", "tax_id", source, sid, report), "payment_terms": _optional_text(r[c["terms"]], "Suppliers", "payment_terms", source, sid, report),
                "is_active": _bool(r["Activo" if source == "SOURCE_B" else "is_active"]), "source_system": source, "source_id": sid})
    return pd.DataFrame(rows)


def _products(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    specs = [
        ("SOURCE_A", "source_a/products.csv", "product_id", "%Y-%m-%d", {"name": "product_name", "price": "unit_price", "supplier": "supplier_id", "sku": "sku", "active": "is_active", "created": "created_date", "uom": None}),
        ("SOURCE_B", "source_b/productos.csv", "IdProducto", "%d/%m/%Y", {"name": "NombreProducto", "price": "PrecioUnitario", "supplier": "IdProveedor", "sku": "CodigoBarras", "active": "Activo", "created": "FechaCreacion", "uom": "UnidadMedida"}),
        ("SOURCE_C", "source_c/products_catalog.csv", "product_code", None, {"name": "name", "price": "price", "supplier": "supplier_code", "sku": None, "active": "active", "created": None, "uom": "uom"}),
    ]
    for source, path, id_col, fmt, c in specs:
        df = _exclude_missing_id(read_csv(settings, path, source), id_col, "Products", source, report)
        for _, r in df.iterrows():
            sid = _clean_text(r[id_col])
            rows.append({
                "product_code": sid, "product_name": _required_text(r[c["name"]], "Products", "product_name", source, sid, report),
                "category": _optional_text(r["Categoria" if source == "SOURCE_B" else "category"], "Products", "category", source, sid, report),
                "unit_price": _decimal(r[c["price"]], source, "Products", "unit_price", sid, report),
                "supplier_id": None, "supplier_code": _optional_text(r[c["supplier"]], "Products", "supplier_code", source, sid, report),
                "sku": _optional_text(r[c["sku"]], "Products", "sku", source, sid, report) if c["sku"] else None,
                "description": _optional_text(r["Descripcion" if source == "SOURCE_B" else "description"], "Products", "description", source, sid, report),
                "uom": _optional_text(r[c["uom"]], "Products", "uom", source, sid, report) if c["uom"] else "UNIDAD",
                "is_active": _bool(r[c["active"]]), "created_date": _date(r[c["created"]], fmt, "Products", "created_date", source, sid, report, required=False) if c["created"] else None,
                "source_system": source, "source_id": sid})
    return pd.DataFrame(rows)


def _invoices(settings: Settings, customers: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_customers = [], set(zip(customers.source_system, customers.source_id))
    specs = [
        ("SOURCE_A", "source_a/invoices.csv", "invoice_id", "customer_id", "%Y-%m-%d"),
        ("SOURCE_B", "source_b/facturas.csv", "IdFactura", "IdCliente", "%d/%m/%Y"),
    ]
    for source, path, id_col, customer_col, fmt in specs:
        df = _exclude_missing_id(read_csv(settings, path, source), id_col, "Invoices", source, report)
        for _, r in df.iterrows():
            sid, customer_code = _clean_text(r[id_col]), _clean_text(r[customer_col])
            if (source, customer_code) not in valid_customers:
                # Tolerancia cero: facturas con cliente inexistente violan integridad referencial.
                report.add("Invoices", source, sid, "excluded", "Factura con cliente inexistente", "customer_code", customer_code)
                continue
            total = _decimal(r["Total" if source == "SOURCE_B" else "total_amount"], source, "Invoices", "total_amount", sid, report)
            tax = _decimal(r["IVA" if source == "SOURCE_B" else "tax_amount"], source, "Invoices", "tax_amount", sid, report)
            subtotal = _decimal(r["Subtotal"], source, "Invoices", "subtotal", sid, report) if source == "SOURCE_B" else total - tax
            rows.append({
                "invoice_number": sid, "customer_id": None, "customer_code": customer_code,
                "invoice_date": _date(r["FechaFactura" if source == "SOURCE_B" else "invoice_date"], fmt, "Invoices", "invoice_date", source, sid, report),
                "due_date": _date(r["FechaVencimiento" if source == "SOURCE_B" else "due_date"], fmt, "Invoices", "due_date", source, sid, report, required=False),
                "subtotal": subtotal, "tax_amount": tax, "total_amount": total, "status": _clean_text(r["Estado" if source == "SOURCE_B" else "status"]) or "PENDING",
                "payment_method": _optional_text(r["MetodoPago" if source == "SOURCE_B" else "payment_method"], "Invoices", "payment_method", source, sid, report),
                "source_system": source, "source_id": sid})
    return pd.DataFrame(rows)


def _invoice_lines(settings: Settings, invoices: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices.source_system, invoices.source_id))
    specs = [("SOURCE_A", "source_a/invoice_lines.csv", "line_id", "invoice_id", "product_id"), ("SOURCE_B", "source_b/factura_lineas.csv", "IdLinea", "IdFactura", "IdProducto")]
    for source, path, id_col, invoice_col, product_col in specs:
        df = _exclude_missing_id(read_csv(settings, path, source), id_col, "InvoiceLines", source, report)
        for _, r in df.iterrows():
            sid, invoice_code = _clean_text(r[id_col]), _clean_text(r[invoice_col])
            if (source, invoice_code) not in valid_invoices:
                # Tolerancia cero: las lineas dependen de una factura valida ya aceptada.
                report.add("InvoiceLines", source, sid, "excluded", "Linea con factura inexistente", "invoice_code", invoice_code)
                continue
            rows.append({
                "invoice_id": None, "invoice_code": invoice_code, "product_id": None, "product_code": _clean_text(r[product_col]) or None,
                "quantity": _decimal(r["Cantidad" if source == "SOURCE_B" else "quantity"], source, "InvoiceLines", "quantity", sid, report),
                "unit_price": _decimal(r["PrecioUnitario" if source == "SOURCE_B" else "unit_price"], source, "InvoiceLines", "unit_price", sid, report),
                "discount_pct": _decimal(r["Descuento" if source == "SOURCE_B" else "discount_pct"], source, "InvoiceLines", "discount_pct", sid, report),
                "line_total": _decimal(r["TotalLinea" if source == "SOURCE_B" else "line_total"], source, "InvoiceLines", "line_total", sid, report),
                "source_system": source, "source_id": sid})
    return pd.DataFrame(rows)


def _payments(settings: Settings, invoices: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices.source_system, invoices.source_id))
    invoice_totals = {(r.source_system, r.source_id): r.total_amount for r in invoices.itertuples()}
    paid: dict[tuple[str, str], Decimal] = {}
    seen = set()
    specs = [("SOURCE_A", "source_a/payments.csv", "payment_id", "invoice_id", "%Y-%m-%d"), ("SOURCE_B", "source_b/pagos.csv", "IdPago", "IdFactura", "%d/%m/%Y")]
    for source, path, id_col, invoice_col, fmt in specs:
        df = _exclude_missing_id(read_csv(settings, path, source), id_col, "Payments", source, report)
        for _, r in df.iterrows():
            sid, invoice_code = _clean_text(r[id_col]), _clean_text(r[invoice_col])
            invoice_key = (source, invoice_code)
            if invoice_key not in valid_invoices:
                # Tolerancia cero: no se cargan pagos para facturas inexistentes o excluidas.
                report.add("Payments", source, sid, "excluded", "Pago con factura inexistente", "invoice_code", invoice_code)
                continue
            amount = _decimal(r["Monto" if source == "SOURCE_B" else "amount"], source, "Payments", "amount", sid, report)
            payment_date = _date(r["FechaPago" if source == "SOURCE_B" else "payment_date"], fmt, "Payments", "payment_date", source, sid, report)
            method = _clean_text(r["MetodoPago" if source == "SOURCE_B" else "payment_method"])
            reference = _clean_text(r["Referencia" if source == "SOURCE_B" else "reference_number"])
            dupe_key = (source, invoice_code, str(payment_date), amount, method, reference)
            if dupe_key in seen:
                # Criterio candidato: se deduplican pagos solo con coincidencia exacta de llave de negocio.
                report.add("Payments", source, sid, "excluded", "Pago duplicado exacto", "dedupe_key", dupe_key)
                continue
            seen.add(dupe_key)
            cumulative = paid.get(invoice_key, Decimal("0")) + amount
            if cumulative > invoice_totals[invoice_key]:
                # Tolerancia cero: el acumulado pagado no puede superar el total de la factura.
                report.add("Payments", source, sid, "excluded", "Pago excede el total acumulado de la factura", "amount", amount)
                continue
            paid[invoice_key] = cumulative
            rows.append({
                "payment_number": sid, "invoice_id": None, "invoice_code": invoice_code, "payment_date": payment_date,
                "amount": amount, "payment_method": method or None, "reference_number": reference or None,
                "status": _clean_text(r["Estado" if source == "SOURCE_B" else "status"]) or "COMPLETED",
                "source_system": source, "source_id": sid})
    return pd.DataFrame(rows)


def build_transformed_dataset(settings: Settings) -> dict[str, str]:
    report = QualityReport()
    settings.transformed_dir.mkdir(parents=True, exist_ok=True)
    frames = {}
    # Orden funcional: dimensiones primero, luego hechos que dependen de esas llaves de negocio.
    frames["customers"] = _customers(settings, report)
    frames["suppliers"] = _suppliers(settings, report)
    frames["products"] = _products(settings, report)
    frames["invoices"] = _invoices(settings, frames["customers"], report)
    frames["invoice_lines"] = _invoice_lines(settings, frames["invoices"], report)
    frames["payments"] = _payments(settings, frames["invoices"], report)
    manifest = {}
    for name, frame in frames.items():
        path = settings.transformed_dir / f"{name}.pkl"
        frame.to_pickle(path)
        manifest[name] = str(path)
    manifest.update(report.write(settings.output_dir))
    return manifest

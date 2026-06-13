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
    _split_name,
)


def customers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_b/clientes.csv", "SOURCE_B"), "IdCliente", "Customers", "SOURCE_B", report)
    for _, r in df.iterrows():
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


def suppliers(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_b/proveedores.csv", "SOURCE_B"), "IdProveedor", "Suppliers", "SOURCE_B", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["IdProveedor"])
        rows.append({
            "supplier_code": sid, "company_name": _required_text(r["RazonSocial"], "Suppliers", "company_name", "SOURCE_B", sid, report),
            "contact_name": _optional_text(r["NombreContacto"], "Suppliers", "contact_name", "SOURCE_B", sid, report),
            "email": _email(r["Correo"], "Suppliers", "SOURCE_B", sid, report), "phone": _optional_text(r["Telefono"], "Suppliers", "phone", "SOURCE_B", sid, report),
            "address": _optional_text(r["DireccionCompleta"], "Suppliers", "address", "SOURCE_B", sid, report), "city": _optional_text(r["Ciudad"], "Suppliers", "city", "SOURCE_B", sid, report),
            "country": _optional_text(r["Pais"], "Suppliers", "country", "SOURCE_B", sid, report),
            "tax_id": _optional_text(r["NIT"], "Suppliers", "tax_id", "SOURCE_B", sid, report), "payment_terms": _optional_text(r["TerminosPago"], "Suppliers", "payment_terms", "SOURCE_B", sid, report),
            "is_active": _bool(r["Activo"]), "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)


def products(settings: Settings, report: QualityReport) -> pd.DataFrame:
    rows = []
    df = _exclude_missing_id(read_csv(settings, "source_b/productos.csv", "SOURCE_B"), "IdProducto", "Products", "SOURCE_B", report)
    for _, r in df.iterrows():
        sid = _clean_text(r["IdProducto"])
        rows.append({
            "product_code": sid, "product_name": _required_text(r["NombreProducto"], "Products", "product_name", "SOURCE_B", sid, report),
            "category": _optional_text(r["Categoria"], "Products", "category", "SOURCE_B", sid, report),
            "unit_price": _decimal(r["PrecioUnitario"], "SOURCE_B", "Products", "unit_price", sid, report),
            "supplier_id": None, "supplier_code": _optional_text(r["IdProveedor"], "Products", "supplier_code", "SOURCE_B", sid, report),
            "sku": _optional_text(r["CodigoBarras"], "Products", "sku", "SOURCE_B", sid, report),
            "description": _optional_text(r["Descripcion"], "Products", "description", "SOURCE_B", sid, report),
            "uom": _optional_text(r["UnidadMedida"], "Products", "uom", "SOURCE_B", sid, report),
            "is_active": _bool(r["Activo"]), "created_date": _date(r["FechaCreacion"], "%d/%m/%Y", "Products", "created_date", "SOURCE_B", sid, report, required=False),
            "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)


def invoices(settings: Settings, customers_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_customers = [], set(zip(customers_frame.source_system, customers_frame.source_id))
    df = _exclude_missing_id(read_csv(settings, "source_b/facturas.csv", "SOURCE_B"), "IdFactura", "Invoices", "SOURCE_B", report)
    for _, r in df.iterrows():
        sid, customer_code = _clean_text(r["IdFactura"]), _clean_text(r["IdCliente"])
        if ("SOURCE_B", customer_code) not in valid_customers:
            # Tolerancia cero: facturas con cliente inexistente violan integridad referencial.
            report.add("Invoices", "SOURCE_B", sid, "excluded", "Factura con cliente inexistente", "customer_code", customer_code)
            continue
        total = _decimal(r["Total"], "SOURCE_B", "Invoices", "total_amount", sid, report)
        tax = _decimal(r["IVA"], "SOURCE_B", "Invoices", "tax_amount", sid, report)
        subtotal = _decimal(r["Subtotal"], "SOURCE_B", "Invoices", "subtotal", sid, report)
        rows.append({
            "invoice_number": sid, "customer_id": None, "customer_code": customer_code,
            "invoice_date": _date(r["FechaFactura"], "%d/%m/%Y", "Invoices", "invoice_date", "SOURCE_B", sid, report),
            "due_date": _date(r["FechaVencimiento"], "%d/%m/%Y", "Invoices", "due_date", "SOURCE_B", sid, report, required=False),
            "subtotal": subtotal, "tax_amount": tax, "total_amount": total, "status": _clean_text(r["Estado"]) or "PENDING",
            "payment_method": _optional_text(r["MetodoPago"], "Invoices", "payment_method", "SOURCE_B", sid, report),
            "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)


def invoice_lines(settings: Settings, invoices_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices_frame.source_system, invoices_frame.source_id))
    df = _exclude_missing_id(read_csv(settings, "source_b/factura_lineas.csv", "SOURCE_B"), "IdLinea", "InvoiceLines", "SOURCE_B", report)
    for _, r in df.iterrows():
        sid, invoice_code = _clean_text(r["IdLinea"]), _clean_text(r["IdFactura"])
        if ("SOURCE_B", invoice_code) not in valid_invoices:
            # Tolerancia cero: las lineas dependen de una factura valida ya aceptada.
            report.add("InvoiceLines", "SOURCE_B", sid, "excluded", "Linea con factura inexistente", "invoice_code", invoice_code)
            continue
        rows.append({
            "invoice_id": None, "invoice_code": invoice_code, "product_id": None, "product_code": _clean_text(r["IdProducto"]) or None,
            "quantity": _decimal(r["Cantidad"], "SOURCE_B", "InvoiceLines", "quantity", sid, report),
            "unit_price": _decimal(r["PrecioUnitario"], "SOURCE_B", "InvoiceLines", "unit_price", sid, report),
            "discount_pct": _decimal(r["Descuento"], "SOURCE_B", "InvoiceLines", "discount_pct", sid, report),
            "line_total": _decimal(r["TotalLinea"], "SOURCE_B", "InvoiceLines", "line_total", sid, report),
            "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)


def payments(settings: Settings, invoices_frame: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    rows, valid_invoices = [], set(zip(invoices_frame.source_system, invoices_frame.source_id))
    invoice_totals = {(r.source_system, r.source_id): r.total_amount for r in invoices_frame.itertuples()}
    paid: dict[tuple[str, str], Decimal] = {}
    seen = set()
    df = _exclude_missing_id(read_csv(settings, "source_b/pagos.csv", "SOURCE_B"), "IdPago", "Payments", "SOURCE_B", report)
    for _, r in df.iterrows():
        sid, invoice_code = _clean_text(r["IdPago"]), _clean_text(r["IdFactura"])
        invoice_key = ("SOURCE_B", invoice_code)
        if invoice_key not in valid_invoices:
            # Tolerancia cero: no se cargan pagos para facturas inexistentes o excluidas.
            report.add("Payments", "SOURCE_B", sid, "excluded", "Pago con factura inexistente", "invoice_code", invoice_code)
            continue
        amount = _decimal(r["Monto"], "SOURCE_B", "Payments", "amount", sid, report)
        payment_date = _date(r["FechaPago"], "%d/%m/%Y", "Payments", "payment_date", "SOURCE_B", sid, report)
        method = _clean_text(r["MetodoPago"])
        reference = _clean_text(r["Referencia"])
        dupe_key = ("SOURCE_B", invoice_code, str(payment_date), amount, method, reference)
        if dupe_key in seen:
            # Criterio candidato: se deduplican pagos solo con coincidencia exacta de llave de negocio.
            report.add("Payments", "SOURCE_B", sid, "excluded", "Pago duplicado exacto", "dedupe_key", dupe_key)
            continue
        seen.add(dupe_key)
        cumulative = paid.get(invoice_key, Decimal("0")) + amount
        if cumulative > invoice_totals[invoice_key]:
            # Tolerancia cero: el acumulado pagado no puede superar el total de la factura.
            report.add("Payments", "SOURCE_B", sid, "excluded", "Pago excede el total acumulado de la factura", "amount", amount)
            continue
        paid[invoice_key] = cumulative
        rows.append({
            "payment_number": sid, "invoice_id": None, "invoice_code": invoice_code, "payment_date": payment_date,
            "amount": amount, "payment_method": method or None, "reference_number": reference or None,
            "status": _clean_text(r["Estado"]) or "COMPLETED",
            "source_system": "SOURCE_B", "source_id": sid})
    return pd.DataFrame(rows)

import os
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "envoice_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    )


def fetch_all_invoices():
    sql = """
        SELECT
            i.id,
            v.name          AS vendor_name,
            i.invoice_number,
            i.invoice_date,
            i.currency,
            i.total_amount,
            i.confidence_score,
            i.status,
            i.validation_reason,
            i.payment_status,
            i.paid_at,
            i.original_file_path,
            i.created_at
        FROM invoices i
        LEFT JOIN vendors v ON v.id = i.vendor_id
        ORDER BY
            CASE WHEN i.status = 'flagged' THEN 0 ELSE 1 END,
            CASE WHEN i.payment_status = 'paid' THEN 1 ELSE 0 END,
            i.created_at DESC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()


def fetch_invoice_by_id(invoice_id: int):
    sql = """
        SELECT
            i.id,
            v.name          AS vendor_name,
            i.invoice_number,
            i.invoice_date,
            i.currency,
            i.total_amount,
            i.confidence_score,
            i.status,
            i.validation_reason,
            i.payment_status,
            i.paid_at,
            i.original_file_path,
            i.created_at
        FROM invoices i
        LEFT JOIN vendors v ON v.id = i.vendor_id
        WHERE i.id = %s;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (invoice_id,))
            return cur.fetchone()


def fetch_line_items(invoice_id: int):
    sql = """
        SELECT description, quantity, unit_price
        FROM line_items
        WHERE invoice_id = %s
        ORDER BY id;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (invoice_id,))
            return cur.fetchall()


def mark_paid(invoice_id: int):
    sql = """
        UPDATE invoices
        SET payment_status = 'paid',
            paid_at        = NOW()
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (invoice_id,))
        conn.commit()


def approve_invoice(invoice_id: int):
    sql = """
        UPDATE invoices
        SET status = 'approved'
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (invoice_id,))
        conn.commit()


def delete_invoice(invoice_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM line_items WHERE invoice_id = %s;", (invoice_id,))
            cur.execute("DELETE FROM invoices WHERE id = %s;", (invoice_id,))
            cur.execute("""
                DELETE FROM vendors
                WHERE id NOT IN (
                    SELECT DISTINCT vendor_id FROM invoices WHERE vendor_id IS NOT NULL
                );
            """)
        conn.commit()


def correct_invoice(invoice_id: int, fields: dict, line_items: list):
    """
    Updates vendor name (resolving/creating vendor_id), updates invoice fields,
    replaces line items, logs all changes to the corrections table,
    cleans up orphaned vendors, and sets status to approved.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

            # ── 0. Fetch original invoice + line items BEFORE any changes ──
            cur.execute("""
                SELECT
                    i.invoice_number, i.invoice_date, i.currency,
                    i.total_amount, v.name AS vendor_name
                FROM invoices i
                LEFT JOIN vendors v ON v.id = i.vendor_id
                WHERE i.id = %s;
            """, (invoice_id,))
            original = cur.fetchone()

            cur.execute("""
                SELECT description, quantity, unit_price
                FROM line_items
                WHERE invoice_id = %s
                ORDER BY id;
            """, (invoice_id,))
            original_items = cur.fetchall()

        with conn.cursor() as cur:
            # ── 1. Resolve / create vendor ──────────────────────────────
            vendor_name = fields.get("vendor_name")
            vendor_id = None
            if vendor_name:
                cur.execute("""
                    INSERT INTO vendors (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                    RETURNING id;
                """, (vendor_name.strip(),))
                vendor_id = cur.fetchone()[0]

            # ── 2. Update invoice header fields ─────────────────────────
            allowed = {"invoice_number", "invoice_date", "currency", "total_amount"}
            updates = {k: v for k, v in fields.items() if k in allowed}
            if vendor_id:
                updates["vendor_id"] = vendor_id

            if updates:
                set_clause = ", ".join(f"{col} = %s" for col in updates)
                values = list(updates.values()) + [invoice_id]
                sql = f"""
                    UPDATE invoices
                    SET {set_clause},
                        status = 'approved',
                        validation_reason = 'Manually reviewed and corrected'
                    WHERE id = %s;
                """
                cur.execute(sql, values)

            # ── 3. Replace line items ────────────────────────────────────
            cur.execute("DELETE FROM line_items WHERE invoice_id = %s;", (invoice_id,))
            for item in line_items:
                cur.execute("""
                    INSERT INTO line_items (invoice_id, description, quantity, unit_price)
                    VALUES (%s, %s, %s, %s);
                """, (invoice_id, item["description"], item["quantity"], item["unit_price"]))

                        # ── 4. Log corrections (only fields that actually changed) ──
            def log_change(field_name, old_val, new_val):
                if str(old_val) != str(new_val):
                    cur.execute("""
                        INSERT INTO corrections (invoice_id, field_name, old_value, new_value)
                        VALUES (%s, %s, %s, %s);
                    """, (invoice_id, field_name, str(old_val), str(new_val)))

            if original:
                log_change("vendor_name", original["vendor_name"], fields.get("vendor_name"))
                log_change("invoice_number", original["invoice_number"], fields.get("invoice_number"))
                log_change("invoice_date", original["invoice_date"], fields.get("invoice_date"))
                log_change("currency", original["currency"], fields.get("currency"))
                log_change("total_amount", original["total_amount"], fields.get("total_amount"))

            # ── Compare line items individually by position ──────────────
            max_len = max(len(original_items), len(line_items))

            for idx in range(max_len):
                old_item = original_items[idx] if idx < len(original_items) else None
                new_item = line_items[idx] if idx < len(line_items) else None

                old_snapshot = {
                    "description": old_item["description"] if old_item else None,
                    "quantity": float(old_item["quantity"]) if old_item and old_item["quantity"] is not None else None,
                    "unit_price": float(old_item["unit_price"]) if old_item and old_item["unit_price"] is not None else None,
                } if old_item else None

                new_snapshot = {
                    "description": new_item["description"] if new_item else None,
                    "quantity": new_item["quantity"] if new_item else None,
                    "unit_price": new_item["unit_price"] if new_item else None,
                } if new_item else None

                # Skip if both are identical (no item at this position in either, or same values)
                if old_snapshot == new_snapshot:
                    continue

                field_label = f"line_item_{idx + 1}"

                if old_item is None:
                    # New line item was added
                    cur.execute("""
                        INSERT INTO corrections (invoice_id, field_name, old_value, new_value)
                        VALUES (%s, %s, %s, %s);
                    """, (invoice_id, field_label, "none (added)", json.dumps(new_snapshot)))

                elif new_item is None:
                    # Line item was removed
                    cur.execute("""
                        INSERT INTO corrections (invoice_id, field_name, old_value, new_value)
                        VALUES (%s, %s, %s, %s);
                    """, (invoice_id, field_label, json.dumps(old_snapshot), "removed"))

                else:
                    # Line item was modified — log only the specific sub-fields that changed
                    if old_snapshot["description"] != new_snapshot["description"]:
                        log_change(f"{field_label}_description",
                                   old_snapshot["description"], new_snapshot["description"])

                    if old_snapshot["quantity"] != new_snapshot["quantity"]:
                        log_change(f"{field_label}_quantity",
                                   old_snapshot["quantity"], new_snapshot["quantity"])

                    if old_snapshot["unit_price"] != new_snapshot["unit_price"]:
                        log_change(f"{field_label}_unit_price",
                                   old_snapshot["unit_price"], new_snapshot["unit_price"])
            # ── 5. Clean up orphaned vendors ─────────────────────────────
            cur.execute("""
                DELETE FROM vendors
                WHERE id NOT IN (
                    SELECT DISTINCT vendor_id FROM invoices WHERE vendor_id IS NOT NULL
                );
            """)

        conn.commit()


def fetch_corrections_for_invoice(invoice_id: int):
    sql = """
        SELECT field_name, old_value, new_value, corrected_at
        FROM corrections
        WHERE invoice_id = %s
        ORDER BY corrected_at DESC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (invoice_id,))
            return cur.fetchall()
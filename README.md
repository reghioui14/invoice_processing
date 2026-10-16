# Invoice AI

Invoices are read by AI, validated, stored in PostgreSQL, and reviewed in a small web dashboard.

## Structure

- `workflows/`: n8n workflows (JSON). Extraction, validation, database insert, and the AI chat.
- `streamlit/`: small web interface to browse invoices and ask questions in a chat.
- `.env.example`: template for environment variables.

## Setup

1. Copy `.env.example` to `.env` and fill in your own passwords.
2. Start the stack: `docker compose up -d`
3. Import the files from `workflows/` into n8n and recreate the credentials (Gemini, PostgreSQL, IMAP).

## Database

| Table | Main columns |
|---|---|
| `vendors` | `id`, `name` (unique), `created_at` |
| `invoices` | `id`, `vendor_id`, `invoice_number`, `invoice_date`, `currency`, `total_amount`, `confidence_score`, `status`, `validation_reason`, `payment_status`, `paid_at`, `original_file_path`, `created_at` |
| `line_items` | `id`, `invoice_id`, `description`, `quantity`, `unit_price` |
| `corrections` | `id`, `invoice_id`, `field_name`, `old_value`, `new_value`, `corrected_by`, `corrected_at` |

```
vendors 1 ── * invoices 1 ── * line_items
                    1 ── * corrections
```

- `status`: `auto_approved`, `approved` or `flagged` (default `flagged`)
- `payment_status`: `paid` or `unpaid` (default `unpaid`)
- Deleting a vendor or an invoice also deletes the rows that depend on it.

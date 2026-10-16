from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Optional, List

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def accept_array_format(cls, value):
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return {
                "description": value[0],
                "quantity": value[1],
                "unit_price": value[2],
            }
        return value

class InvoiceInput(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    adjustments_total: Optional[float] = None
    currency: Optional[str] = None
    line_items: Optional[List[LineItem]] = Field(default_factory=list)
    confidence_score: Optional[float] = None
class Reason(BaseModel):
    tier: str
    message: str

class ValidationOutput(BaseModel):
    status: str
    reasons: List[Reason]

    @computed_field
    @property
    def validation_reason(self) -> str | None:
        meaningful = [r for r in self.reasons if r.tier != "none"]
        if not meaningful:
            return None
        return "; ".join(f"[{r.tier}] {r.message}" for r in meaningful)
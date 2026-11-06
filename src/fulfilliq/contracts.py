from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import SCHEMA_VERSION


class ContractError(ValueError):
    """A batch/event contract failed validation."""


class BaseEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal[SCHEMA_VERSION]
    event_type: str
    order_id: str = Field(min_length=1, max_length=128)
    event_ts: datetime
    promised_delivery_date: date

    @field_validator("event_ts", mode="before")
    @classmethod
    def timestamp_has_no_timezone_claim(cls, value: object) -> object:
        # Olist timestamps have no reliable timezone. Reject fabricated offsets.
        if isinstance(value, str) and (value.endswith("Z") or "+" in value[10:]):
            raise ValueError("event_ts must be a timezone-naive source timestamp")
        return value


class OrderPlaced(BaseEvent):
    event_type: Literal["order_placed"]
    customer_state: str | None = Field(default=None, max_length=8)
    seller_state: str | None = Field(default=None, max_length=8)
    items_count: int = Field(ge=1, le=999)
    seller_count: int = Field(ge=1, le=999)
    order_value_brl: float = Field(ge=0)
    freight_brl: float = Field(ge=0)
    product_category_primary: str | None = Field(default=None, max_length=128)


class DeliveryOutcome(BaseEvent):
    event_type: Literal["delivery_outcome"]
    delivered_date: date
    final_order_status: Literal["delivered"]


def parse_event(payload: dict) -> OrderPlaced | DeliveryOutcome:
    kind = payload.get("event_type")
    if kind == "order_placed":
        return OrderPlaced.model_validate(payload)
    if kind == "delivery_outcome":
        return DeliveryOutcome.model_validate(payload)
    raise ContractError(f"unsupported event_type {kind!r}")

"""ReserveInventoryActivity - Temporal Activity for inventory reservation.

This Activity reserves inventory for order items.
In production, this would call an external inventory microservice.

Architecture:
- @activity.defn decorator makes this a Temporal Activity
- Simulates inventory reservation (replace with actual API call)
- Returns ReservationOutput with reservation ID

Compensation:
- cancel_reservation Activity releases the reservation
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from temporalio import activity

# =============================================================================
# Input/Output DTOs
# =============================================================================


class InventoryItemInput(BaseModel):
    """Item to reserve in inventory."""

    product_id: UUID
    quantity: int = Field(..., ge=1)
    product_name: str | None = None


class ReserveInventoryInput(BaseModel):
    """Input for reserve_inventory activity.

    Attributes:
        order_id: Order UUID for tracking
        user_id: Customer UUID
        items: Items to reserve
    """

    order_id: UUID
    user_id: UUID
    items: list[InventoryItemInput]


class ReservationOutput(BaseModel):
    """Output from reserve_inventory activity.

    Attributes:
        reservation_id: Unique reservation identifier
        order_id: Associated order UUID
        reserved_items: Items that were reserved
        expires_at: When reservation expires
    """

    reservation_id: str
    order_id: UUID
    reserved_items: list[InventoryItemInput]
    expires_at: datetime


# =============================================================================
# Reserve Inventory Activity
# =============================================================================


@activity.defn(name="reserve_inventory")
async def reserve_inventory(data: ReserveInventoryInput) -> ReservationOutput:
    """Reserve inventory for order items.

    This is a Temporal Activity that reserves inventory.
    In production, this would call the inventory microservice API.

    Args:
        data: Reservation request with items

    Returns:
        ReservationOutput with reservation ID

    Raises:
        Exception: On insufficient inventory or service errors
    """
    activity.logger.info(
        f"📦 Reserving inventory for order {data.order_id} ({len(data.items)} items)"
    )

    # Simulate inventory check
    for item in data.items:
        # In production: await inventory_client.check_availability(item.product_id, item.quantity)
        activity.logger.debug(f"Checking availability: {item.product_id} x {item.quantity}")

    # Generate reservation
    reservation_id = f"RES-{uuid4().hex[:12].upper()}"
    expires_at = datetime.now() + timedelta(minutes=30)

    # In production:
    # reservation = await inventory_client.reserve(
    #     order_id=data.order_id,
    #     items=[(item.product_id, item.quantity) for item in data.items],
    # )

    activity.logger.info(f"✅ Inventory reserved: {reservation_id}")

    return ReservationOutput(
        reservation_id=reservation_id,
        order_id=data.order_id,
        reserved_items=data.items,
        expires_at=expires_at,
    )


# =============================================================================
# Cancel Reservation Activity (Compensation)
# =============================================================================


@activity.defn(name="cancel_reservation")
async def cancel_reservation(reservation_id: str) -> bool:
    """Cancel inventory reservation (compensation activity).

    Called during saga compensation to release reserved inventory.
    This is idempotent - already cancelled reservations are ignored.

    Args:
        reservation_id: Reservation ID to cancel

    Returns:
        True if cancelled successfully
    """
    activity.logger.info(f"🔙 Cancelling reservation: {reservation_id}")

    # In production:
    # try:
    #     await inventory_client.cancel_reservation(reservation_id)
    # except ReservationNotFound:
    #     pass  # Idempotent - already cancelled

    # Simulate successful cancellation
    activity.logger.info(f"✅ Reservation {reservation_id} cancelled")
    return True


__all__ = [
    "InventoryItemInput",
    "ReservationOutput",
    "ReserveInventoryInput",
    "cancel_reservation",
    "reserve_inventory",
]

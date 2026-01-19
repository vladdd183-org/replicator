"""ScheduleDeliveryActivity - Temporal Activity for delivery scheduling.

This Activity schedules delivery for an order.
In production, this would integrate with shipping/logistics systems.

Architecture:
- @activity.defn decorator makes this a Temporal Activity
- Simulates delivery scheduling (replace with actual logistics API)
- Returns DeliveryOutput with tracking details

Compensation:
- cancel_delivery Activity cancels the scheduled delivery
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel
from temporalio import activity


# =============================================================================
# Input/Output DTOs
# =============================================================================

class ScheduleDeliveryInput(BaseModel):
    """Input for schedule_delivery activity.
    
    Attributes:
        order_id: Order UUID being shipped
        shipping_address: Delivery address
        user_id: Customer UUID (for notifications)
        items_count: Number of items (for package estimation)
    """
    
    order_id: UUID
    shipping_address: str
    user_id: UUID
    items_count: int = 1
    
    # Shipping preferences
    expedited: bool = False
    delivery_instructions: str | None = None


class DeliveryOutput(BaseModel):
    """Output from schedule_delivery activity.
    
    Attributes:
        delivery_id: Internal delivery tracking ID
        order_id: Associated order UUID
        tracking_number: External carrier tracking number
        carrier: Shipping carrier name
        estimated_delivery: Expected delivery date
        status: Delivery status
    """
    
    delivery_id: str
    order_id: UUID
    tracking_number: str
    carrier: str
    estimated_delivery: datetime
    status: str  # "scheduled", "pending", "shipped"


# =============================================================================
# Schedule Delivery Activity
# =============================================================================

@activity.defn(name="schedule_delivery")
async def schedule_delivery(data: ScheduleDeliveryInput) -> DeliveryOutput:
    """Schedule delivery for order.
    
    This is a Temporal Activity that schedules shipping.
    In production, this would call logistics APIs (FedEx, UPS, etc.).
    
    Note: This step often doesn't need compensation because
    delivery scheduling is typically the final step and
    can be cancelled separately.
    
    Args:
        data: Delivery request with shipping details
        
    Returns:
        DeliveryOutput with tracking information
        
    Raises:
        Exception: On scheduling errors
    """
    activity.logger.info(
        f"🚚 Scheduling delivery for order {data.order_id}"
    )
    
    # Calculate estimated delivery
    base_days = 3 if data.expedited else 5
    estimated_delivery = datetime.now() + timedelta(days=base_days)
    
    # In production:
    # shipment = await shipping_client.create_shipment(
    #     address=data.shipping_address,
    #     items_count=data.items_count,
    #     service_type="express" if data.expedited else "standard",
    # )
    
    # Generate delivery record
    delivery_id = f"DEL-{uuid4().hex[:12].upper()}"
    tracking_number = f"1Z{uuid4().hex[:16].upper()}"
    
    activity.logger.info(
        f"✅ Delivery scheduled: {delivery_id}, tracking: {tracking_number}"
    )
    
    return DeliveryOutput(
        delivery_id=delivery_id,
        order_id=data.order_id,
        tracking_number=tracking_number,
        carrier="UPS",  # Would be actual carrier
        estimated_delivery=estimated_delivery,
        status="scheduled",
    )


# =============================================================================
# Cancel Delivery Activity (Compensation)
# =============================================================================

@activity.defn(name="cancel_delivery")
async def cancel_delivery(delivery_id: str) -> bool:
    """Cancel scheduled delivery (compensation activity).
    
    Called during saga compensation if order is cancelled
    after delivery was scheduled.
    
    Args:
        delivery_id: Delivery ID to cancel
        
    Returns:
        True if cancelled successfully
    """
    activity.logger.info(f"🔙 Cancelling delivery: {delivery_id}")
    
    # In production:
    # try:
    #     await shipping_client.cancel_shipment(delivery_id)
    # except ShipmentNotFound:
    #     pass  # Already cancelled or shipped
    # except ShipmentAlreadyShipped:
    #     # Cannot cancel, need to handle return
    #     pass
    
    activity.logger.info(f"✅ Delivery {delivery_id} cancelled")
    return True


__all__ = [
    "ScheduleDeliveryInput",
    "DeliveryOutput",
    "schedule_delivery",
    "cancel_delivery",
]

"""OrderModule Temporal Activities.

Activities are the building blocks of Temporal Workflows.
Each Activity represents an atomic, compensatable operation.

Architecture:
- Activity = Porto Task + @activity.defn decorator
- Activities are executed by Temporal Worker
- Each Activity has a corresponding compensation Activity

Activities in this module:
- CreateOrderActivity: Creates order record in database
- ReserveInventoryActivity: Reserves inventory for order items
- ChargePaymentActivity: Processes payment
- ScheduleDeliveryActivity: Schedules delivery

Compensation Activities:
- CancelOrderActivity: Marks order as cancelled/failed
- CancelReservationActivity: Releases inventory reservation
- RefundPaymentActivity: Issues refund for payment
"""

from src.Containers.AppSection.OrderModule.Activities.ChargePaymentActivity import (
    ChargePaymentInput,
    PaymentOutput,
    charge_payment,
    refund_payment,
)
from src.Containers.AppSection.OrderModule.Activities.CreateOrderActivity import (
    CreateOrderInput,
    CreateOrderOutput,
    cancel_order,
    create_order,
)
from src.Containers.AppSection.OrderModule.Activities.NotificationActivity import (
    NotificationInput,
    send_order_cancelled,
    send_order_confirmation,
)
from src.Containers.AppSection.OrderModule.Activities.ReserveInventoryActivity import (
    ReservationOutput,
    ReserveInventoryInput,
    cancel_reservation,
    reserve_inventory,
)
from src.Containers.AppSection.OrderModule.Activities.ScheduleDeliveryActivity import (
    DeliveryOutput,
    ScheduleDeliveryInput,
    cancel_delivery,
    schedule_delivery,
)

# All activities for Worker registration
ALL_ACTIVITIES = [
    # Main activities
    create_order,
    reserve_inventory,
    charge_payment,
    schedule_delivery,
    send_order_confirmation,
    # Compensation activities
    cancel_order,
    cancel_reservation,
    refund_payment,
    cancel_delivery,
    send_order_cancelled,
]


__all__ = [
    # Activity functions
    "create_order",
    "cancel_order",
    "reserve_inventory",
    "cancel_reservation",
    "charge_payment",
    "refund_payment",
    "schedule_delivery",
    "cancel_delivery",
    "send_order_confirmation",
    "send_order_cancelled",
    # Input/Output DTOs
    "CreateOrderInput",
    "CreateOrderOutput",
    "ReserveInventoryInput",
    "ReservationOutput",
    "ChargePaymentInput",
    "PaymentOutput",
    "ScheduleDeliveryInput",
    "DeliveryOutput",
    "NotificationInput",
    # Registry
    "ALL_ACTIVITIES",
]

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

from src.Containers.AppSection.OrderModule.Activities.CreateOrderActivity import (
    create_order,
    cancel_order,
    CreateOrderInput,
    CreateOrderOutput,
)
from src.Containers.AppSection.OrderModule.Activities.ReserveInventoryActivity import (
    reserve_inventory,
    cancel_reservation,
    ReserveInventoryInput,
    ReservationOutput,
)
from src.Containers.AppSection.OrderModule.Activities.ChargePaymentActivity import (
    charge_payment,
    refund_payment,
    ChargePaymentInput,
    PaymentOutput,
)
from src.Containers.AppSection.OrderModule.Activities.ScheduleDeliveryActivity import (
    schedule_delivery,
    cancel_delivery,
    ScheduleDeliveryInput,
    DeliveryOutput,
)
from src.Containers.AppSection.OrderModule.Activities.NotificationActivity import (
    send_order_confirmation,
    send_order_cancelled,
    NotificationInput,
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

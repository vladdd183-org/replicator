"""Inventory service integration task.

Provides inventory reservation and release operations
for the order creation saga.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

import logfire
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Task import Task
from src.Containers.AppSection.OrderModule.Errors import (
    InventoryError,
    InsufficientInventoryError,
    InventoryReservationFailedError,
    InventoryServiceUnavailableError,
)


class InventoryItem(BaseModel):
    """Item to reserve in inventory."""
    
    product_id: UUID
    quantity: int
    product_name: str | None = None


class ReserveInventoryInput(BaseModel):
    """Input for inventory reservation.
    
    Attributes:
        order_id: Order UUID (for tracking)
        items: Items to reserve
    """
    
    order_id: UUID
    user_id: UUID
    items: list[InventoryItem]


class ReservationResult(BaseModel):
    """Result of inventory reservation.
    
    Attributes:
        reservation_id: Unique reservation identifier
        reserved_items: Items that were reserved
        expires_at: When reservation expires
    """
    
    reservation_id: str
    order_id: UUID
    reserved_items: list[InventoryItem]
    expires_at: str | None = None


@dataclass
class InventoryTask(Task[ReserveInventoryInput, Result[ReservationResult, InventoryError]]):
    """Task for inventory operations.
    
    Integrates with inventory service to reserve and release stock.
    In production, this would call an external inventory microservice.
    
    For demonstration, this simulates the inventory service behavior.
    """
    
    # Configuration
    reservation_ttl_minutes: int = 30
    
    # Simulated inventory (in production, this would be an API client)
    _available_stock: dict[UUID, int] = field(default_factory=dict)
    _reservations: dict[str, ReservationResult] = field(default_factory=dict)
    
    async def run(
        self,
        data: ReserveInventoryInput,
    ) -> Result[ReservationResult, InventoryError]:
        """Reserve inventory for an order.
        
        Args:
            data: Reservation request with items
            
        Returns:
            Result with reservation details or error
        """
        logfire.info(
            "📦 Reserving inventory",
            order_id=str(data.order_id),
            item_count=len(data.items),
        )
        
        try:
            # Simulate checking availability
            for item in data.items:
                available = self._available_stock.get(item.product_id, 100)  # Default 100 for demo
                
                if item.quantity > available:
                    logfire.warning(
                        "❌ Insufficient inventory",
                        product_id=str(item.product_id),
                        requested=item.quantity,
                        available=available,
                    )
                    return Failure(InsufficientInventoryError(
                        product_id=item.product_id,
                        requested=item.quantity,
                        available=available,
                    ))
            
            # Create reservation
            reservation_id = f"RES-{uuid4().hex[:12].upper()}"
            
            result = ReservationResult(
                reservation_id=reservation_id,
                order_id=data.order_id,
                reserved_items=data.items,
            )
            
            # Store reservation (in production, this would be API call)
            self._reservations[reservation_id] = result
            
            # Deduct from available stock
            for item in data.items:
                current = self._available_stock.get(item.product_id, 100)
                self._available_stock[item.product_id] = current - item.quantity
            
            logfire.info(
                "✅ Inventory reserved",
                reservation_id=reservation_id,
                order_id=str(data.order_id),
            )
            
            return Success(result)
            
        except Exception as e:
            logfire.exception(
                "💥 Inventory reservation failed",
                order_id=str(data.order_id),
                error=str(e),
            )
            return Failure(InventoryReservationFailedError(reason=str(e)))
    
    async def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel an inventory reservation.
        
        Called during saga compensation to release reserved stock.
        
        Args:
            reservation_id: Reservation to cancel
            
        Returns:
            True if cancelled successfully
        """
        logfire.info(
            "🔙 Cancelling inventory reservation",
            reservation_id=reservation_id,
        )
        
        try:
            reservation = self._reservations.pop(reservation_id, None)
            
            if reservation:
                # Return stock to available
                for item in reservation.reserved_items:
                    current = self._available_stock.get(item.product_id, 0)
                    self._available_stock[item.product_id] = current + item.quantity
                
                logfire.info(
                    "✅ Reservation cancelled",
                    reservation_id=reservation_id,
                )
                return True
            
            logfire.warning(
                "⚠️ Reservation not found (may already be cancelled)",
                reservation_id=reservation_id,
            )
            return True  # Idempotent - already cancelled is OK
            
        except Exception as e:
            logfire.exception(
                "💥 Failed to cancel reservation",
                reservation_id=reservation_id,
                error=str(e),
            )
            raise
    
    async def get_reservation(self, reservation_id: str) -> ReservationResult | None:
        """Get reservation details.
        
        Args:
            reservation_id: Reservation to look up
            
        Returns:
            Reservation details if found
        """
        return self._reservations.get(reservation_id)


# Factory function for DI
def create_inventory_task() -> InventoryTask:
    """Create InventoryTask instance."""
    return InventoryTask()


__all__ = [
    "InventoryTask",
    "InventoryItem",
    "ReserveInventoryInput",
    "ReservationResult",
    "create_inventory_task",
]

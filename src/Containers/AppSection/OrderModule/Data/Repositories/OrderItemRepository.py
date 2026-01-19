"""OrderItem repository for database operations."""

from decimal import Decimal
from uuid import UUID

from src.Containers.AppSection.OrderModule.Models.OrderItem import OrderItem


class OrderItemRepository:
    """Repository for OrderItem entity.
    
    Provides data access methods for order items.
    """
    
    async def add(self, item: OrderItem) -> OrderItem:
        """Add a new order item.
        
        Args:
            item: OrderItem entity to persist
            
        Returns:
            Persisted order item
        """
        # Calculate subtotal before saving
        item.subtotal = item.calculate_subtotal()
        await item.save()
        return item
    
    async def add_many(self, items: list[OrderItem]) -> list[OrderItem]:
        """Add multiple order items.
        
        Args:
            items: List of OrderItem entities
            
        Returns:
            List of persisted items
        """
        for item in items:
            item.subtotal = item.calculate_subtotal()
        await OrderItem.insert(*items)
        return items
    
    async def get(self, item_id: UUID) -> OrderItem | None:
        """Get order item by ID.
        
        Args:
            item_id: UUID of the order item
            
        Returns:
            OrderItem if found, None otherwise
        """
        return await OrderItem.select().where(OrderItem.id == item_id).first()
    
    async def get_by_order(self, order_id: UUID) -> list[OrderItem]:
        """Get all items for an order.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            List of order items
        """
        return await OrderItem.select().where(OrderItem.order == order_id)
    
    async def delete(self, item_id: UUID) -> bool:
        """Delete an order item.
        
        Args:
            item_id: UUID of the item to delete
            
        Returns:
            True if deleted
        """
        result = await OrderItem.delete().where(OrderItem.id == item_id)
        return result is not None
    
    async def delete_by_order(self, order_id: UUID) -> int:
        """Delete all items for an order.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Number of items deleted
        """
        result = await OrderItem.delete().where(OrderItem.order == order_id)
        return result if result else 0
    
    async def calculate_order_total(self, order_id: UUID) -> Decimal:
        """Calculate total amount for all items in an order.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Total amount
        """
        result = await OrderItem.raw(
            """
            SELECT COALESCE(SUM(subtotal), 0) as total
            FROM order_items
            WHERE order = {}
            """,
            order_id,
        )
        return Decimal(str(result[0]["total"])) if result else Decimal("0.00")
    
    async def get_item_count(self, order_id: UUID) -> int:
        """Get number of items in an order.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Item count
        """
        return await OrderItem.count().where(OrderItem.order == order_id)
    
    async def get_total_quantity(self, order_id: UUID) -> int:
        """Get total quantity of all items in an order.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Total quantity
        """
        result = await OrderItem.raw(
            """
            SELECT COALESCE(SUM(quantity), 0) as total
            FROM order_items
            WHERE order = {}
            """,
            order_id,
        )
        return int(result[0]["total"]) if result else 0

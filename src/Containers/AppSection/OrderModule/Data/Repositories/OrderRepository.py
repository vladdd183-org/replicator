"""Order repository for database operations."""

from decimal import Decimal
from uuid import UUID

from src.Containers.AppSection.OrderModule.Models.Order import Order, OrderStatus


class OrderRepository:
    """Repository for Order entity.
    
    Provides data access methods for orders including CRUD operations
    and specialized queries.
    """
    
    async def add(self, order: Order) -> Order:
        """Add a new order to the database.
        
        Args:
            order: Order entity to persist
            
        Returns:
            Persisted order with generated ID
        """
        await order.save()
        return order
    
    async def get(self, order_id: UUID) -> Order | None:
        """Get order by ID.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Order if found, None otherwise
        """
        return await Order.select().where(Order.id == order_id).first()
    
    async def get_with_items(self, order_id: UUID) -> Order | None:
        """Get order with its items.
        
        Args:
            order_id: UUID of the order
            
        Returns:
            Order with items loaded, None if not found
        """
        order = await self.get(order_id)
        if order:
            # Items are loaded via foreign key relationship
            from src.Containers.AppSection.OrderModule.Models.OrderItem import OrderItem
            items = await OrderItem.select().where(OrderItem.order == order_id)
            order._items = items  # Attach for convenience
        return order
    
    async def update(self, order: Order) -> Order:
        """Update an existing order.
        
        Args:
            order: Order entity with updated fields
            
        Returns:
            Updated order
        """
        await order.save()
        return order
    
    async def update_status(
        self,
        order_id: UUID,
        status: OrderStatus,
    ) -> bool:
        """Update order status.
        
        Args:
            order_id: UUID of the order
            status: New status
            
        Returns:
            True if updated, False if order not found
        """
        result = await Order.update({
            Order.status: status.value,
        }).where(Order.id == order_id)
        return result is not None
    
    async def delete(self, order_id: UUID) -> bool:
        """Delete an order.
        
        Args:
            order_id: UUID of the order to delete
            
        Returns:
            True if deleted, False if not found
        """
        result = await Order.delete().where(Order.id == order_id)
        return result is not None
    
    async def find_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        """Find orders by user ID.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of orders for the user
        """
        return await Order.select().where(
            Order.user_id == user_id
        ).order_by(
            Order.created_at, ascending=False
        ).limit(limit).offset(offset)
    
    async def find_by_status(
        self,
        status: OrderStatus,
        limit: int = 100,
    ) -> list[Order]:
        """Find orders by status.
        
        Args:
            status: Status to filter by
            limit: Maximum number of results
            
        Returns:
            List of orders with the specified status
        """
        return await Order.select().where(
            Order.status == status.value
        ).limit(limit)
    
    async def find_pending_orders(self, limit: int = 100) -> list[Order]:
        """Find orders pending processing.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of pending orders
        """
        return await self.find_by_status(OrderStatus.PENDING, limit)
    
    async def count_by_user(self, user_id: UUID) -> int:
        """Count orders for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Number of orders
        """
        result = await Order.count().where(Order.user_id == user_id)
        return result
    
    async def get_user_total_spending(self, user_id: UUID) -> Decimal:
        """Calculate total spending for a user.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            Total amount spent (completed orders only)
        """
        result = await Order.raw(
            """
            SELECT COALESCE(SUM(total_amount), 0) as total
            FROM orders
            WHERE user_id = {} AND status IN ('confirmed', 'shipped', 'delivered')
            """,
            user_id,
        )
        return Decimal(str(result[0]["total"])) if result else Decimal("0.00")
    
    async def exists(self, order_id: UUID) -> bool:
        """Check if order exists.
        
        Args:
            order_id: UUID to check
            
        Returns:
            True if order exists
        """
        return await Order.exists().where(Order.id == order_id)
    
    async def set_reservation_id(
        self,
        order_id: UUID,
        reservation_id: str,
    ) -> bool:
        """Set inventory reservation ID for order.
        
        Args:
            order_id: UUID of the order
            reservation_id: Inventory reservation reference
            
        Returns:
            True if updated
        """
        result = await Order.update({
            Order.reservation_id: reservation_id,
        }).where(Order.id == order_id)
        return result is not None
    
    async def set_payment_id(
        self,
        order_id: UUID,
        payment_id: str,
    ) -> bool:
        """Set payment transaction ID for order.
        
        Args:
            order_id: UUID of the order
            payment_id: Payment transaction reference
            
        Returns:
            True if updated
        """
        result = await Order.update({
            Order.payment_id: payment_id,
        }).where(Order.id == order_id)
        return result is not None

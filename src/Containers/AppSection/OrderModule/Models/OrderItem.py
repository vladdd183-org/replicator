"""OrderItem database model.

Represents individual line items within an order.
"""

from decimal import Decimal

from piccolo.columns import UUID, Decimal as DecimalColumn, ForeignKey, Integer, Varchar
from piccolo.columns.defaults.uuid import UUID4
from piccolo.table import Table

from src.Containers.AppSection.OrderModule.Models.Order import Order


class OrderItem(Table):
    """Order item entity representing a single product in an order.
    
    Each order can have multiple items with quantity and pricing.
    
    Attributes:
        id: Unique item identifier
        order: Reference to parent order
        product_id: Product being ordered
        product_name: Product name snapshot (for historical accuracy)
        quantity: Number of units ordered
        unit_price: Price per unit at time of order
        subtotal: Calculated total for this line item
    """
    
    # Primary key
    id = UUID(default=UUID4(), primary_key=True)
    
    # Parent order reference
    order = ForeignKey(references=Order, on_delete="CASCADE")
    
    # Product information (snapshot at order time)
    product_id = UUID(null=False, index=True)
    product_name = Varchar(length=255, null=False)
    sku = Varchar(length=50, null=True)
    
    # Quantity and pricing
    quantity = Integer(default=1)
    unit_price = DecimalColumn(
        digits=(10, 2),
        default=Decimal("0.00"),
    )
    subtotal = DecimalColumn(
        digits=(12, 2),
        default=Decimal("0.00"),
    )
    
    class Meta:
        tablename = "order_items"
    
    def __str__(self) -> str:
        return f"OrderItem({self.product_name}, qty={self.quantity})"
    
    def calculate_subtotal(self) -> Decimal:
        """Calculate subtotal from quantity and unit price."""
        return Decimal(str(self.quantity)) * self.unit_price

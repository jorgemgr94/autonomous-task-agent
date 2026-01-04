"""Order management tool."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class CreateOrderInput(BaseModel):
    """Input schema for create_order tool."""

    product_id: str = Field(..., description="The product ID to order")
    quantity: int = Field(..., ge=1, le=100, description="Quantity to order (1-100)")
    customer_id: str = Field(..., description="The customer ID placing the order")


class CreateOrderTool(BaseTool):
    """Create a new order in the system."""

    name = "create_order"
    description = "Create a new order for a product"
    has_side_effects = True  # This modifies external state

    def execute(self, **kwargs: Any) -> ToolResult:
        # Validate input
        try:
            inputs = CreateOrderInput(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=f"Invalid input: {e}")

        # Simulate order creation
        # NOTE: Here we are simulating the order creation.
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        return ToolResult(
            success=True,
            data={
                "order_id": order_id,
                "product_id": inputs.product_id,
                "quantity": inputs.quantity,
                "customer_id": inputs.customer_id,
                "status": "created",
            },
        )

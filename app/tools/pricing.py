"""Pricing tool for product lookups."""

from typing import Any

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class GetPricingInput(BaseModel):
    """Input schema for get_pricing tool."""

    product_id: str = Field(..., description="The product ID to look up")


# Mock products
PRODUCTS = {
    "PROD-001": {"name": "Basic Widget", "price": 29.99, "currency": "USD"},
    "PROD-002": {"name": "Pro Widget", "price": 99.99, "currency": "USD"},
    "PROD-003": {"name": "Enterprise Widget", "price": 299.99, "currency": "USD"},
}


class GetPricingTool(BaseTool):
    """Look up pricing information for a product."""

    name = "get_pricing"
    description = "Get pricing information for a product by its ID"
    has_side_effects = False

    def execute(self, **kwargs: Any) -> ToolResult:
        # Validate input
        try:
            inputs = GetPricingInput(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=f"Invalid input: {e}")

        # Look up product
        product = PRODUCTS.get(inputs.product_id)
        if product is None:
            return ToolResult(
                success=False,
                error=f"Product not found: {inputs.product_id}",
            )

        return ToolResult(
            success=True,
            data={
                "product_id": inputs.product_id,
                "name": product["name"],
                "price": product["price"],
                "currency": product["currency"],
            },
        )

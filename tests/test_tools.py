"""Tool system tests."""

from app.tools import registry
from app.tools.orders import CreateOrderTool
from app.tools.pricing import GetPricingTool


def test_registry_has_tools():
    """Registry should have all registered tools."""
    assert len(registry.tool_names) == 4
    assert "get_pricing" in registry.tool_names
    assert "create_order" in registry.tool_names
    assert "send_notification" in registry.tool_names
    assert "escalate_to_human" in registry.tool_names


def test_registry_get_tool():
    """Registry should return tools by name."""
    tool = registry.get("get_pricing")
    assert tool is not None
    assert tool.name == "get_pricing"


def test_registry_unknown_tool():
    """Registry should return None for unknown tools."""
    tool = registry.get("unknown_tool")
    assert tool is None


def test_get_pricing_tool_success():
    """GetPricingTool should return product info for valid ID."""
    tool = GetPricingTool()
    result = tool.execute(product_id="PROD-001")

    assert result.success is True
    assert result.data is not None
    assert result.data["product_id"] == "PROD-001"
    assert result.data["price"] == 29.99


def test_get_pricing_tool_not_found():
    """GetPricingTool should fail for unknown product."""
    tool = GetPricingTool()
    result = tool.execute(product_id="UNKNOWN")

    assert result.success is False
    assert result.error is not None
    assert "not found" in result.error.lower()


def test_get_pricing_tool_invalid_input():
    """GetPricingTool should fail for invalid input."""
    tool = GetPricingTool()
    result = tool.execute()  # Missing required product_id

    assert result.success is False
    assert result.error is not None


def test_create_order_tool_success():
    """CreateOrderTool should create order with valid input."""
    tool = CreateOrderTool()
    result = tool.execute(
        product_id="PROD-001",
        quantity=2,
        customer_id="CUST-100",
    )

    assert result.success is True
    assert result.data is not None
    assert result.data["product_id"] == "PROD-001"
    assert result.data["quantity"] == 2
    assert result.data["customer_id"] == "CUST-100"
    assert result.data["order_id"].startswith("ORD-")


def test_create_order_tool_invalid_quantity():
    """CreateOrderTool should fail for invalid quantity."""
    tool = CreateOrderTool()
    result = tool.execute(
        product_id="PROD-001",
        quantity=0,  # Invalid: must be >= 1
        customer_id="CUST-100",
    )

    assert result.success is False
    assert result.error is not None

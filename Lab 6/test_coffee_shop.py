import pytest
from coffee_shop_order import process_order_batch, check_espresso_machine

# Example test case:
def test_single_medium_coffee():
    orders = [
        {
            "paid": True,
            "size": "medium",
            "strict_allergy": False,
            "is_member": False,
            "customizations": [{"type": "standard", "cost": 0.5}]
        }
    ]
    result = process_order_batch(orders, 0.1)
    assert result["total"] == 5.5
    assert result["status"] == "COMPLETED"

# TODO: Add test cases to achieve 90-100% on both Line and Branch coverage!

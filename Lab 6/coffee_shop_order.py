import pytest
from coffee_shop_order import process_order_batch, check_espresso_machine


def make_order(**kwargs):
    order = {"paid": True, "size": "medium", "strict_allergy": False,
             "is_member": False, "customizations": []}
    order.update(kwargs)
    return order


# ---------- process_order_batch: line coverage ----------

def test_single_medium_coffee():
    orders = [make_order(customizations=[{"type": "standard", "cost": 0.5}])]
    result = process_order_batch(orders, 0.1)
    assert result["total"] == 5.5
    assert result["status"] == "COMPLETED"


def test_invalid_orders_type_raises():
    with pytest.raises(ValueError):
        process_order_batch("not a list", 0.1)


def test_unpaid_order_is_skipped():
    result = process_order_batch([make_order(paid=False)], 0.1)
    assert result == {"total": 0.0, "status": "NO_SALE"}


def test_small_and_large_sizes():
    orders = [make_order(size="small"), make_order(size="large")]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 9.0
    assert result["status"] == "COMPLETED"


def test_invalid_size_rejected():
    result = process_order_batch([make_order(size="huge")], 0.1)
    assert result == {"total": 0.0, "status": "NO_SALE"}


def test_negative_cost_customization_rejected():
    orders = [make_order(customizations=[{"type": "standard", "cost": -1.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 4.5


def test_allergen_alert_non_strict_keeps_order():
    orders = [make_order(customizations=[{"type": "allergen_alert", "cost": 0.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 4.5
    assert result["status"] == "COMPLETED"


def test_allergen_alert_strict_voids_item():
    orders = [make_order(strict_allergy=True,
                         customizations=[{"type": "allergen_alert", "cost": 0.0}])]
    result = process_order_batch(orders, 0.1)
    assert result == {"total": 0.0, "status": "NO_SALE"}


def test_syrup_cost_capped_at_1_50():
    orders = [make_order(customizations=[{"type": "syrup", "cost": 3.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 6.0


def test_syrup_under_cap_charged_fully():
    orders = [make_order(customizations=[{"type": "syrup", "cost": 1.0}])]
    result = process_order_batch(orders, 0.0)
    assert result["total"] == 5.5


def test_member_discount_applied():
    result = process_order_batch([make_order(is_member=True)], 0.0)
    assert result["total"] == 4.05


def test_audit_rejected_when_more_than_four_rejections():
    orders = [make_order(size="bad") for _ in range(5)] + [make_order()]
    result = process_order_batch(orders, 0.0)
    assert result["status"] == "AUDIT_REJECTED"
    assert result["total"] == 4.5


# ---------- check_espresso_machine: line coverage ----------

def test_machine_no_data():
    assert check_espresso_machine([]) == "NO_DATA"


def test_machine_shutdown_on_two_consecutive_overheats():
    assert check_espresso_machine([[90.0, 97.0, 98.0]]) == "SHUTDOWN"


def test_machine_optimal():
    assert check_espresso_machine([[90.0, 92.0], [95.0, 96.0]]) == "OPTIMAL"

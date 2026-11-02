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


# ---------- Extra tests: branch / condition coverage ----------

def test_negative_tax_rate_raises():
    # second operand of the `or` in the validation check
    with pytest.raises(ValueError):
        process_order_batch([make_order()], -0.01)


def test_zero_tax_rate_is_valid():
    # boundary: tax_rate == 0 must NOT raise
    assert process_order_batch([make_order()], 0)["total"] == 4.5


def test_empty_order_list_is_no_sale():
    assert process_order_batch([], 0.1) == {"total": 0.0, "status": "NO_SALE"}


def test_defaults_used_when_keys_missing():
    # no "size" -> medium, no "customizations" -> [], paid defaults False
    assert process_order_batch([{"paid": True}], 0.0)["total"] == 4.5
    assert process_order_batch([{}], 0.0)["status"] == "NO_SALE"


def test_customization_with_missing_fields_defaults():
    # type -> "" (else branch), cost -> 0.0
    orders = [make_order(customizations=[{}])]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_zero_cost_not_rejected_boundary():
    # cost == 0 is NOT < 0, so no rejection
    orders = [make_order(customizations=[{"type": "standard", "cost": 0.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 4.5


def test_syrup_exactly_at_cap_boundary():
    orders = [make_order(customizations=[{"type": "syrup", "cost": 1.5}])]
    assert process_order_batch(orders, 0.0)["total"] == 6.0


def test_strict_allergy_breaks_out_of_remaining_customizations():
    orders = [make_order(strict_allergy=True, customizations=[
        {"type": "allergen_alert", "cost": 0.0},
        {"type": "standard", "cost": 5.0}])]
    assert process_order_batch(orders, 0.0)["status"] == "NO_SALE"


def test_non_strict_allergy_continues_processing_other_mods():
    orders = [make_order(customizations=[
        {"type": "allergen_alert", "cost": 0.0},
        {"type": "standard", "cost": 1.0}])]
    assert process_order_batch(orders, 0.0)["total"] == 5.5


def test_exactly_four_rejections_is_not_audit():
    # boundary: rejected_items == 4 -> NOT > 4
    orders = [make_order(size="bad") for _ in range(4)] + [make_order()]
    assert process_order_batch(orders, 0.0)["status"] == "COMPLETED"


def test_audit_rejected_takes_priority_over_no_sale():
    orders = [make_order(size="bad") for _ in range(5)]
    result = process_order_batch(orders, 0.0)
    assert result == {"total": 0.0, "status": "AUDIT_REJECTED"}


def test_non_member_pays_full_price_and_member_discounted():
    orders = [make_order(is_member=False), make_order(is_member=True)]
    assert process_order_batch(orders, 0.0)["total"] == 4.5 + 4.05


def test_non_list_orders_with_valid_tax_raises():
    with pytest.raises(ValueError):
        process_order_batch(None, 0.1)


# ---------- espresso machine branches ----------

def test_machine_none_input_is_no_data():
    assert check_espresso_machine(None) == "NO_DATA"


def test_machine_empty_cycle_is_optimal():
    # inner loop with zero iterations
    assert check_espresso_machine([[]]) == "OPTIMAL"


def test_machine_streak_resets_between_overheats():
    # hot, cool, hot -> never 2 in a row
    assert check_espresso_machine([[97.0, 90.0, 97.0]]) == "OPTIMAL"


def test_machine_exactly_96_is_not_overheat():
    assert check_espresso_machine([[96.0, 96.0, 96.0]]) == "OPTIMAL"


def test_machine_streak_resets_between_cycles():
    # single hot reading at end of one cycle and start of next must not combine
    assert check_espresso_machine([[90.0, 97.0], [97.0, 90.0]]) == "OPTIMAL"


def test_machine_shutdown_in_later_cycle():
    assert check_espresso_machine([[90.0], [97.0, 98.0]]) == "SHUTDOWN"

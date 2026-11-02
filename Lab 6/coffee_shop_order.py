def process_order_batch(orders, tax_rate):
    if not isinstance(orders, list) or tax_rate < 0:
        raise ValueError("Invalid orders list or tax rate")

    batch_total = 0.0
    rejected_items = 0

    for order in orders:
        if not order.get("paid", False):
            continue

        size = order.get("size", "medium")
        if size == "small":
            base_price = 3.0
        elif size == "medium":
            base_price = 4.5
        elif size == "large":
            base_price = 6.0
        else:
            rejected_items += 1
            continue

        item_total = base_price
        customizations = order.get("customizations", [])

        for mod in customizations:
            mod_type = mod.get("type", "")
            cost = mod.get("cost", 0.0)

            if cost < 0:
                rejected_items += 1
                continue

            if mod_type == "allergen_alert":
                rejected_items += 1
                if order.get("strict_allergy", False):
                    item_total = 0.0
                    break
            elif mod_type == "syrup":
                item_total += cost if cost <= 1.5 else 1.5
            else:
                item_total += cost

        if order.get("is_member", False):
            item_total *= 0.90

        batch_total += item_total

    final_total = batch_total * (1 + tax_rate)

    if rejected_items > 4:
        return {"total": round(final_total, 2), "status": "AUDIT_REJECTED"}
    if batch_total == 0.0:
        return {"total": 0.0, "status": "NO_SALE"}
    return {"total": round(final_total, 2), "status": "COMPLETED"}


def check_espresso_machine(temperature_cycles):
    if not temperature_cycles:
        return "NO_DATA"

    for cycle in temperature_cycles:
        overheat_streak = 0
        for temp in cycle:
            if temp > 96.0:
                overheat_streak += 1
                if overheat_streak >= 2:
                    return "SHUTDOWN"
            else:
                overheat_streak = 0
    return "OPTIMAL"

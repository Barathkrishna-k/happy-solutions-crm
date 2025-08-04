def compute_quote(payload):
    LABOUR_COST_PER_HOUR_MAP = {
        "Studio": 80, "1 BHK": 80, "2 BHK": 120, "3 BHK": 140,
        "4 BHK": 160, "5 BHK": 180, "6 BHK": 180,
    }

    distance = float(payload.get("distance_km", 0))
    truck_size = (payload.get("truck_size") or "").upper()
    packing_hours = float(payload.get("packing_hours", 0))
    packing_rate = float(payload.get("packing_rate", 0))
    weight_kg = float(payload.get("weight_kg", 0))
    toll_fee = float(payload.get("toll_fee", 0))
    labour_hours = float(payload.get("labour_hours", 0))
    type_of_house = payload.get("type_of_house")
    inventory_items = payload.get("inventory_items", []) or []
    inventory_total = sum([(float(i.get("qty",0))*float(i.get("unit_price",0))) for i in inventory_items])

    small = {"4T", "6T"}
    large = {"8T", "10T", "12T", "14T", "18T"}
    if truck_size in small:
        truck_charge = (distance * 0.5 * 0.3) + (distance * (1/3)) * 0.3
    elif truck_size in large:
        truck_charge = (distance * 0.5 * 1.81) + (distance * (1/3)) * 1.81
    else:
        truck_charge = 0.0

    packing_charge = packing_hours * packing_rate
    weight_charge = weight_kg * 0.8
    insurance = 0.025 * weight_charge
    labour_cost_per_hour = LABOUR_COST_PER_HOUR_MAP.get(type_of_house, 0)
    labour_charge = labour_hours * labour_cost_per_hour

    subtotal = truck_charge + packing_charge + insurance + labour_charge + toll_fee + inventory_total
    gst = 0.10 * subtotal
    total = subtotal + gst

    return {
        "charges": {
            "truck": round(truck_charge, 2),
            "packing": round(packing_charge, 2),
            "weight": round(weight_charge, 2),
            "insurance": round(insurance, 2),
            "labour": round(labour_charge, 2),
            "toll": round(toll_fee, 2),
            "inventoryTotal": round(inventory_total, 2),
        },
        "subtotal": round(subtotal, 2),
        "gst": round(gst, 2),
        "total": round(total, 2)
    }

import pulp
import re
import sqlite3
import os

DATABASE = 'db/fake_basketroute.db'

def create_connection():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), DATABASE)
    conn = sqlite3.connect(db_path)
    return conn

def translate_ip_result_to_plan(result, items, stores):
    """
    Translate the integer programming result into a human-readable shopping plan.
    :param result: Dictionary with keys 'plan' (list of tuples (store_id, item_id, quantity)) and 'total_cost'
    :param items: List of item details (dicts with 'id' and 'name')
    :param stores: List of store details (dicts with 'id' and 'name')
    :return: dictionary by store with items and quantities to buy and total cost 
    """
    plan = {}
    item_dict = {item['id']: item['name'] for item in items}
    store_dict = {store['id']: store['name'] for store in stores}
    for store_id, item_id, quantity in result['plan']:
        plan[store_dict[store_id]] = plan.get(store_dict[store_id], [])
        plan[store_dict[store_id]].append({
            'item': item_dict[item_id],
            'quantity': quantity
        })
    return {
        'plan': plan,
        'cost': result['total_cost'],
        'status': result['status']
    }

def optimize(store_item_prices, item_requirements, max_stores=5):
    """
    Optimize the shopping plan to minimize cost while ensuring each item is bought from exactly one store.
    
    :param store_item_prices: List of tuples (store_id, item_id, price, inventory)
    :param item_requirements: List of integers corresponding to the required quantity for each item
    :return: Dictionary with the optimal shopping plan and total cost

    requires:
        len(store_item_prices) == len(item_requirements)
    """
    
    # Validate inputs
    if not isinstance(store_item_prices, list) or not all(isinstance(x, tuple) for x in store_item_prices):
        raise ValueError("store_item_prices must be a list of tuples (store, item, price, inventory)")
    
    return assignmentSolver(store_item_prices, item_requirements, max_stores)

def assignmentSolver(store_item_prices, item_requirements, max_stores=5):
    # store_item_prices: [(store_id, item_id, price, inventory), …]
    # item_requirements: { item_id: required_qty, … }
    # max_stores: maximum distinct stores you may visit

    # 1) debug prints
    print(f"Store_item_prices: {store_item_prices}")
    print(f"Item requirements: {item_requirements}")
    print(f"Max stores: {max_stores}")

    # 2) collect distinct stores & items
    store_list = sorted({s for s, _, _, _ in store_item_prices})
    item_list  = sorted(item_requirements.keys())

    # 3) build price & inventory lookups
    price     = {(s,i): p for s,i,p,inv in store_item_prices}
    inventory = {(s,i): inv for s,i,p,inv in store_item_prices}

    # 4) only consider store-item pairs with positive inventory
    valid_pairs = [(s,i) for (s,i), inv in inventory.items() if inv > 0]

    # 5) set up LP
    prob = pulp.LpProblem("GroceryAssignment", pulp.LpMinimize)

    # integer: x[s,i] = how many units of item i to buy at store s
    x = pulp.LpVariable.dicts("Qty", valid_pairs, lowBound=0, cat="Integer")

    # binary: v[s] = 1 if we visit store s at all
    v = pulp.LpVariable.dicts("UseStore", store_list, cat="Binary")

    # 6) objective = sum over (s,i) of price × qty
    prob += pulp.lpSum(price[(s,i)] * x[(s,i)] for (s,i) in valid_pairs)

    # 7) inventory constraints
    for (s,i) in valid_pairs:
        prob += x[(s,i)] <= inventory[(s,i)], f"Inv_{s}_{i}"

    # 8) satisfy item requirements (allow splitting across stores)
    for i in item_list:
        supply_vars = [x[(s,i)] for s in store_list if (s,i) in inventory]
        prob += pulp.lpSum(supply_vars) >= item_requirements[i], f"Req_{i}"

    # 9) link quantity → store used
    for (s,i) in valid_pairs:
        # if we buy anything from s for item i, v[s] must be 1
        prob += x[(s,i)] <= item_requirements[i] * v[s], f"Link_{s}_{i}"

    # 10) cap the number of stores
    prob += pulp.lpSum(v[s] for s in store_list) <= max_stores, "MaxStores"

    # 11) solve quietly
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    # 12) extract plan
    status = pulp.LpStatus[prob.status]
    plan = []
    if status == "Optimal":
        for (s,i) in valid_pairs:
            qty = pulp.value(x[(s,i)])
            if qty and qty > 0.5:
                plan.append((s, i, int(qty)))

    total_cost = pulp.value(prob.objective)
    return {
        "plan":       plan,        # e.g. [(2, 49, 2), (8, 49, 1), (5,  2, 1), …]
        "total_cost": total_cost, # float
        "status":     status      # e.g. "Optimal"
    }

if __name__ == "__main__":
    # Query database for store_item_prices, item_names, and store_names
    num = 5
    conn = create_connection()
    items = get_all_products(conn)[:num]
    requirements = [81, 2, 2, 2, 2]  # Example requirements for the first 5 items
    conn = create_connection()
    stores = get_all_stores(conn)

    # Use first 5 items and stores for testing
    conn = create_connection()
    store_item_prices = build_item_store_matrix(conn, items, stores)
    # Call the optimizer
    result = translate_ip_result_to_plan(optimize(store_item_prices, requirements), items, stores)

    print("We need to buy:")
    for i in range(num):
        print(f"  {requirements[i]} of {items[i]['name']}")

    print("\nOptimal shopping plan:")
    for store, purchases in result['plan'].items():
        print(f"At {store}, buy:")
        for purchase in purchases:
            # X of Y for $Z Each for a total of $W
            item = purchase['item']
            quantity = purchase['quantity']
            price_per_item = next((p for (s, i, p, inv) in store_item_prices if s == next(sid for sid, sname in [(st['id'], st['name']) for st in stores] if sname == store) and i == next(iid for iid, iname in [(it['id'], it['name']) for it in items] if iname == item)), None)
            total_price = price_per_item * quantity
            print(f"  - {quantity} of {item} for ${price_per_item:.2f} each, total ${total_price:.2f}")
    print(f"\nTotal cost: ${result['total_cost']:.2f}")
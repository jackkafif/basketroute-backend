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
        'total_cost': result['total_cost'],
        'status': result['status']
    }

def optimize(store_item_prices, item_requirements):
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
    
    return assignmentSolver(store_item_prices, item_requirements)

def assignmentSolver(store_item_prices, item_requirements):
    # Build ordered list of items from store_item_prices
    item_list = sorted(list({x[1] for x in store_item_prices}))
    store_list = sorted(list({x[0] for x in store_item_prices}))

    # Build mapping for price and inventory lookup
    price = {}
    inventory = {}
    for s, i, pr, inv in store_item_prices:
        price[(s, i)] = pr
        inventory[(s, i)] = inv

    # Find for each item which stores have it
    stores_for_item = {i: [] for i in item_list}
    for (s, i) in price:
        stores_for_item[i].append(s)

    # Decision variables: how many to buy from each store-item
    x = pulp.LpVariable.dicts("Buy", price.keys(), lowBound=0, cat='Integer')

    # Define the problem
    prob = pulp.LpProblem("GroceryShopping", pulp.LpMinimize)

    # Objective: Minimize total cost
    prob += pulp.lpSum([price[(s, i)] * x[(s, i)] for (s, i) in price])

    # Each item must be bought in required quantity
    for idx, i in enumerate(item_list):
        prob += pulp.lpSum([x[(s, i)] for s in stores_for_item[i]]) >= item_requirements[idx]

    # Cannot exceed inventory in any store for any item
    for (s, i) in price:
        prob += x[(s, i)] <= inventory[(s, i)]

    # Solve
    prob.solve()

    plan = []
    for (s, i) in x:
        qty = int(pulp.value(x[(s, i)]))
        if qty > 0:
            plan.append((s, i, qty))
    total_cost = pulp.value(prob.objective)

    return {
        "plan": plan,
        "total_cost": total_cost,
        "status": pulp.LpStatus[prob.status]
    }
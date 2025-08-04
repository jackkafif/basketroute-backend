import pulp
import re

def solve_shopping_ip(item_names, store_names, item_store_matrix, max_stores=3, min_stores=0):
    prob = pulp.LpProblem("GroceryShopping", pulp.LpMinimize)

    # Decision variable for each (item, store) pair: 1 if item bought at store, 0 otherwise
    item_store_vars = pulp.LpVariable.dicts(
        "ItemStore",
        ((item, store) for item in item_names for store in store_names),
        cat='Binary'
    )

    # Objective: Minimize total cost
    prob += pulp.lpSum(
        item_store_matrix[i]['stores'][j]['price'] * item_store_vars[(item_names[i], store_names[j])]
        for i in range(len(item_names))
        for j in range(len(store_names))
    ), "TotalCost"

    # Each item must be bought from exactly one store (with inventory > 0)
    for i, item in enumerate(item_names):
        prob += pulp.lpSum(
            item_store_vars[(item, store_names[j])]
            for j in range(len(store_names))
            if item_store_matrix[i]['stores'][j]['inventory'] > 0
        ) == 1, f"Item_{item}_Constraint"

    # Can only buy an item from a store if that store has inventory (binary or not)
    for i, item in enumerate(item_names):
        for j, store in enumerate(store_names):
            if item_store_matrix[i]['stores'][j]['inventory'] == 0:
                prob += item_store_vars[(item, store)] == 0, f"NoInventory_{item}_{store}"

    # Store is visited if any item is bought there
    store_vars = pulp.LpVariable.dicts("Store", store_names, cat='Binary')
    for store in store_names:
        for item in item_names:
            prob += item_store_vars[(item, store)] <= store_vars[store], f"Link_{item}_{store}"

    # Maximum number of stores to visit
    prob += pulp.lpSum([store_vars[store] for store in store_names]) <= max_stores, "MaxStoresConstraint"

    # Minimum number of stores to visit (optional, for testing)
    if min_stores is not None:
        prob += pulp.lpSum([store_vars[store] for store in store_names]) >= min_stores, "MinStoresConstraint"

    # Solve the problem
    prob.solve()
    print("Status:", pulp.LpStatus[prob.status])

    # Collect results
    total_cost = pulp.value(prob.objective)
    plans = []
    for v in prob.variables():
        if v.varValue and v.varValue > 0:
            plans.append((v.name, v.varValue))
    return plans, total_cost
def translate_ip_result_to_plan(ip_result):
    """
    Input: List of tuples (variable_name, value)
    Output: Dictionary mapping store names to list of items to buy there
    """
    plan = {}
    # Pattern extracts two groups inside parentheses, accounting for spaces, underscores, and quotes
    pattern = r"ItemStore_\('([^']+)',_?'([^']+)'\)"

    for var_name, value in ip_result:
        if value > 0 and var_name.startswith("ItemStore_"):
            match = re.match(pattern, var_name)
            if match:
                item = match.group(1).replace('_', ' ')
                store = match.group(2).replace('_', ' ')
                if store not in plan:
                    plan[store] = []
                plan[store].append(item)
            else:
                print(f"Warning: could not parse variable name: {var_name}")

    return plan

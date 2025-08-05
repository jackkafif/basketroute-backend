import pulp
from geopy.distance import geodesic

def optimize_path(stores, starting_point=None):
    if not stores:
        return []

    # if no explicit start, use the first store
    if starting_point is None:
        starting_point = (stores[0]['lat'], stores[0]['lon'])

    # build locations list: 0 = start, 1..n-1 = stores
    num_locations = len(stores) + 1
    locations = [starting_point] + [(s['lat'], s['lon']) for s in stores]

    # distance matrix
    distance_matrix = [[0.0]*num_locations for _ in range(num_locations)]
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = geodesic(locations[i], locations[j]).meters

    # set up the LP
    prob = pulp.LpProblem("Open_TSP", pulp.LpMinimize)
    x = pulp.LpVariable.dicts(
        "x",
        ((i, j)
         for i in range(num_locations)
         for j in range(num_locations)
         if i != j),
        cat="Binary"
    )
    # only one u‐var per store (1..n-1), domain [1..n-1]
    u = pulp.LpVariable.dicts(
        "u",
        (i for i in range(1, num_locations)),
        lowBound=1,
        upBound=num_locations - 1,
        cat="Continuous"
    )

    # objective: total travel distance
    prob += pulp.lpSum(distance_matrix[i][j] * x[i, j]
                       for (i, j) in x)

    # ---- start‐node constraints ----
    # exactly one arc out of start
    prob += pulp.lpSum(x[0, j] for j in range(1, num_locations)) == 1
    # no arcs back into start
    prob += pulp.lpSum(x[j, 0] for j in range(1, num_locations)) == 0

    # ---- store‐node constraints ----
    for i in range(1, num_locations):
        # exactly one incoming arc to each store
        prob += pulp.lpSum(x[j, i]
                           for j in range(num_locations) if j != i) == 1
        # at most one outgoing arc from each store
        prob += pulp.lpSum(x[i, j]
                           for j in range(num_locations) if i != j) <= 1

    # force exactly (n-2) total outgoing arcs from stores,
    # so exactly one store ends the path
    prob += (
        pulp.lpSum(x[i, j]
                   for i in range(1, num_locations)
                   for j in range(num_locations)
                   if i != j)
        == num_locations - 2
    )

    # ---- MTZ subtour‐elimination (only among stores) ----
    for i in range(1, num_locations):
        for j in range(1, num_locations):
            if i != j:
                prob += (
                    u[i]
                    - u[j]
                    + (num_locations - 1) * x[i, j]
                    <= num_locations - 2
                )

    # solve
    prob.solve()

    # check status
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return []

    # rebuild the path
    path = []
    current = 0
    while True:
        # find the one arc out of current
        nxt = next(
            (j for j in range(num_locations)
             if j != current
             and (current, j) in x
             and pulp.value(x[current, j]) > 0.5),
            None
        )
        if nxt is None or nxt == 0:
            break
        path.append(nxt)
        current = nxt

    # map back to stores (skip index 0)
    ordered = [stores[idx - 1] for idx in path]
    return {
        'ordered_stores': ordered,
        'total_distance_meters': pulp.value(prob.objective),
        'status': status
    }

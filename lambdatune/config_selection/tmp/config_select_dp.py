def find_all_orders(queries):
    if len(queries) == 1:
        return list([queries])

    orders = list()

    for query in queries:
        subset = set(queries)
        subset.remove(query)
        subset = list(subset)

        for order in find_all_orders(subset):
            order.insert(0, query)
            orders.append(order)

    return orders


def find_all_orders_optimized(queries, dependencies: dict, cost_map: dict):
    if len(queries) == 1:
        return list([queries])

    orders = list()

    # Queries to start exploring from
    starting_queries = list(queries)

    while len(starting_queries) > 0:
        query = starting_queries.pop(0)

        #print(f"Starting query: {query}")

        # Copy the cost map
        cost_map_cp = dict(cost_map)

        # Queries to consider (- the current query)
        subset = list(queries)
        subset.remove(query)

        # Update costs according to the current query
        for index in dependencies[query]:
            cost_map_cp[index] = 0

        # Find equivalent queries
        equivalent = list()
        for q in list(subset):
            cost = sum([cost_map_cp[index] for index in dependencies[q]])

            if cost == 0:
                if q in starting_queries:
                    starting_queries.remove(q)
                subset.remove(q)
                equivalent.append(q)

        #print(f"Pruned: {len(equivalent)}")

        subset = list(subset)

        if not subset:
            equivalent.insert(0, query)
            orders.append(equivalent)

        all_orders = find_all_orders_optimized(subset, dependencies, cost_map)

        for order in all_orders:
            for q in equivalent: order.insert(0, q)
            order.insert(0, query)
            orders.append(order)

    return orders

def compute_order_cost(order, dependencies, cost_map):
    n = len(order)
    cost = 0
    expected_cost = 0

    for query in order:
        for index in dependencies[query]:
            cost += cost_map[index]
            cost_map[index] = 0

        #print(f"Curr cost = {cost}, Adding: {cost / n}")
        expected_cost += cost / n

    return expected_cost


if __name__ == "__main__":

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


    dependencies_1 = {
        "Q1": set(A),
        "Q2": set(A),
        "Q3": set(B),
        "Q4": set(A),
        "Q5": set(A)
    }

    dependencies_2 = {
        "Q1": set(A),
        "Q2": set(A),
        "Q3": set({A, B}),
        "Q4": set(A),
        "Q5": set(B)
    }

    dependencies_3 = {
        "Q1": set(A),
        "Q2": set(A),
        "Q3": set({A, B}),
        "Q4": set(A),
        "Q5": set(B),
        "Q6": F
    }

    dependencies_4 = {
        "Q1": set(A),
        "Q2": set(B),
        "Q3": set(C),
        "Q4": set(D),
        "Q5": set(E)
    }

    cost_map = {
        A: 1,
        B: 1,
        C: 1,
        D: 1,
        E: 1,
        F: 6
    }

    queries = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    dependencies = dependencies_1


    all_orders = find_all_orders(queries)
    all_orders_optimized = find_all_orders_optimized(queries, dependencies, cost_map)

    print(len(all_orders))
    print(len(all_orders_optimized))

    all_orders = [(order, compute_order_cost(order, dependencies, dict(cost_map))) for order in all_orders]
    all_orders = sorted(all_orders, key=lambda k: k[1])

    all_orders_optimized = [(order, compute_order_cost(order, dependencies, dict(cost_map))) for order in all_orders_optimized]
    all_orders_optimized = sorted(all_orders_optimized, key=lambda k: k[1])

    print("---")
    for order in all_orders_optimized:
        print(order)




    # queries2cost = {}
    # for cardinality in range(1, nr_queries+1):
    #     for queries: all subsets of queries with given cardinality:
    #         min_cost = float('inf')
    #         for last_query in queries:
    #             prior_queries = queries - last_query
    #             prior_cost = queries2cost[prior_queries]
    #             total_cost = ...
    #             if total_cost < min_cost:
    #                 min_cost = total_cost
    #
    #         queries2cost[queries] = min_cost
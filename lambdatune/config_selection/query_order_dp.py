import sys
import logging

from itertools import combinations
from collections import defaultdict


class QuerySetMeta:
    """
    Helper class that contains methods for maintaining query-set metadata
    """
    def __init__(self, queries, index_dependencies, cost_map):
        """
        :param queries: The list of input queries
        :param index_dependencies: The map with the query->index-set dependencies
        :param cost_map: The cost map, i.e. cost of creating the index cost_map[index]
        """
        self.index_dependencies = index_dependencies
        self.cost_map = cost_map
        self.query_to_index = dict()
        self.query_set_to_indexes = dict()

        # Keeps the best order and cost found for a query set
        # TODO: Use these to store the best order and costs; Implement the corresponding methods
        self.best_order = dict()
        self.best_cost = dict()

        # Assign each query a unique id
        idx = 0
        for query in sorted(queries):
            self.query_to_index[query] = idx
            idx += 1

    def add_new_order(self, query_set, order, cost):
        key = self.get_query_set_mask(query_set)

        if cost < self.best_cost[key]:
            self.best_cost[key] = cost
            self.best_order[key] = order

    def get_best_solution(self, query_set):
        key = self.get_query_set_mask(query_set)

        return self.best_order[key], self.best_cost[key]


    def get_query_id(self, query: str):
        return self.query_to_index[query]

    def get_query_set_mask(self, queries: set):
        query_ids = [self.query_to_index[q] for q in queries]

        mask = 0
        for query_id in query_ids:
            mask = mask | (1 << query_id)

        # Readable version of the mask (#TODO remove)
        mask_readable = "{:08b}".format(mask)

        return mask

    def add_query_set(self, query_set):
        """
        Adds a new query set. For every query in the query_set, it updates the query_set_to_indexes[query]. Thus,
        it maintains the union of all the indexes for all the queries in the query set.
        :param query_set: The query set
        :return: None
        """
        mask = self.get_query_set_mask(query_set)
        self.query_set_to_indexes[mask] = set()

        for query in query_set:
            query_indexes = self.index_dependencies[query]
            self.query_set_to_indexes[mask] = self.query_set_to_indexes[mask].union(query_indexes)

    def add_query_to_query_set(self, query, set_mask):
        """
        Adds a new query (and query set). Probably #TODO: Remove
        :param query:
        :param set_mask:
        :return:
        """
        query_id = self.query_to_index[query]

        new_set_mask = set_mask | (1 << query_id)
        new_set_indexes = set(self.query_set_to_indexes[set_mask])

        for index in self.index_dependencies[query]:
            new_set_indexes.add(index)

        self.query_set_to_indexes[new_set_mask] = new_set_indexes

    def get_query_cost(self, subset_mask, query):
        """
        Given a query subset (executed queries) it computes the cost of the new query
        :param subset_mask: The mask of the set of the already executed queries
        :param query: The new query to be added
        :return: The cost of executing the new query
        """

        if subset_mask == 0:
            # This is the first query to be executed
            required_indexes = self.index_dependencies[query]
        else:
            # Get the required indexes for that query
            query_indexes = self.index_dependencies[query]

            # Remove the indexes that have been already created in the current query subset
            required_indexes = query_indexes.difference(self.query_set_to_indexes[subset_mask])

        c = 0

        for index in required_indexes:
            if index not in self.cost_map:
                raise Exception(f"Index {index} did not found in the cost map")
            c += self.cost_map[index]

        return c


def compute_optimal_order(queries, index_dependencies, cost_map, frequency: dict=None):
    meta = QuerySetMeta(queries, index_dependencies, cost_map)

    if frequency:
        n = sum(frequency.values())
    else:
        n = len(queries)

    dp_cost = defaultdict(int)
    dp_order = defaultdict(list)
    dp_cost_numerator = defaultdict(int)

    subset_mask = None

    # Initialize with individual queries (sets of cardinality = 1)
    for query in queries:
        query_mask = meta.get_query_set_mask([query])
        meta.add_query_set([query])

        dp_cost[query_mask] = (meta.get_query_cost(0, query) / n)

        if frequency and query in frequency:
            dp_cost[query_mask] = dp_cost[query_mask] * (frequency[query])

        dp_cost_numerator[query_mask] = meta.get_query_cost(0, query)
        dp_order[query_mask] = [query]

    # Enumerate all subsets of cardinality i
    for i in range(2, n + 1):
        subsets = list(combinations(queries, i))

        logging.debug(f"#Subsets: {len(subsets)}")

        for subset in subsets:
            subset_mask = meta.get_query_set_mask(subset)
            subset_mask_readable = "{:08b}".format(subset_mask)

            meta.add_query_set(subset)

            ans = sys.maxsize
            best_order = None

            for query in subset:
                # For each query in the subset, try removing a query q
                # Try out subtracting every query from the subset, and adding it again using the optimal cost
                # of the previously computed {subset} - {query}.
                subset_without_query = subset_mask & ~(1 << meta.get_query_id(query))

                query_cost = meta.get_query_cost(subset_without_query, query)

                new_total_cost = (dp_cost_numerator[subset_without_query] + query_cost) / n

                if frequency and query in frequency:
                    new_total_cost += ((dp_cost_numerator[subset_without_query] + query_cost) / n) * (frequency[query] - 1)

                # Compute the cost as the sum of the optimal cost of the queries {subset} - {query}
                cost = dp_cost[subset_without_query] + new_total_cost

                # Keep the best cost
                if cost < ans:
                    ans = cost
                    # Keep the associated sub-order
                    order = list(dp_order[subset_without_query])
                    order.append(query)
                    best_order = order
                    cost_numerator = dp_cost_numerator[subset_without_query] + query_cost

            dp_cost[subset_mask] = ans
            dp_order[subset_mask] = best_order
            dp_cost_numerator[subset_mask] = cost_numerator

        logging.debug(f"Finished with subset of size: {i}")

    return dp_cost[subset_mask], dp_order[subset_mask]


def compute_order_cost(order, index_dependencies, cost_map, frequency: dict):
    """
    Computes the cost of a given order
    :param order: The order
    :param index_dependencies: The index dependencies
    :param cost_map: The cost map
    :return: The cost of the order
    """
    cost = 0
    numerator = 0
    created_indexes = set()

    if frequency:
        n = sum(frequency.values())
    else:
        n = len(order)

    for query in order:
        required_indexes = index_dependencies[query].difference(created_indexes)
        created_indexes = created_indexes.union(required_indexes)

        numerator += sum(cost_map[index] for index in required_indexes)

        cost += numerator / n

        if frequency and query in frequency:
            cost += (frequency[query] - 1) * (numerator / n)

    return cost
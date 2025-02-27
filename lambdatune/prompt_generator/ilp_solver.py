from collections import defaultdict

import tiktoken
from gurobipy import GRB, Model
from lambdatune.utils import get_llm

# encoding = tiktoken.encoding_for_model(get_llm())
encoding = None

def optimize(conditions: list, token_budget: int):
    """
    Value = frequency * estimated cost
    Weight = #tokens
    """
    values = [d[1] * d[2] for d in conditions]
    weights = list()

    for condition in conditions:
        weight = len(condition)#len(encoding.encode(condition[0]))
        weights.append(weight)

    m = Model("knapsack")
    m.setParam("OutputFlag", 0)

    # Create variables
    x = m.addVars(len(weights), vtype=GRB.BINARY, name="x")

    # Set the objective: maximize the total value
    m.setObjective(sum(values[i] * x[i] for i in range(len(values))), GRB.MAXIMIZE)

    # Add constraint: the sum of the weights should be less than or equal to the max_weight
    m.addConstr(
        sum(weights[i] * x[i] for i in range(len(weights))) <= token_budget, "c"
    )

    # Optimize the model
    m.optimize()

    selected_conditions = list()
    for i in range(len(weights)):
        if x[i].x == 1.0:
            selected_conditions.append(conditions[i])

    return selected_conditions


class ILPSolver:
    def __init__(self):
        self.key_to_idx = defaultdict(list)
        self.idx_to_key = dict()

    def extract_dependencies(self, conditions: dict):
        dependencies = defaultdict(set)

        conditions = conditions.items()
        idx = 0

        values = list()
        costs = list()

        # Keeps track of the added conditions taking into account symmetry (a=b == b=a)
        added_conditions = set()

        # Creates condition dependencies by grouping them by the left
        # join key using a dictionary.
        # For example, for the following joins: a=b, a=c, a=d
        # there will be a record dependencies[a] = [b, c, d]
        #
        # At the same time, it assigns a unique id to each column. For instance, for the example above
        # it will assign the following IDs: a->0, b->1, c->2, d->3
        for condition_set in conditions:
            left_key = condition_set[0]

            if left_key not in self.key_to_idx:
                self.key_to_idx[left_key] = list()

            left_key_idx = idx
            self.key_to_idx[left_key].append(idx)
            self.idx_to_key[idx] = left_key
            idx += 1

            # The value of the left key alone is zero
            values.append(0)

            # The cost of the left key is its number of tokens
            # costs.append(len(encoding.encode(left_key)))
            costs.append(len(left_key))

            right_keys = sorted(condition_set[1], key=lambda x: x[0])

            for pair in right_keys:
                key = pair[0]
                value = pair[1]

                right_key_idx = idx
                self.key_to_idx[key].append(idx)
                self.idx_to_key[idx] = key
                idx += 1

                dependencies[left_key_idx].add(right_key_idx)

                values.append(value)
                # costs.append(len(encoding.encode(key)))
                costs.append(len(key))

        return dependencies, costs, values

    def optimize_with_dependencies(self, conditions: dict, token_budget: int):
        # Reset key_to_idx
        self.key_to_idx = defaultdict(list)

        dependencies, weights, values = self.extract_dependencies(conditions)

        m = Model("knapsack")
        m.setParam("OutputFlag", 0)

        # Create variables
        x = m.addVars(len(weights), vtype=GRB.BINARY, name="x")

        # Set the objective: maximize the total value
        m.setObjective(sum(values[i] * x[i] for i in range(len(values))), GRB.MAXIMIZE)

        # Add constraint: the sum of the weights should be less than or equal to the max_weight
        m.addConstr(
            sum(weights[i] * x[i] for i in range(len(weights))) <= token_budget, "c"
        )

        condition_to_ids = dict()
        for dep_key in dependencies:
            for dep_value in dependencies[dep_key]:
                m.addConstr(x[dep_key] >= x[dep_value])

                # Check if the symmetric condition exists
                left_key = self.idx_to_key[dep_key]
                right_key = self.idx_to_key[dep_value]

                condition = f"{left_key}_{right_key}"
                symmetric = f"{right_key}_{left_key}"

                condition_to_ids[condition] = (dep_key, dep_value)

                if symmetric in condition_to_ids:
                    symmetric_ids = condition_to_ids[symmetric]


                    # y = m.addVar(vtype=GRB.BINARY, name=f"y_{dep_key}_{dep_value}")
                    #
                    # m.addConstr(x[dep_key] + x[dep_value] - x[symmetric_ids[0]] - x[symmetric_ids[1]] + 2 * y >= 1,
                    #             f"not_equal_1_{dep_key}_{dep_value}")
                    #
                    # m.addConstr(
                    #     x[symmetric_ids[0]] + x[symmetric_ids[1]] - x[dep_key] - x[dep_value] + 2 * (1 - y) >= 1,
                    #     f"not_equal_2_{dep_key}_{dep_value}")


            m.addConstr(x[dep_key] <= sum(x[i] for i in dependencies[dep_key]))

        m.optimize()

        selected_conditions = defaultdict(list)

        key_counter = defaultdict(int)

        for dep_key in dependencies:
            left_key=self.idx_to_key[dep_key]
            if x[dep_key].x == 1:
                for dep_value in dependencies[dep_key]:
                    key=self.idx_to_key[dep_value]
                    if x[dep_value].x == 1:
                        selected_conditions[left_key].append(key)

        # for condition_set in conditions.items():
        #     left_key = condition_set[0]

        #     kc = key_counter[left_key]
        #     left_key_idx = self.key_to_idx[left_key][kc]
        #     key_counter[left_key] += 1

        #     if x[left_key_idx].x == 1:
        #         right_keys = sorted(condition_set[1], key=lambda x: x[0])
        #         for pair in right_keys:
        #             key = pair[0]
        #             cost = pair[1]

        #             kc = key_counter[key]
        #             right_key_idx = self.key_to_idx[key][kc]
        #             key_counter[key] += 1

        #             if x[right_key_idx].x == 1:
        #                 selected_conditions[left_key].append(key)
        #                 total_cost+=cost
        return selected_conditions,sum(values[i] * x[i] for i in range(len(values))).getValue()

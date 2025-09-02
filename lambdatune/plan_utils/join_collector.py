from collections import defaultdict


class JoinCollectorVisitor:
    def __init__(self, db_schema: dict):
        self.filter_operands = set()
        self.join_conditions = defaultdict(int)
        self.join_cost_estimations = dict()
        self.relations = defaultdict(int)
        self.aliases = dict()
        self.db_schema = db_schema
        self.filters=dict()
        self.query_costs=dict()

    def get_filter_operands(self, condition):
        operands = set()

        if " OR " in condition:
            for condition in condition.split(" OR "):
                for op in self.get_filter_operands(condition):
                    operands.add(op)
        elif " AND " in condition:
            for condition in condition.split(" AND "):
                for op in self.get_filter_operands(condition):
                    operands.add(op)
        else:
            condition = condition.replace("(", "").replace(")", "")

            if " = " in condition:
                split = condition.split(" = ")
            elif " > " in condition:
                split = condition.split(" > ")
            elif " < " in condition:
                split = condition.split(" < ")
            elif " >= " in condition:
                split = condition.split(" >= ")
            elif " <= " in condition:
                split = condition.split(" <= ")
            elif " <> " in condition:
                split = condition.split(" <> ")
            else:
                return operands

            for op in split:
                operands.add(op)

        return operands

    def visit(self, node,query_cost):
        for child in node.children:
            child.accept(self,query_cost)

        if "Alias" in node.info and "Relation Name" in node.info:
            rel_name = node.info["Relation Name"]
            self.aliases[node.info["Alias"]] = rel_name

        if "Relation Name" in node.info:
            rel_name = node.info["Relation Name"]

            if "Alias" in node.info:
                self.aliases[node.info["Alias"]] = rel_name
                rel_name += " as " + node.info["Alias"]

            self.relations[rel_name] += 1

        if "Filter" in node.info:
                cond = node.info["Filter"]
                operands = self.get_filter_operands(cond)
                for operand in operands:
                    if "Relation Name" in node.info:
                        name = node.info["Relation Name"]
                        self.filter_operands.add(f"{name}.{operand}")
                # if "Relation Name" in node.info:
                #     self.filters[f'{node.info["Relation Name"]}.{cond}']=node.cost_estim

        # Check for join keys
        join_cond = None

        if "Join Filter" in node.info:
            join_cond = node.info["Join Filter"][1:-1]
        elif "Hash Cond" in node.info:
            join_cond = node.info["Hash Cond"][1:-1]
        elif "Recheck Cond" in node.info:
            join_cond = node.info["Recheck Cond"][1:-1]

            if node.info["Node Type"] == "Bitmap Heap Scan":
                join_cond = node.info["Relation Name"] + "." + join_cond
        elif "Index Cond" in node.info:
            if "Relation Name" in node.info:
                join_cond = node.info["Relation Name"] + "." + node.info["Index Cond"][1:-1]
        else:
            pass

        if join_cond:
            if len(join_cond.split(" = ")) == 2:
                if len(join_cond.split(" = ")[0].split(".")) == 2 and len(join_cond.split(" = ")[1].split(".")) == 2:
                    # Skip complex expressions

                    try:
                        left_tbl, left_col = join_cond.split(" = ")[0].split(".")
                        right_tbl, right_col = join_cond.split(" = ")[1].split(".")
                    except Exception:
                        print()

                    """
                        Process only if both tables and columns exists in the schema
                    """
                    left_tbl = self.aliases[left_tbl] if left_tbl in self.aliases else left_tbl
                    right_tbl = self.aliases[right_tbl] if right_tbl in self.aliases else right_tbl

                    cond1 = left_tbl in self.db_schema
                    cond2 = left_col in self.db_schema[left_tbl]
                    cond3 = right_tbl in self.db_schema
                    cond4 = right_col in self.db_schema[right_tbl]

                    cost_estim = node.cost_estim

                    self.join_cost_estimations[join_cond] = cost_estim
                    self.join_conditions[join_cond] += 1
                    self.query_costs[join_cond]=query_cost

    def resolve_aliases(self):
        for join_condition in list(self.join_conditions.keys()):
            and_conditions = join_condition.split("AND")

            if len(and_conditions) > 1:
                pass

            for i in range(0, len(and_conditions)):
                cond = and_conditions[i].split(" = ")

                if len(cond) == 1:
                    continue

                left = self.resolve_alias(cond[0])
                right = self.resolve_alias(cond[1])

                and_conditions[i] = f"{left} = {right}"

            new_join_condition = " AND ".join(and_conditions)

            if new_join_condition != join_condition:
                self.join_conditions[new_join_condition] += 1
                self.join_cost_estimations[new_join_condition] = self.join_cost_estimations[join_condition]
                self.query_costs[new_join_condition]=self.query_costs[join_condition]

                # Remove the old key
                self.join_conditions.pop(join_condition)
                self.join_cost_estimations.pop(join_condition)

    def resolve_alias(self, operand):
        split = operand.split(".")

        if len(split) == 2 and split[0] in self.aliases:
            return f"{self.aliases[split[0]]}.{split[1]}"
        else:
            return operand
class ScanCollectorVisitor:
    def __init__(self):
        self.scans = set()

    def visit(self, plan):
        if "Bitmap Heap Scan" in plan.node_type:
            plan.children[0].accept(self)
            pass
        elif "Index Name" in plan.info:
            relation_name = plan.info["Index Name"]
            node_type = plan.info["Node Type"]

            index_scan_name = f"{node_type}({relation_name})"
            self.scans.add(index_scan_name)
            return
        elif "Alias" in plan.info:
            self.scans.add(plan.info["Alias"])
        elif "Relation Name" in plan.info:
            self.scans.add(plan.info["Relation Name"])
        else:
            for child in plan.children:
                child.accept(self)


class JoinCollectorVisitor:
    def __init__(self):
        self.joins = set()

    def visit(self, plan):
        for child in plan.children:
            child.accept(self)

        if plan.is_join:
            self.joins.add(plan)


class PostgresPlanNode:
    def __init__(self, json_node):
        self.node_type = json_node["Node Type"]
        self.actual_time = json_node["Actual Total Time"] if "Actual Total Time" in json_node else None
        self.cost_estim = json_node["Total Cost"]
        self.actual_rows = json_node["Actual Rows"] if "Actual Rows" in json_node else None
        self.plan_rows = json_node["Plan Rows"] if "Plan Rows" in json_node else None
        self.is_join = "Plans" in json_node and  len(json_node["Plans"]) == 2
        self.info = json_node
        self.children = list()

        self.parent = None

        if "Plans" in json_node:
            for plan in json_node["Plans"]:
                child = PostgresPlanNode(plan)
                child.parent = self
                self.children.append(child)

    def get_scans(self):
        scan_visitor = ScanCollectorVisitor()
        self.accept(scan_visitor)
        return scan_visitor.scans

    def get_joins(self):
        join_visitor = JoinCollectorVisitor()
        self.accept(join_visitor)
        return join_visitor.joins

    def get_set_representation(self):
        """
        Returns the set representation of this scan as a set of scan-sets
        """

        # joins = list(self.get_joins())
        # scan_set = [join.get_scans() for join in joins]

        return set(frozenset(join.get_scans()) for join in self.get_joins())

    def get_nodes_as_list(self):
        nodes = [self]

        for child in self.children:
            for node in child.get_nodes_as_list():
                nodes.append(node)

        return nodes

    def accept(self, visitor):
        visitor.visit(self)

    def __str__(self):
        return self.node_type
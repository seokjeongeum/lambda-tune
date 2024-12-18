import sys

from . import PostgresPlanNode

class PostgresPlan:
    def __init__(self, plan_json, query_id=None):
        self.root = PostgresPlanNode(plan_json["plan"]["Plan"])

        self.actual_time = None
        if "Actual Total Time" in plan_json:
            self.actual_time = plan_json["Actual Total Time"]
        else:
            self.actual_time = plan_json["execTime"]

    def get_actual_time(self):
        return self.actual_time

    def get_indexes(self):
        return PostgresPlan.extract_indices_from_plan(self.info["plan"])

    def get_nodes_flat(self, plan):
        nodes = list()

        cost = plan["Actual Total Time"]
        node = {"type": plan["Node Type"]}

        if "Plans" in plan:
            children = plan["Plans"]
            node["children"] = children

            for child in children:
                cost -= child["Actual Total Time"]
                nodes.extend(self.get_nodes_flat(child))

        node["cost"] = cost
        nodes.append(node)

        return nodes

    def get_avg_cost_deviation(self):
        nodes = self.root.get_nodes_as_list()

        avg_dev = 0.0
        for node in nodes:
            diff = abs(node.plan_rows - node.actual_rows)
            perc = 0
            if node.actual_rows != 0:
                perc = diff / node.actual_rows
            avg_dev += perc

        avg_dev = avg_dev / len(nodes)

        dev = abs(sum([n.plan_rows for n in nodes]) - sum([n.actual_rows for n in nodes])) / len(nodes)
        print("Avg dev: ", avg_dev)
        return avg_dev

    @staticmethod
    def extract_indices_from_plan(plan_json):
        node_type = plan_json["Node Type"]

        indices = list()

        if "Index Scan" in node_type:
            index_name = plan_json["Index Name"]

            indices.append(index_name)

        if "Plans" in plan_json:
            children = plan_json["Plans"]

            for child in children:
                for idx in PostgresPlan.extract_indices_from_plan(child):
                    indices.append(idx)

        return indices

    @staticmethod
    def extract_scans_from_plan(plan_json):
        node_type = plan_json["Node Type"]
        scans = list()

        if "Index Scan" == node_type or "Seq Scan" in node_type:
            if "Relation Name" not in plan_json:
                pass
            table_name = plan_json["Relation Name"]

            scans.append(table_name)
        if "Plans" in plan_json:
            children = plan_json["Plans"]

            for child in children:
                for idx in PostgresPlan.extract_scans_from_plan(child):
                    scans.append(idx)

        return scans

    @staticmethod
    def extract_table_sets(plan_json):
        node_type = plan_json["Node Type"]
        table_sets = set()

        if "Index Scan" == node_type or "Seq Scan" in node_type:
            table_name = plan_json["Relation Name"]

            table_sets.add(frozenset({table_name}))

        if "Plans" in plan_json:
            children = plan_json["Plans"]

            new_table_set = set()

            for child in children:
                for table_set in PostgresPlan.extract_table_sets(child):
                    table_sets.add(table_set)

                    for tbl in table_set:
                        new_table_set.add(tbl)
            new_table_set = frozenset(new_table_set)
            table_sets.add(new_table_set)

        return table_sets




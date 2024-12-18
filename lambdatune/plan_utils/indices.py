def extract_indices_from_plan(plan_json):
    node_type = plan_json["Node Type"]

    indices = list()

    if "Index Scan" in node_type:
        index_name = plan_json["Index Name"]

        indices.append(index_name)

    if "Plans" in plan_json:
        children = plan_json["Plans"]

        for child in children:
            for idx in extract_indices_from_plan(child):
                indices.append(idx)

    return indices

def extract_scans_from_plan(plan_json):
    node_type = plan_json["Node Type"]
    scans = list()

    if "Index Scan" == node_type or "Seq Scan" in node_type:
        if "Relation Name" not in plan_json:
            print()
        table_name = plan_json["Relation Name"]

        scans.append(table_name)
    if "Plans" in plan_json:
        children = plan_json["Plans"]

        for child in children:
            for idx in extract_scans_from_plan(child):
                scans.append(idx)

    return scans


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
            for table_set in extract_table_sets(child):
                table_sets.add(table_set)

                for tbl in table_set:
                    new_table_set.add(tbl)
        new_table_set = frozenset(new_table_set)
        table_sets.add(new_table_set)

    return table_sets
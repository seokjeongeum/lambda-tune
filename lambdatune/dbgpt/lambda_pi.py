
def prompt(plan_1: str, plan_2: str, system: str):
    text = ("These are two plans for the same query."
            "Plan 1: \n"
            f"{plan_1}\n"
            "Plan 2: \n"
            f"{plan_2}\n"
            "Plan 1 is faster than Plan 2."
            f"The database system is {system}."
            f"Suggest configuration changes to speed up Plan 2, or, revert it to Plan 1 if possible."
            f"Your response should strictly consist of a list of SQL commands compatible with {system}, and no additional text."
            "Your response should strictly follow the following JSON schema:\n"
            "{plan_diff: explain the plan differences, "
            "reasoning: explain your reasoning about the recommened parameters,"
            "commands: [list of SQL commands]}"
            )

    print(text)


plan_1 = """
 Limit  (cost=827441.68..827441.70 rows=1 width=32)
   ->  Aggregate  (cost=827441.68..827441.70 rows=1 width=32)
         ->  Nested Loop  (cost=0.43..827436.66 rows=2010 width=8)
               ->  Seq Scan on part  (cost=0.00..7074.00 rows=201 width=4)
                     Filter: ((p_brand = 'Brand#22'::bpchar) AND (p_container = 'SM BAG'::bpchar))
               ->  Index Scan using idx_lineitem_partkey on lineitem  (cost=0.43..4081.31 rows=10 width=17)
                     Index Cond: (l_partkey = part.p_partkey)
                     Filter: (l_quantity < (SubPlan 1))
                     SubPlan 1
                       ->  Aggregate  (cost=127.59..127.60 rows=1 width=32)
                             ->  Bitmap Heap Scan on lineitem lineitem_1  (cost=4.67..127.51 rows=31 width=5)
                                   Recheck Cond: (l_partkey = part.p_partkey)
                                   ->  Bitmap Index Scan on idx_lineitem_partkey  (cost=0.00..4.67 rows=31 width=0)
                                         Index Cond: (l_partkey = part.p_partkey)
"""

plan_2 = """
 Limit  (cost=194957.14..194957.15 rows=1 width=32)
   ->  Aggregate  (cost=194957.14..194957.15 rows=1 width=32)
         ->  Hash Join  (cost=6346.61..194952.11 rows=2010 width=8)
               Hash Cond: (lineitem.l_partkey = part.p_partkey)
               Join Filter: (lineitem.l_quantity < (SubPlan 1))
               ->  Seq Scan on lineitem  (cost=0.00..171576.15 rows=6001215 width=17)
               ->  Hash  (cost=6344.10..6344.10 rows=201 width=4)
                     ->  Gather  (cost=1000.00..6344.10 rows=201 width=4)
                           Workers Planned: 2
                           ->  Parallel Seq Scan on part  (cost=0.00..5324.00 rows=84 width=4)
                                 Filter: ((p_brand = 'Brand#22'::bpchar) AND (p_container = 'SM BAG'::bpchar))
               SubPlan 1
                 ->  Aggregate  (cost=127.59..127.60 rows=1 width=32)
                       ->  Bitmap Heap Scan on lineitem lineitem_1  (cost=4.67..127.51 rows=31 width=5)
                             Recheck Cond: (l_partkey = part.p_partkey)
                             ->  Bitmap Index Scan on idx_lineitem_partkey  (cost=0.00..4.67 rows=31 width=0)
                                   Index Cond: (l_partkey = part.p_partkey)

"""

prompt(plan_1, plan_2, "postgres")
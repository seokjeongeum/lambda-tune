import json
import unittest

from lambdatune.prompt_generator.ilp_solver import ILPSolver
from lambdatune.prompt_generator.compress_query_plans import hide_table_column_names
from lambdatune.llm_response import LLMResponse


class PromptGeneratorTests(unittest.TestCase):
    def test_extract_dependencies(self):
        conditions = {
            "a": [("b", 400), ("c", 600)],
            "b": [("a", 1500), ("c", 150), ("d", 80)]
        }

        solver = ILPSolver()
        dependencies, costs, values = solver.extract_dependencies(conditions)

        key_to_id_expected = {
            "a": [0, 4],
            "b": [1, 3],
            "c": [2, 5],
            "d": [6]
        }

        dependencies_expected = {
            0: {1, 2},
            3: {4, 5, 6}
        }

        self.assertEqual(solver.key_to_idx, key_to_id_expected)
        self.assertEqual(dependencies, dependencies_expected)
        self.assertEqual(values, [0, 400, 600, 0, 1500, 150, 80])
        self.assertEqual(costs, [1, 1, 1, 1, 1, 1, 1])

    def test_optimize_with_dependencies_1(self):
        conditions = {
            "a": [("b", 400), ("c", 600)],
            "b": [("a", 1500), ("c", 150), ("d", 80)]
        }

        solver = ILPSolver()

        r = solver.optimize_with_dependencies(conditions, 300)

        expected_solution = {
            "a": ["c"],
            "b": ["a", "c", "d"]
        }

        self.assertEqual(r, expected_solution)

    def test_optimize_with_dependencies_2(self):
        conditions = {
            "a": [("b", 2000), ("c", 600)],
            "b": [("a", 1500), ("c", 150), ("d", 80)]
        }

        solver = ILPSolver()

        r = solver.optimize_with_dependencies(conditions, 300)

        expected_solution = {
            "a": ["b", "c"],
            "b": ["c", "d"]
        }

        self.assertEqual(r, expected_solution)

    def test_optimize_with_dependencies_3(self):
        conditions = {
            "a": [("b", 2000), ("c", 600)],
            "b": [("a", 1500), ("c", 1050), ("d", 80)],
            "c": [("a", 5000), ("b", 500), ("z", 800)]
        }

        solver = ILPSolver()

        r = solver.optimize_with_dependencies(conditions, 300)

        expected_solution = {
            "a": ["b"],
            "b": ["c", "d"],
            "c": ["a", "z"]
        }

        self.assertEqual(r, expected_solution)

    def test_hide_table_columns(self):
        job = {
            "movie_info_idx.info_type_id": [
                "info_type.id"
            ],
            "movie_companies.movie_id": [
                "cast_info.movie_id",
                "complete_cast.movie_id",
                "movie_info.movie_id",
                "movie_info_idx.movie_id",
                "movie_keyword.movie_id",
                "movie_link.linked_movie_id",
                "title.id"
            ],
            "movie_companies.company_type_id": [
                "company_type.id"
            ],
            "title.id": [
                "aka_title.movie_id",
                "cast_info.movie_id",
                "complete_cast.movie_id",
                "movie_companies.movie_id",
                "movie_info.movie_id",
                "movie_info_idx.movie_id",
                "movie_keyword.movie_id",
                "movie_link.linked_movie_id"
            ],
            "movie_keyword.keyword_id": [
                "keyword.id"
            ],
            "company_name.id": [
                "movie_companies.company_id"
            ],
            "movie_info.movie_id": [
                "cast_info.movie_id",
                "complete_cast.movie_id",
                "movie_companies.movie_id",
                "movie_info_idx.movie_id",
                "movie_keyword.movie_id",
                "title.id"
            ],
            "movie_info_idx.movie_id": [
                "cast_info.movie_id",
                "complete_cast.movie_id",
                "movie_companies.movie_id",
                "movie_info.movie_id",
                "movie_keyword.movie_id",
                "title.id"
            ],
            "movie_info.info_type_id": [
                "info_type.id"
            ],
            "info_type.id": [
                "movie_info.info_type_id",
                "movie_info_idx.info_type_id",
                "person_info.info_type_id"
            ],
            "cast_info.movie_id": [
                "movie_companies.movie_id",
                "movie_info.movie_id",
                "movie_keyword.movie_id",
                "title.id"
            ],
            "name.id": [
                "aka_name.person_id",
                "cast_info.person_id",
                "person_info.person_id"
            ],
            "person_info.info_type_id": [
                "info_type.id"
            ],
            "aka_name.person_id": [
                "cast_info.person_id",
                "name.id",
                "person_info.person_id"
            ],
            "cast_info.person_id": [
                "aka_name.person_id",
                "name.id"
            ],
            "movie_link.linked_movie_id": [
                "cast_info.movie_id",
                "title.id"
            ],
            "link_type.id": [
                "movie_link.link_type_id"
            ],
            "movie_link.link_type_id": [
                "link_type.id"
            ],
            "movie_companies.company_id": [
                "company_name.id"
            ],
            "cast_info.role_id": [
                "role_type.id"
            ],
            "role_type.id": [
                "cast_info.role_id"
            ],
            "char_name.id": [
                "cast_info.person_role_id"
            ],
            "company_type.id": [
                "movie_companies.company_type_id"
            ],
            "movie_link.movie_id": [
                "movie_companies.movie_id",
                "movie_info.movie_id",
                "movie_keyword.movie_id",
                "title.id"
            ],
            "keyword.id": [
                "movie_keyword.keyword_id"
            ],
            "title.kind_id": [
                "kind_type.id"
            ],
            "kind_type.id": [
                "title.kind_id"
            ],
            "aka_title.movie_id": [
                "movie_companies.movie_id",
                "title.id"
            ],
            "movie_keyword.movie_id": [
                "movie_companies.movie_id",
                "title.id"
            ],
            "complete_cast.movie_id": [
                "movie_keyword.movie_id",
                "title.id"
            ],
            "complete_cast.subject_id": [
                "comp_cast_type.id"
            ],
            "complete_cast.status_id": [
                "comp_cast_type.id"
            ],
            "comp_cast_type.id": [
                "complete_cast.status_id",
                "complete_cast.subject_id"
            ],
            "person_info.person_id": [
                "cast_info.person_id",
                "name.id"
            ],
            "(ml.linked_movie_id": [
                "movie_info_idx.movie_id)  AND  (it2.id"
            ],
            "(t2.id": [
                "movie_info_idx.movie_id)  AND  (it2.id"
            ]
        }

        hidden_table_colums, tables, columns = hide_table_column_names(job)

        self.assertEqual(len(hidden_table_colums.keys()), len(job.keys()))

        for l_fake_table_col in hidden_table_colums:
            fake_table = l_fake_table_col.split(".")[0]
            fake_col = l_fake_table_col.split(".")[1]

            l_real_table_col = f"{tables[fake_table]}.{columns[fake_col]}"

            self.assertTrue(l_real_table_col in job)

            fake_right = hidden_table_colums[l_fake_table_col]
            real_right = job[l_real_table_col]

            self.assertEqual(len(fake_right), len(real_right))

            for r_fake_table_col in fake_right:
                fake_table = r_fake_table_col.split(".")[0]
                fake_col = r_fake_table_col.split(".")[1]

                r_real_table_col = f"{tables[fake_table]}.{columns[fake_col]}"

                # TODO: Fix this
                if "(" in r_real_table_col:
                    continue

                self.assertTrue(r_real_table_col in job[l_real_table_col])

    def test_hide_table_columns_2(self):
        response = LLMResponse("./resources/test_config_hidden_cols.json")

        config = response.get_config()

        print(config)
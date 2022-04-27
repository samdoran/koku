#
# Copyright 2022 Red Hat Inc.
# SPDX-License-Identifier: Apache-2.0
#
import os
import re
from unittest.mock import patch

from django.db import connection
from psycopg2 import OperationalError
from psycopg2.errors import ProgrammingError
from psycopg2.errors import UndefinedTable

from api.iam.test.iam_test_case import IamTestCase
from koku.configurator import CONFIGURATOR
from masu.api.db_performance.db_performance import DBPerformanceStats
from masu.api.db_performance.db_performance import SERVER_VERSION


class TestDBPerformanceClass(IamTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        conn = connection.connection
        with conn.cursor() as cur:
            cur.execute("create extension if not exists pg_stat_statements;;")

    def test_separate_connection(self):
        """Test that the DBPerformanceStats class uses a separate connetion"""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            self.assertNotEqual(dbp.conn, connection.connection)
            _conn = dbp.conn
        self.assertTrue(_conn.closed)

    @patch("koku.configurator.CONFIGURATOR.get_database_ca", return_value=True)
    def test_ssl(self, ca):
        """Test that a certificate file can be used to make a connection."""
        expected = OperationalError
        dbp = None
        exc = None
        try:
            dbp = DBPerformanceStats("KOKU", CONFIGURATOR)
        except Exception as e:
            exc = e
        if exc is not None:
            self.assertEqual(expected, type(exc))
        else:
            self.assertFalse(dbp.conn.closed)

    def test_bad_sql(self):
        """Test that bad sql will throw an exception."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            with self.assertRaises(UndefinedTable):
                dbp._execute("""select * from no_table_here;""")

    def test_del_closes_connection(self):
        """Test that instance delete closes the connection"""
        dbp = DBPerformanceStats("KOKU", CONFIGURATOR)
        _conn = dbp.conn
        self.assertFalse(_conn.closed)
        del dbp
        self.assertTrue(_conn.closed)

    def test_get_db_version(self):
        """Test that the db engine version can be retrieved."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            ver = dbp.get_pg_engine_version()
            self.assertEqual(ver, SERVER_VERSION)
            self.assertTrue(all(isinstance(v, int) for v in ver))

    def test_get_dbsettings(self):
        """Test that the current settings are retrieved from the databsae."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            settings = dbp.get_pg_settings()
            self.assertTrue(len(settings) > 0)
            self.assertIn("application_name", (s["name"] for s in settings))

            expected_nsmes = {"application_name", "search_path"}
            settings = dbp.get_pg_settings(setting_names=list(expected_nsmes))
            self.assertEqual({s["name"] for s in settings}, expected_nsmes)

    def test_handle_limit(self):
        """Test handle limit clause."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            params = {}
            res = dbp._handle_limit(None, params)
            self.assertEqual(res, "")
            self.assertEqual(params, {})

            res = dbp._handle_limit(-1, params)
            self.assertEqual(res, "")
            self.assertEqual(params, {})

            res = dbp._handle_limit(10, params)
            self.assertEqual(res.strip(), "limit %(limit)s")
            self.assertEqual(params, {"limit": 10})

    def test_handle_offset(self):
        """Test handle offset clause."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            params = {}
            res = dbp._handle_offset(None, params)
            self.assertEqual(res, "")
            self.assertEqual(params, {})

            res = dbp._handle_offset(-1, params)
            self.assertEqual(res, "")
            self.assertEqual(params, {})

            res = dbp._handle_offset(10, params)
            self.assertEqual(res.strip(), "offset %(offset)s")
            self.assertEqual(params, {"offset": 10})

    def test_handle_lockinfo(self):
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            lockinfo = dbp.get_lock_info()
            if lockinfo:
                self.assertTrue(len(lockinfo) < 500)

            lockinfo = dbp.get_lock_info(limit=1)
            if lockinfo:
                self.assertTrue(len(lockinfo) < 1)

    def test_get_conn_activity(self):
        """Test that the correct connection activty is returned."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            dbpid = dbp.conn.get_backend_pid()
            activity = dbp.get_activity()
            self.assertTrue(all(a["backend_pid"] != dbpid for a in activity))

            activity = dbp.get_activity(include_self=True)
            self.assertTrue(any(a["backend_pid"] == dbpid for a in activity))

            activity = dbp.get_activity(include_self=True, pid=[dbpid])
            self.assertTrue(all(a["backend_pid"] == dbpid for a in activity))

            activity = dbp.get_activity(state=["COMPLETELY INVALID STATE HERE!"])
            self.assertEqual(activity, [])

    def test_get_stmt_stats(self):
        """Test that statement statistics are returned."""
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            has_pss, pss_ver = dbp._validate_pg_stat_statements()
            if has_pss:
                self.assertIsNotNone(pss_ver)
                stats = dbp.get_statement_stats()
                self.assertTrue(0 < len(stats) <= 500)
                self.assertIn("calls", stats[0])
            else:
                self.assertIsNone(pss_ver)
                stats = dbp.get_statement_stats()
                self.assertEqual(len(stats), 1)
                self.assertIn("Result", stats[0])

    def test_case_ranking(self):
        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            res = dbp._case_db_ordering_clause("eek")
            self.assertEqual(res, ("", {}))

        with DBPerformanceStats("KOKU", CONFIGURATOR, database_ranking=["zero", "one"]) as dbp:
            case, params = dbp._case_db_ordering_clause("eek")
            case = re.sub(" +", " ", case.replace(os.linesep, " ").lower())
            expected = (
                "case eek when %(db_val_0)s then %(db_rank_0)s "
                + "when %(db_val_1)s then %(db_rank_1)s else %(def_case_val)s end::text || eek"
            )
            self.assertEqual(case, expected)

    def test_explain(self):
        bad_statements = [
            "analyze select 1",
            "create table eek (id int)",
            "drop table eek",
            "alter table eek",
            "commit",
            "rollback",
            "insert into eek",
            "update eek",
            "delete from eek",
        ]
        for bad_sql in bad_statements:
            with self.assertRaises(ProgrammingError, msg=f"Failing statement is {bad_sql}"):
                with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
                    res = dbp.explain_sql("analyze select 1")

        expected = [{"query_plan": "Result  (cost=0.00..0.01 rows=1 width=4)\n  Output: 1", "query_text": "select 1"}]

        with DBPerformanceStats("KOKU", CONFIGURATOR) as dbp:
            res = dbp.explain_sql("select 1")
            self.assertEqual(res, expected)
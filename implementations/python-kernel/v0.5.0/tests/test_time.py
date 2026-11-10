import itertools
import random
import unittest
from datetime import date

from usg.core.records import Anchor
from usg.grammar.node import ALLEN, speech_time, temporal, time_lit, time_rel, unresolved_time
from usg.grammar.timeval import (CONVERSE, DateInterval, Resolved, Unresolved, allen_relation, check_consistency,
                                 check_temporal, converse, interval_of, parse_interval, resolve_node, resolve_relative)

FRI = Anchor(document_date="2026-10-16")  # a Friday


class AllenTests(unittest.TestCase):
    def test_thirteen_relations_and_converses(self):
        self.assertEqual(len(ALLEN), 13)
        for r in ALLEN:
            self.assertEqual(converse(converse(r)), r)
        self.assertEqual(converse("BEFORE"), "AFTER")
        self.assertEqual(converse("EQUALS"), "EQUALS")

    def test_named_examples(self):
        cases = {
            ((0, 2), (3, 5)): "BEFORE", ((0, 3), (3, 5)): "MEETS", ((0, 3), (2, 5)): "OVERLAPS",
            ((0, 2), (0, 5)): "STARTS", ((1, 3), (0, 5)): "DURING", ((3, 5), (0, 5)): "FINISHES",
            ((0, 5), (0, 5)): "EQUALS", ((3, 5), (0, 2)): "AFTER", ((3, 5), (0, 3)): "MET_BY",
            ((2, 5), (0, 3)): "OVERLAPPED_BY", ((0, 5), (0, 2)): "STARTED_BY", ((0, 5), (1, 3)): "CONTAINS",
            ((0, 5), (3, 5)): "FINISHED_BY",
        }
        self.assertEqual(set(cases.values()), set(ALLEN))
        for (a, b), want in cases.items():
            self.assertEqual(allen_relation(*a, *b), want, (a, b))

    def test_exactly_one_relation_and_converse_symmetry_over_all_small_intervals(self):
        ivs = [(s, e) for s in range(6) for e in range(s + 1, 7)]
        seen = set()
        for a, b in itertools.product(ivs, ivs):
            r = allen_relation(*a, *b)  # raises unless exactly one relation matches
            seen.add(r)
            self.assertEqual(allen_relation(*b, *a), CONVERSE[r])
        self.assertEqual(seen, set(ALLEN))
        with self.assertRaises(ValueError):
            allen_relation(3, 3, 0, 1)


class ConsistencyTests(unittest.TestCase):
    def test_simple_cases(self):
        ok = lambda *c: check_consistency(list(c))[0]
        self.assertTrue(ok(("BEFORE", "a", "b"), ("BEFORE", "b", "c")))
        self.assertFalse(ok(("BEFORE", "a", "b"), ("BEFORE", "b", "c"), ("BEFORE", "c", "a")))
        self.assertFalse(ok(("BEFORE", "a", "b"), ("AFTER", "a", "b")))
        self.assertTrue(ok(("BEFORE", "a", "b"), ("AFTER", "b", "a")))  # same fact stated twice
        self.assertTrue(ok(("MEETS", "a", "b"), ("MEETS", "b", "c")))
        self.assertFalse(ok(("EQUALS", "a", "b"), ("BEFORE", "a", "b")))
        self.assertTrue(ok(("DURING", "a", "b"), ("DURING", "b", "c")))
        self.assertFalse(ok(("DURING", "a", "b"), ("BEFORE", "a", "b")))
        self.assertFalse(ok(("BEFORE", "a", "a")))  # an interval cannot precede itself
        self.assertTrue(ok(("EQUALS", "a", "a")))
        self.assertFalse(check_consistency([("NOPE", "a", "b")])[0])
        self.assertTrue(check_consistency([])[0])

    def test_sound_and_complete_against_brute_force(self):
        """Compare with an exhaustive search over placements of three intervals (random constraint sets)."""
        pts = 6
        ivs = [(s, e) for s in range(pts) for e in range(s + 1, pts + 1)]
        rel = {(i, j): allen_relation(*ivs[i], *ivs[j]) for i in range(len(ivs)) for j in range(len(ivs))}
        rng = random.Random(7)
        relations = sorted(ALLEN)
        n_ok = n_bad = 0
        for _ in range(250):
            r_ab, r_bc, r_ac = (rng.choice(relations) for _ in range(3))
            want = any(rel[(a, b)] == r_ab and rel[(b, c)] == r_bc and rel[(a, c)] == r_ac
                       for a in range(len(ivs)) for b in range(len(ivs)) for c in range(len(ivs)))
            got, _ = check_consistency([(r_ab, "a", "b"), (r_bc, "b", "c"), (r_ac, "a", "c")])
            self.assertEqual(got, want, (r_ab, r_bc, r_ac))
            n_ok += want
            n_bad += not want
        self.assertGreater(n_ok, 20)
        self.assertGreater(n_bad, 20)  # the sample exercises both outcomes


class ResolutionTests(unittest.TestCase):
    def r(self, expr, anchor=FRI, **kw):
        return resolve_relative(expr, anchor, **kw)

    def test_the_anchor_is_a_friday(self):
        self.assertEqual(date(2026, 10, 16).strftime("%A"), "Friday")

    def test_days(self):
        self.assertEqual(self.r("YESTERDAY"), Resolved("2026-10-15", "2026-10-16", "YESTERDAY"))
        self.assertEqual(self.r("TODAY").start, "2026-10-16")
        self.assertEqual(self.r("TOMORROW").start, "2026-10-17")
        self.assertEqual(self.r("DAY_BEFORE_YESTERDAY").start, "2026-10-14")
        self.assertEqual(self.r("DAYS_AGO:3").start, "2026-10-13")
        self.assertEqual(self.r("IN_DAYS:10"), Resolved("2026-10-26", "2026-10-27", "IN_DAYS"))
        self.assertIsInstance(self.r("DAYS_AGO:x"), Unresolved)

    def test_weeks_months_years(self):
        self.assertEqual((self.r("THIS_WEEK").start, self.r("THIS_WEEK").end), ("2026-10-12", "2026-10-19"))  # Monday start
        self.assertEqual(self.r("LAST_WEEK").start, "2026-10-05")
        self.assertEqual(self.r("NEXT_WEEK").start, "2026-10-19")
        self.assertEqual(self.r("THIS_WEEK", week_start=6).start, "2026-10-11")  # locale: Sunday start
        self.assertEqual((self.r("LAST_MONTH").start, self.r("LAST_MONTH").end), ("2026-09-01", "2026-10-01"))
        self.assertEqual(self.r("THIS_MONTH").end, "2026-11-01")
        dec = Anchor(document_date="2026-12-15")
        self.assertEqual((self.r("NEXT_MONTH", dec).start, self.r("NEXT_MONTH", dec).end), ("2027-01-01", "2027-02-01"))
        jan = Anchor(document_date="2026-01-10")
        self.assertEqual(self.r("LAST_MONTH", jan).start, "2025-12-01")
        self.assertEqual((self.r("LAST_YEAR").start, self.r("LAST_YEAR").end), ("2025-01-01", "2026-01-01"))

    def test_weekdays_are_strictly_before_or_after(self):
        self.assertEqual(self.r("LAST_FRIDAY").start, "2026-10-09")  # not today
        self.assertEqual(self.r("NEXT_FRIDAY").start, "2026-10-23")
        self.assertEqual(self.r("LAST_MONDAY").start, "2026-10-12")
        self.assertEqual(self.r("NEXT_MONDAY").start, "2026-10-19")
        self.assertEqual(self.r("LAST_SATURDAY").start, "2026-10-10")

    def test_nothing_is_invented(self):
        for e in ("RECENTLY", "EARLIER", "SOON", "THIS_FRIDAY", "NO_SUCH_THING", "LONG_AGO"):
            self.assertIsInstance(self.r(e), Unresolved, e)
        self.assertIsInstance(self.r("YESTERDAY", None), Unresolved)  # no anchor: stays unresolved
        self.assertIsInstance(self.r("YESTERDAY", Anchor()), Unresolved)
        self.assertIsInstance(self.r("YESTERDAY", Anchor(document_date="2026-10-16", calendar="hijri")), Unresolved)
        self.assertIsInstance(self.r("YESTERDAY", Anchor(document_date="not-a-date")), Unresolved)

    def test_speech_time_is_a_fallback_anchor(self):
        a = Anchor(speech_time="2026-10-16T09:30:00")
        self.assertEqual(self.r("YESTERDAY", a).start, "2026-10-15")

    def test_node_resolution_keeps_the_original_expression(self):
        n = time_rel("YESTERDAY")
        r = resolve_node(n, FRI)
        self.assertEqual(r.get("expr"), "YESTERDAY")  # stored ALONGSIDE, not instead
        self.assertEqual((r.get("resolved_start"), r.get("resolved_end")), ("2026-10-15", "2026-10-16"))
        self.assertIs(resolve_node(r, FRI), r)  # idempotent
        v = time_rel("RECENTLY")
        self.assertIs(resolve_node(v, FRI), v)
        self.assertIs(resolve_node(n, None), n)
        self.assertIsNotNone(interval_of(r))
        self.assertIsNone(interval_of(n))

    def test_intervals(self):
        self.assertEqual(parse_interval("INSTANT", "2026-10-15"), DateInterval(date(2026, 10, 15), date(2026, 10, 16)))
        self.assertIsNone(parse_interval("INSTANT", "2026-10-15T14:00"))  # date-time instants have no extent
        self.assertEqual(parse_interval("INTERVAL", "2026-10-01/2026-10-31").end, date(2026, 10, 31))
        self.assertIsNone(parse_interval("INTERVAL", "2026-10-31/2026-10-01"))
        self.assertIsNone(parse_interval("DURATION", "PT2H"))
        with self.assertRaises(ValueError):
            DateInterval(date(2026, 1, 2), date(2026, 1, 1))


class TemporalCheckTests(unittest.TestCase):
    A = time_lit("INTERVAL", "2026-10-01/2026-10-05")
    B = time_lit("INTERVAL", "2026-10-10/2026-10-12")

    def test_concrete_relations_must_hold(self):
        self.assertEqual(check_temporal(temporal("BEFORE", self.A, self.B)), [])
        bad = check_temporal(temporal("AFTER", self.A, self.B))
        self.assertEqual([c for c, _ in bad], ["VC-G06"])
        self.assertIn("BEFORE", bad[0][1])

    def test_unsatisfiable_cycles_are_found_through_structure(self):
        from usg.grammar.node import and_, holds, apply, ref
        e = lambda n: __import__("usg.grammar.node", fromlist=["extent"]).extent(
            apply("MOVE", 1, {"MOVER": ref(f"REFERENT:{n}")}))
        t = and_(temporal("BEFORE", e(1), e(2)), temporal("BEFORE", e(2), e(3)), temporal("BEFORE", e(3), e(1)))
        self.assertEqual([c for c, _ in check_temporal(t)], ["VC-G06"])
        ok = and_(temporal("BEFORE", e(1), e(2)), temporal("BEFORE", e(2), e(3)))
        self.assertEqual(check_temporal(ok), [])

    def test_resolved_relative_times_take_part(self):
        y = resolve_node(time_rel("YESTERDAY"), FRI)
        t = resolve_node(time_rel("TOMORROW"), FRI)
        self.assertEqual(check_temporal(temporal("BEFORE", y, t)), [])
        self.assertEqual([c for c, _ in check_temporal(temporal("AFTER", y, t))], ["VC-G06"])
        self.assertEqual(check_temporal(temporal("AFTER", time_rel("YESTERDAY"), speech_time())), [])  # unresolved: no claim


if __name__ == "__main__":
    unittest.main()

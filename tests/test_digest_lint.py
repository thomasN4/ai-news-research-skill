"""Regression checks for digest mistakes that must fail CI."""

import copy
from pathlib import Path
import runpy
import unittest


lint = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/lint-digest.py"))["lint"]
MANIFEST = {
    "coverage_start": "2026-01-01",
    "coverage_end": "2026-01-31",
    "revision": 1,
    "updated_at": "2026-02-01T00:00:00Z",
    "updated_by": "codex",
}
DIGEST = """<!doctype html>
<!-- INSTRUCTIONS FOR CLAUDE
Coverage: 2026-01-01 through 2026-01-31. -->
<html lang="en"><head>
<meta name="coverage-start" content="2026-01-01">
<meta name="coverage-end" content="2026-01-31">
<title>Knowledge Patch (v1)</title></head><body>
<div class="patch-label">PATCH v1 · covers 2026-01-01 → 2026-01-31</div>
<section class="month"><h2>January</h2>
<div class="ev"><div class="head"><span class="date">Jan</span>
<h3>A <em>reported</em> event</h3><span class="chip r">REPORTED</span></div>
<div class="src"><a href="https://example.com/report">Source</a></div></div>
</section><footer>knowledge patch v1</footer></body></html>
"""


class DigestLintTests(unittest.TestCase):
    def test_valid_digest_with_partial_date(self):
        self.assertEqual(lint(DIGEST, MANIFEST), [])

    def test_valid_confirmed_chip(self):
        self.assertEqual(lint(DIGEST.replace('class="chip r">REPORTED', 'class="chip c">CONFIRMED'), MANIFEST), [])

    def test_metadata_mismatches_fail(self):
        for old, new in (
            ('content="2026-01-31"', 'content="2026-02-01"'),
            ('Coverage: 2026-01-01 through 2026-01-31.', 'Coverage: stale.'),
            ('INSTRUCTIONS FOR CLAUDE', 'Removed instructions'),
            ('<title>Knowledge Patch (v1)', '<title>Knowledge Patch (v2)'),
            ('PATCH v1', 'PATCH v2'),
            ('covers 2026-01-01 → 2026-01-31', 'covers 2026-01-01 → 2026-02-01'),
            ('knowledge patch v1</footer>', 'knowledge patch v2</footer>'),
            ('<meta name="coverage-end" content="2026-01-31">', ''),
        ):
            with self.subTest(old=old):
                self.assertTrue(lint(DIGEST.replace(old, new), MANIFEST))

    def test_incomplete_or_mislabeled_cards_fail(self):
        for old, new in (
            ('<span class="date">Jan</span>', ''),
            ('<span class="date">Jan</span>', '<span class="date"></span>'),
            ('<h3>A <em>reported</em> event</h3>', ''),
            ('<span class="chip r">REPORTED</span>', ''),
            ('class="chip r">REPORTED', 'class="chip r">CONFIRMED'),
            ('class="chip r">REPORTED', 'class="chip r c">REPORTED'),
            ('>REPORTED</span>', '>VERIFIED</span>'),
            ('class="src"', 'class="other"'),
            ('https://example.com/report', '/report'),
            ('https://example.com/report', 'javascript:alert(1)'),
            ('>Source</a>', '></a>'),
            ('class="month"', 'class="other"'),
        ):
            with self.subTest(old=old):
                self.assertTrue(lint(DIGEST.replace(old, new), MANIFEST))

    def test_empty_digest_fails(self):
        self.assertTrue(lint('', MANIFEST))

    def test_invalid_manifest_fails(self):
        for key, value in (
            ('coverage_start', '2026-02-01'),
            ('coverage_end', 'invalid'),
            ('revision', True),
            ('revision', 0),
            ('revision', '1'),
            ('updated_by', ''),
            ('updated_at', '2026-02-01T00:00:00'),
        ):
            manifest = copy.deepcopy(MANIFEST)
            manifest[key] = value
            with self.subTest(key=key, value=value):
                self.assertTrue(lint(DIGEST, manifest))
        for key in MANIFEST:
            manifest = copy.deepcopy(MANIFEST)
            del manifest[key]
            with self.subTest(missing=key):
                self.assertTrue(lint(DIGEST, manifest))


class ChronologyTests(unittest.TestCase):
    @staticmethod
    def sequence(labels, roundups=()):
        start = DIGEST.index('<div class="ev">')
        end = DIGEST.index('\n</section>', start)
        template = DIGEST[start:end]
        cards = []
        for index, label in enumerate(labels):
            card = template.replace('>Jan</span>', f'>{label}</span>')
            card = card.replace('A <em>reported</em> event', f'Card {index}: {label}')
            if index in roundups:
                card = card.replace('class="ev"', 'class="ev" data-roundup="true"')
            cards.append(card)
        return DIGEST[:start] + '\n'.join(cards) + DIGEST[end:]

    def test_ranges_and_arrows_sort_on_start_and_preserve_ties(self):
        for labels in (
            ('Jan 8–29', 'Jan 9'),
            ('Jan 8 → 29', 'Jan 9'),
            ('Jan 8 → Feb 2', 'Jan 9'),
            ('Jan 8–29', 'Jan 8–10', 'Jan 8'),
        ):
            with self.subTest(labels=labels):
                self.assertEqual(lint(self.sequence(labels), MANIFEST), [])

    def test_definite_inversions_report_titles_and_lines(self):
        for labels in (
            ('Jan 9', 'Jan 8–29'),
            ('Jan 9', 'Jan 8 → 29'),
            ('Jan 20', 'by Jan 13'),
            ('Jan 20', 'on or before Jan 13'),
            ('after Jan 20', 'Jan 20'),
            ('Jan 10', 'before Jan 10'),
        ):
            with self.subTest(labels=labels):
                errors = lint(self.sequence(labels), MANIFEST)
                self.assertEqual(len(errors), 1)
                self.assertIn('definite inversion', errors[0])
                self.assertIn('Card 0:', errors[0])
                self.assertIn('Card 1:', errors[0])
                self.assertIn('line ', errors[0])

    def test_ambiguous_dates_do_not_produce_false_inversions(self):
        for labels in (
            ('on or before Jan 13', 'Jan 8'),
            ('Jan 8', 'by Jan 13'),
            ('after Jan 10', 'Jan 20'),
            ('by Jan 13', 'by Jan 8'),
            ('Jan 20', '~Jan 8'),
            ('~Jan 20', 'Jan 8'),
            ('on or after Jan 10', 'on or before Jan 10'),
        ):
            with self.subTest(labels=labels):
                self.assertEqual(lint(self.sequence(labels), MANIFEST), [])

    def test_ambiguous_middle_card_cannot_hide_an_inversion(self):
        for middle in ('~Jan 22', 'by Jan 25', 'on or before Jan 25'):
            with self.subTest(middle=middle):
                errors = lint(self.sequence(('Jan 20', middle, 'Jan 19')), MANIFEST)
                self.assertEqual(len(errors), 1)
                self.assertIn('Card 0:', errors[0])
                self.assertIn('Card 2:', errors[0])

    def test_early_mid_late_use_repository_sort_keys(self):
        self.assertEqual(lint(self.sequence(('early Jan', 'Jan 5', 'mid-Jan', 'Jan 15', 'late Jan', 'Jan 25')), MANIFEST), [])
        for labels in (('Jan 6', 'early Jan'), ('Jan 16', 'mid-Jan'), ('Jan 26', 'late Jan')):
            with self.subTest(labels=labels):
                self.assertIn('definite inversion', lint(self.sequence(labels), MANIFEST)[0])

    def test_dated_events_roundups_then_undated(self):
        labels = ('Jan 20', 'Jan 1–31', 'Jan 1–30', 'Jan', 'Jan (ongoing)')
        self.assertEqual(lint(self.sequence(labels, roundups=(1, 2)), MANIFEST), [])
        for labels, roundups in (
            (('Jan 1–31', 'Jan 20'), (0,)),
            (('Jan', 'Jan 20'), ()),
            (('Jan', 'Jan 1–31'), (1,)),
        ):
            with self.subTest(labels=labels):
                self.assertIn('definite inversion', lint(self.sequence(labels, roundups), MANIFEST)[0])

    def test_window_spanning_event_is_not_assumed_to_be_a_roundup(self):
        self.assertEqual(lint(self.sequence(('Jan 1–31', 'Jan 20')), MANIFEST), [])
        self.assertIn('definite inversion', lint(self.sequence(('Jan 20', 'Jan 1–31')), MANIFEST)[0])

    def test_invalid_dates_and_markers_fail_instead_of_skipping(self):
        for label in ('tomorrow', 'Jan 32', 'Feb 30', 'Jan 20–19', 'Jan 10 rubbish'):
            with self.subTest(label=label):
                self.assertTrue(lint(self.sequence((label,)), MANIFEST))
        for label, value in (('Jan', 'true'), ('Jan 10', 'yes')):
            digest = self.sequence((label,)).replace('class="ev"', f'class="ev" data-roundup="{value}"')
            with self.subTest(label=label, value=value):
                self.assertTrue(lint(digest, MANIFEST))

    def test_comparisons_reset_for_each_month_section(self):
        digest = self.sequence(('Jan 20',))
        start = digest.index('<section class="month">')
        end = digest.index('</section>', start) + len('</section>')
        section = digest[start:end].replace('Jan 20', 'Jan 10')
        digest = digest[:end] + section + digest[end:]
        self.assertEqual(lint(digest, MANIFEST), [])

    def test_multi_year_coverage_requires_explicit_section_year(self):
        manifest = dict(MANIFEST, coverage_end='2027-01-31')
        digest = self.sequence(('Jan 10',)).replace('2026-01-31', '2027-01-31')
        self.assertIn('data-year', lint(digest, manifest)[0])
        digest = digest.replace('class="month"', 'class="month" data-year="2027"')
        self.assertEqual(lint(digest, manifest), [])
        self.assertTrue(lint(digest.replace('data-year="2027"', 'data-year="unknown"'), manifest))


if __name__ == '__main__':
    unittest.main()

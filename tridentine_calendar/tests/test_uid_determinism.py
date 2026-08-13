import datetime as dt
import tempfile
import unittest
from pathlib import Path

import icalendar as ical

from ..tridentine_calendar import LiturgicalCalendar
from ..utils import gen_uid
from ..utils import iterate_liturgical_year


class TestUidDeterminism(unittest.TestCase):

    @staticmethod
    def _uid_map(calendar_bytes):
        calendar = ical.Calendar.from_ical(calendar_bytes)
        return {
            (event.decoded('DTSTART'), str(event['SUMMARY'])): str(event['UID'])
            for event in calendar.walk('VEVENT')
        }

    @staticmethod
    def _uid_identity_map(calendar):
        identities = []
        for liturgical_year in calendar.liturgical_years.values():
            for date in iterate_liturgical_year(liturgical_year.year):
                identities.extend(
                    (date, event.uid_identity)
                    for event in liturgical_year.calendar[date]
                )
        output = ical.Calendar.from_ical(calendar.to_ical(False))
        events = list(output.walk('VEVENT'))
        assert len(identities) == len(events)
        return {
            identity: str(event['UID'])
            for identity, event in zip(identities, events)
        }

    def test_same_identity_and_date_generate_same_uid(self):
        date = dt.date(2031, 4, 23)
        self.assertEqual(gen_uid('St. George', date), gen_uid('St. George', date))

    def test_different_occurrence_dates_generate_different_uids(self):
        self.assertNotEqual(
            gen_uid('St. George', dt.date(2031, 4, 23)),
            gen_uid('St. George', dt.date(2032, 4, 23)),
        )

    def test_different_events_on_same_date_generate_different_uids(self):
        date = dt.date(2031, 4, 23)
        self.assertNotEqual(gen_uid('St. George', date), gen_uid('St. Mark', date))

    def test_generated_event_identity_is_locale_independent(self):
        maps = {
            lang: self._uid_identity_map(LiturgicalCalendar(2031, lang=lang))
            for lang in ('en', 'ja', 'fr')
        }
        self.assertEqual(maps['en'], maps['fr'])
        common = set.intersection(*(set(uid_map) for uid_map in maps.values()))
        self.assertTrue(common)
        for identity in common:
            self.assertEqual(len({uid_map[identity] for uid_map in maps.values()}), 1)

    def test_plain_and_html_use_the_same_uids(self):
        calendar = LiturgicalCalendar(2031, lang='ja')
        plain = self._uid_map(calendar.to_ical(False))
        html = self._uid_map(calendar.to_ical(True))
        self.assertEqual(plain, html)

    def test_existing_uid_takes_precedence(self):
        initial = ical.Calendar.from_ical(
            LiturgicalCalendar(2031, lang='ja').to_ical(False)
        )
        target = initial.walk('VEVENT')[0]
        key = (target.decoded('DTSTART'), str(target['SUMMARY']))
        expected_uid = 'existing-event@example.test'
        target['UID'] = expected_uid
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'existing.ics'
            path.write_bytes(initial.to_ical())
            reused = self._uid_map(
                LiturgicalCalendar(
                    2031, reuse_uids_from=path, lang='ja'
                ).to_ical(False)
            )
        self.assertEqual(reused[key], expected_uid)

    def test_uid_alias_takes_precedence(self):
        date = dt.date(2026, 1, 1)
        expected_uid = 'existing-octave-day@example.test'
        old = ical.Calendar()
        event = ical.Event()
        event.add('DTSTART', date)
        event.add('SUMMARY', 'The Circumcision')
        event.add('UID', expected_uid)
        old.add_component(event)

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / 'existing.ics'
            path.write_bytes(old.to_ical())
            output = ical.Calendar.from_ical(
                LiturgicalCalendar(
                    2026, reuse_uids_from=path, lang='en'
                ).to_ical(False)
            )

        matches = [
            candidate for candidate in output.walk('VEVENT')
            if candidate.decoded('DTSTART') == date
            and str(candidate['SUMMARY']) == 'Octave Day of the Nativity of the Lord'
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(str(matches[0]['UID']), expected_uid)


if __name__ == '__main__':
    unittest.main()

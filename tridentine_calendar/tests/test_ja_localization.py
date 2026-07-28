"""Tests for Japanese localization fixes."""

import datetime as dt
import unittest

from icalendar import Calendar as IcsCalendar

from tridentine_calendar import movable_feasts as mf
from tridentine_calendar.tridentine_calendar import LiturgicalCalendar
from tridentine_calendar.i18n import Translator


def _events_by_date(liturgical_calendar):
    ics_calendar = IcsCalendar.from_ical(liturgical_calendar.to_ical())
    events = {}
    for component in ics_calendar.walk('VEVENT'):
        events.setdefault(component.get('DTSTART').dt, []).append(component)
    return events


def _bare_summary(summary):
    for prefix in ['› ', '» ']:
        if summary.startswith(prefix):
            return summary[len(prefix):]
    return summary


class TestJapaneseLocalizationPhase1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ja_calendar = LiturgicalCalendar([2026, 2027], lang='ja')
        cls.ja_events = _events_by_date(cls.ja_calendar)

    def summaries_for(self, date):
        return [str(event.get('SUMMARY')) for event in self.ja_events[date]]

    def bare_summaries_for(self, date):
        return [_bare_summary(summary) for summary in self.summaries_for(date)]

    def test_core_feast_summaries(self):
        self.assertIn(
            '御復活の祝日',
            self.bare_summaries_for(mf.Easter.date(2026))
        )
        self.assertIn(
            '我らの主イエズス・キリストの御昇天',
            self.bare_summaries_for(mf.Ascension.date(2026))
        )
        self.assertNotIn(
            '我らの主イエズス・キリストの御昇天の祝日',
            self.bare_summaries_for(mf.Ascension.date(2026))
        )
        self.assertIn(
            '御昇天後の主日',
            self.bare_summaries_for(mf.Ascension.date(2026) + dt.timedelta(3))
        )
        self.assertIn(
            '聖霊降臨の主日',
            self.bare_summaries_for(mf.Pentecost.date(2026))
        )

    def test_jubilate_and_cantate_summaries(self):
        self.assertIn(
            '御復活後第三の主日（Jubilate Sunday）',
            self.bare_summaries_for(mf.JubilateSunday.date(2026))
        )
        self.assertIn(
            '御復活後第五の主日（Cantate Sunday）',
            self.bare_summaries_for(mf.CantateSunday.date(2026))
        )

    def test_supplica_and_thomas_more_summaries(self):
        self.assertIn(
            '祈り（ポンペイの聖母）',
            self.bare_summaries_for(dt.date(2026, 5, 8))
        )
        self.assertIn(
            '祈り（ポンペイの聖母）',
            self.bare_summaries_for(mf.TheSupplica.date(2026))
        )
        self.assertIn(
            '聖トマス・モア',
            self.bare_summaries_for(dt.date(2026, 7, 9))
        )

    def test_accented_feast_names_are_translated(self):
        self.assertIn(
            'ペニャフォルトの聖ライムンド',
            self.bare_summaries_for(dt.date(2026, 1, 23))
        )
        self.assertIn(
            'アルカンタラの聖ペトロ',
            self.bare_summaries_for(dt.date(2026, 10, 19))
        )

    def test_st_mark_dates_are_distinct(self):
        self.assertIn('聖マルコ', self.bare_summaries_for(dt.date(2026, 4, 25)))
        self.assertNotIn(
            '聖マルコ教皇',
            self.bare_summaries_for(dt.date(2026, 4, 25))
        )
        self.assertIn(
            '聖マルコ教皇',
            self.bare_summaries_for(dt.date(2026, 10, 7))
        )

    def test_outranking_sentence_direction(self):
        descriptions = [
            str(event.get('DESCRIPTION'))
            for event in self.ja_events[dt.date(2026, 10, 4)]
            if str(event.get('SUMMARY')) == '› アッシジの聖フランシスコ'
        ]
        self.assertEqual(len(descriptions), 1)
        self.assertIn(
            '今年は聖霊降臨後第十九主日が'
            'アッシジの聖フランシスコの祝日に優先します。',
            descriptions[0]
        )
        self.assertNotIn(
            'アッシジの聖フランシスコが聖霊降臨後第十九主日に優先',
            descriptions[0]
        )

    def test_st_francis_of_assisi_is_not_duplicated(self):
        francis_count = self.bare_summaries_for(dt.date(2026, 10, 4)).count(
            'アッシジの聖フランシスコ'
        )
        self.assertEqual(francis_count, 1)

    def test_color_overrides_apply_only_to_japanese_calendar(self):
        guadalupe = [
            event for event in self.ja_calendar[dt.date(2026, 12, 12)]
            if event.name == 'Our Lady of Guadalupe'
        ][0]
        christmas_eve = [
            event for event in self.ja_calendar[dt.date(2026, 12, 24)]
            if event.name == 'Christmas Eve'
        ][0]
        self.assertEqual(guadalupe.color, 'White')
        self.assertEqual(christmas_eve.color, 'Violet')

        en_calendar = LiturgicalCalendar([2027], lang='en')
        en_guadalupe = [
            event for event in en_calendar[dt.date(2026, 12, 12)]
            if event.name == 'Our Lady of Guadalupe'
        ][0]
        self.assertNotEqual(en_guadalupe.color, 'White')

    def test_translator_outranking_template(self):
        translator = Translator(lang='ja')
        text = translator.format_outranking(
            'アッシジの聖フランシスコ',
            '聖霊降臨後第十九主日',
            False
        )
        self.assertEqual(
            text,
            '今年は聖霊降臨後第十九主日が'
            'アッシジの聖フランシスコの祝日に優先します。'
        )

    def test_english_and_french_core_summaries_are_unchanged(self):
        en_events = _events_by_date(LiturgicalCalendar(2026, lang='en'))
        fr_events = _events_by_date(LiturgicalCalendar(2026, lang='fr'))

        self.assertIn('Easter', [
            str(event.get('SUMMARY'))
            for event in en_events[mf.Easter.date(2026)]
        ])
        self.assertIn('Ascension', [
            str(event.get('SUMMARY'))
            for event in en_events[mf.Ascension.date(2026)]
        ])
        self.assertIn('Pentecost', [
            str(event.get('SUMMARY'))
            for event in en_events[mf.Pentecost.date(2026)]
        ])

        self.assertIn('Pâques', [
            str(event.get('SUMMARY'))
            for event in fr_events[mf.Easter.date(2026)]
        ])
        self.assertIn("L'Ascension", [
            str(event.get('SUMMARY'))
            for event in fr_events[mf.Ascension.date(2026)]
        ])
        self.assertIn('La Pentecôte', [
            str(event.get('SUMMARY'))
            for event in fr_events[mf.Pentecost.date(2026)]
        ])


class TestJapaneseHideFeasts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.years = [2025, 2026, 2027]
        cls.ja_calendar = LiturgicalCalendar(cls.years, lang='ja')
        cls.ja_ics_data = cls.ja_calendar.to_ical()
        cls.ja_events = _events_by_date(cls.ja_calendar)

    def event_names_for(self, date):
        return [event.name for event in self.ja_calendar[date]]

    def summaries_for(self, date):
        return [str(event.get('SUMMARY')) for event in self.ja_events.get(date, [])]

    def descriptions_for(self, date):
        return [
            str(event.get('DESCRIPTION'))
            for event in self.ja_events.get(date, [])
        ]

    def assert_event_hidden(self, date, name):
        self.assertNotIn(name, self.event_names_for(date))
        for summary in self.summaries_for(date):
            self.assertNotIn(name, summary)

    def test_fixed_date_targets_are_hidden_in_japanese(self):
        hidden = [
            (dt.date(2026, 1, 5), 'Twelfth Night'),
            (dt.date(2026, 1, 18), "St. Peter's Chair"),
            (dt.date(2026, 1, 18), 'Chair of Unity Octave'),
            (dt.date(2026, 2, 1), 'St. Brigid'),
            (dt.date(2026, 4, 2), 'St. Mary of Egypt'),
            (dt.date(2026, 4, 24), "St. Mark's Eve"),
            (dt.date(2026, 4, 30), 'Walpurgisnacht'),
            (dt.date(2026, 5, 15), 'St. Dymphna'),
            (dt.date(2026, 5, 15), 'St. Isidore the Farmer'),
            (dt.date(2026, 6, 9), 'St. Columba'),
            (dt.date(2026, 6, 15), 'St. Germaine Cousin'),
            (dt.date(2026, 7, 12), 'St. Veronica'),
            (dt.date(2026, 8, 8), 'Fourteen Holy Helpers'),
            (dt.date(2026, 9, 4), 'St. Rosalia'),
            (dt.date(2026, 9, 17), 'St. Hildegard of Bingen'),
            (dt.date(2026, 9, 23), 'St. Pio of Pietrelcina'),
            (dt.date(2026, 9, 24), 'Our Lady of Walsingham'),
            (dt.date(2026, 9, 26), 'Canadian Martyrs'),
            (dt.date(2026, 10, 31), 'Halloween'),
            (dt.date(2026, 11, 13), 'St. Cabrini'),
            (dt.date(2025, 12, 16), 'Las Posadas'),
            (dt.date(2025, 12, 17), 'Golden Nights'),
        ]
        for date, name in hidden:
            with self.subTest(date=date, name=name):
                self.assert_event_hidden(date, name)

    def test_movable_targets_are_hidden_in_japanese(self):
        movable_targets = [
            (mf.PloughMonday, 'Plough Monday'),
            (mf.FatThursday, 'Fat Thursday'),
            (mf.ShroveMonday, 'Shrove Monday'),
            (mf.MardiGras, 'Mardi Gras'),
        ]
        for year in self.years:
            for movable, name in movable_targets:
                date = movable.date(year)
                with self.subTest(year=year, date=date, name=name):
                    self.assert_event_hidden(date, name)

    def test_february_22_st_peters_chair_at_antioch_remains(self):
        self.assertIn(
            'Chair of St. Peter at Antioch',
            self.event_names_for(dt.date(2026, 2, 22))
        )

    def test_marked_hidden_events_do_not_appear_in_ics(self):
        data = self.ja_ics_data.decode('utf-8')
        self.assertNotIn("St. Peter's Chair", data)
        self.assertNotIn('Chair of Unity Octave', data)
        self.assertNotIn('Halloween', data)

    def test_hidden_period_information_is_removed_from_japanese_ics(self):
        data = self.ja_ics_data.decode('utf-8')
        for text in ['Shrovetide', 'shrovetide', 'Hallowtide', 'hallowtide']:
            with self.subTest(text=text):
                self.assertNotIn(text, data)

        for date in [dt.date(2026, 2, 12), dt.date(2026, 11, 1)]:
            descriptions = self.descriptions_for(date)
            self.assertTrue(any(description for description in descriptions))
            for description in descriptions:
                self.assertNotIn('Shrovetide', description)
                self.assertNotIn('Hallowtide', description)

    def test_hallowtide_liturgical_events_remain(self):
        self.assertIn('Hallowmas', self.event_names_for(dt.date(2026, 11, 1)))
        self.assertIn(
            "All Souls' Day",
            self.event_names_for(dt.date(2026, 11, 2))
        )

    def test_st_francis_of_assisi_remains_once(self):
        names = self.event_names_for(dt.date(2026, 10, 4))
        self.assertEqual(names.count('St. Francis of Assisi'), 1)

    def test_hidden_events_remain_in_english_and_french(self):
        for lang in ['en', 'fr']:
            calendar = LiturgicalCalendar([2026], lang=lang)
            with self.subTest(lang=lang, name="St. Peter's Chair"):
                self.assertIn(
                    "St. Peter's Chair",
                    [event.name for event in calendar[dt.date(2026, 1, 18)]]
                )
            with self.subTest(lang=lang, name='Chair of Unity Octave'):
                self.assertIn(
                    'Chair of Unity Octave',
                    [event.name for event in calendar[dt.date(2026, 1, 18)]]
                )
            with self.subTest(lang=lang, name='Fat Thursday'):
                self.assertIn(
                    'Fat Thursday',
                    [event.name for event in calendar[mf.FatThursday.date(2026)]]
                )
            with self.subTest(lang=lang, name='Halloween'):
                self.assertIn(
                    'Halloween',
                    [event.name for event in calendar[dt.date(2026, 10, 31)]]
                )

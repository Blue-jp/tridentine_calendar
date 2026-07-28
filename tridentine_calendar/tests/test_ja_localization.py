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

"""Tests for Japanese localization fixes."""

import calendar
import csv
import datetime as dt
import io
from importlib import resources
from pathlib import Path
import tempfile
import unittest

from icalendar import Calendar as IcsCalendar
from icalendar import Event as IcsEvent

from tridentine_calendar import movable_feasts as mf
from tridentine_calendar.tridentine_calendar import (
    LiturgicalCalendar,
    _decode_ja_csv_content,
    _normalize_additional_link_url,
)
from tridentine_calendar.i18n import Translator


def _events_by_date_from_ical(ical_data):
    ics_calendar = IcsCalendar.from_ical(ical_data)
    events = {}
    for component in ics_calendar.walk('VEVENT'):
        events.setdefault(component.get('DTSTART').dt, []).append(component)
    return events


def _events_by_date(liturgical_calendar, html_formatting=False):
    return _events_by_date_from_ical(
        liturgical_calendar.to_ical(html_formatting))


def _bare_summary(summary):
    if summary.startswith(' '):
        summary = summary[1:]
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


class TestJapaneseExpressionBlockers(unittest.TestCase):
    years = [2025, 2026, 2027, 2028]
    rosary_name = 'ロザリオの童貞マリアの祝日'
    old_rosary_name = '童貞聖マリアの聖なるロザリオ'
    typed_feast_names = [
        '我らの主イエズス・キリストの御降誕の大祝日',
        '主イエズス・キリストの御割礼の祝日',
        'イエズスの聖名の祝日',
        '主の御公現の祝日',
        'キリストの聖体の祝日',
        'イエズスの聖心の大祝日',
    ]

    @classmethod
    def setUpClass(cls):
        cls.calendar = LiturgicalCalendar(cls.years, lang='ja')
        cls.plain_ical = cls.calendar.to_ical()
        cls.html_ical = cls.calendar.to_ical(html_formatting=True)
        cls.plain_events = _events_by_date_from_ical(cls.plain_ical)
        cls.html_events = _events_by_date_from_ical(cls.html_ical)

    def _event_with_summary(self, events, date, summary):
        matches = [
            event for event in events[date]
            if _bare_summary(str(event.get('SUMMARY'))) == summary
        ]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_holy_rosary_name_and_properties_for_all_years(self):
        for year in self.years:
            date = dt.date(year, 10, 7)
            internal = [
                event for event in self.calendar[date]
                if event.name == 'The Holy Rosary'
            ]
            with self.subTest(year=year):
                self.assertEqual(len(internal), 1)
                self.assertEqual(internal[0].rank, 2)
                self.assertEqual(internal[0].color, 'White')

                for events in [self.plain_events, self.html_events]:
                    event = self._event_with_summary(
                        events, date, self.rosary_name)
                    summary = str(event.get('SUMMARY'))
                    description = str(event.get('DESCRIPTION'))
                    self.assertNotIn(self.old_rosary_name, summary)
                    self.assertNotIn(self.old_rosary_name, description)
                    self.assertIn(
                        'gen_saint365.php?id=100701', description)
                    self.assertIn(
                        'feastofthemostholyrosary.html', description)

    def test_holy_rosary_does_not_affect_either_st_mark(self):
        for year in self.years:
            october_mark = self._event_with_summary(
                self.plain_events,
                dt.date(year, 10, 7),
                '聖マルコ教皇',
            )
            april_mark = self._event_with_summary(
                self.plain_events,
                dt.date(year, 4, 25),
                '聖マルコ',
            )
            with self.subTest(year=year):
                self.assertEqual(
                    str(october_mark.get('DESCRIPTION')).splitlines()[0],
                    '記念',
                )
                self.assertNotIn(
                    self.rosary_name,
                    str(april_mark.get('SUMMARY')),
                )

    def test_old_holy_rosary_summaries_reuse_uids(self):
        old_calendar = IcsCalendar()
        old_calendar.add('prodid', '-//Rosary UID reuse test//EN')
        old_calendar.add('version', '2.0')
        expected_uids = {}
        for year in self.years:
            date = dt.date(year, 10, 7)
            uid = f'old-holy-rosary-{year}@example.test'
            expected_uids[date] = uid
            event = IcsEvent()
            event.add('summary', ' ' + self.old_rosary_name)
            event.add('dtstart', date)
            event.add('uid', uid)
            old_calendar.add_component(event)

        with tempfile.TemporaryDirectory() as tmp_dir:
            old_path = Path(tmp_dir) / 'old.ics'
            old_path.write_bytes(old_calendar.to_ical())
            updated = LiturgicalCalendar(
                self.years,
                reuse_uids_from=old_path,
                lang='ja',
            )
            outputs = [
                _events_by_date_from_ical(updated.to_ical()),
                _events_by_date_from_ical(
                    updated.to_ical(html_formatting=True)),
            ]

        for events in outputs:
            for date, uid in expected_uids.items():
                event = self._event_with_summary(
                    events, date, self.rosary_name)
                with self.subTest(date=date, html=events is outputs[1]):
                    self.assertEqual(str(event.get('UID')), uid)

    def test_names_with_event_type_do_not_repeat_feast(self):
        for events in [self.plain_events, self.html_events]:
            all_events = [
                event
                for day_events in events.values()
                for event in day_events
            ]
            for name in self.typed_feast_names:
                matches = [
                    event
                    for event in all_events
                    if _bare_summary(str(event.get('SUMMARY'))) == name
                ]
                with self.subTest(
                        html=events is self.html_events, name=name):
                    self.assertEqual(len(matches), len(self.years))
                    for event in matches:
                        description = str(event.get('DESCRIPTION'))
                        self.assertTrue(description.startswith(name + 'は'))
                        self.assertNotIn('祝日の祝日', description)

    def test_japanese_event_type_suffixes_are_general(self):
        translator = Translator(lang='ja')
        outranking = '聖霊降臨後第十九主日'
        for feast in [
            '主の御公現の祝日',
            '御復活後第三の主日',
            '使徒聖パウロの記念',
        ]:
            with self.subTest(feast=feast):
                self.assertEqual(
                    translator.format_outranking(
                        feast, outranking, False),
                    f'今年は{outranking}が{feast}に優先します。',
                )

        self.assertEqual(
            translator.format_outranking(
                'アッシジの聖フランシスコ',
                outranking,
                False,
            ),
            f'今年は{outranking}が'
            'アッシジの聖フランシスコの祝日に優先します。',
        )

    def test_forbidden_repeated_event_types_are_absent(self):
        for output in [self.plain_ical, self.html_ical]:
            text = output.decode('utf-8')
            for repeated_text in [
                '祝日の祝日',
                '主日の祝日',
                '記念の祝日',
            ]:
                with self.subTest(
                        html=output is self.html_ical,
                        repeated_text=repeated_text):
                    self.assertNotIn(repeated_text, text)
            self.assertNotIn(self.old_rosary_name, text)


class TestJapaneseSameDaySummaryOrdering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.years = [2025, 2026, 2027, 2028]
        cls.ja_calendar = LiturgicalCalendar(cls.years, lang='ja')
        cls.plain_ical = cls.ja_calendar.to_ical()
        cls.html_ical = cls.ja_calendar.to_ical(html_formatting=True)
        cls.plain_events = _events_by_date_from_ical(cls.plain_ical)
        cls.html_events = _events_by_date_from_ical(cls.html_ical)

    @staticmethod
    def summaries(events, date):
        return [str(event.get('SUMMARY')) for event in events.get(date, [])]

    def test_representative_same_day_summaries(self):
        expected = {
            dt.date(2026, 9, 10): [
                ' トレンティーノの聖ニコラオ',
                '› 福者カルロ・スピノラ、福者セバスチアノ木村等殉教者',
            ],
            dt.date(2026, 9, 23): [
                ' 9月の四季の斎日',
                '› 聖リノ教皇',
                '› 聖テクラ',
            ],
            dt.date(2026, 10, 4): [
                ' 聖霊降臨後第十九主日',
                '› アッシジの聖フランシスコ',
                '» 祈り（ポンペイの聖母）',
            ],
            dt.date(2026, 10, 7): [
                ' ロザリオの童貞マリアの祝日',
                '› 聖マルコ教皇',
            ],
        }
        for events in [self.plain_events, self.html_events]:
            for date, summaries in expected.items():
                with self.subTest(
                        html=events is self.html_events, date=date):
                    self.assertEqual(self.summaries(events, date), summaries)
                    self.assertFalse(any(
                        'Pio' in summary
                        for summary in self.summaries(events, date)
                    ))

    def test_prefix_and_mark_codepoints_are_exact(self):
        for calendar_events in [self.plain_events, self.html_events]:
            for date, events in calendar_events.items():
                summaries = [str(event.get('SUMMARY')) for event in events]
                has_marker = any(
                    summary.startswith(('› ', '» '))
                    for summary in summaries
                )
                for summary in summaries:
                    with self.subTest(
                            html=calendar_events is self.html_events,
                            date=date, summary=repr(summary)):
                        if summary.startswith('› '):
                            self.assertEqual(ord(summary[0]), 0x203A)
                        elif summary.startswith('» '):
                            self.assertEqual(ord(summary[0]), 0x00BB)
                        elif len(summaries) > 1 and has_marker:
                            self.assertEqual(repr(summary[:1]), repr(' '))
                            self.assertEqual(ord(summary[0]), 0x0020)
                            self.assertFalse(summary.startswith('  '))
                        else:
                            self.assertFalse(summary.startswith(' '))

    def test_single_event_summary_is_not_prefixed(self):
        for events in [self.plain_events, self.html_events]:
            for date, day_events in events.items():
                if len(day_events) != 1:
                    continue
                summary = str(day_events[0].get('SUMMARY'))
                with self.subTest(
                        html=events is self.html_events, date=date):
                    self.assertFalse(summary.startswith(' '))

    def test_multiple_unmarked_events_are_not_prefixed(self):
        for events in [self.plain_events, self.html_events]:
            summaries = self.summaries(
                events, dt.date(2026, 4, 25))
            with self.subTest(html=events is self.html_events):
                self.assertEqual(summaries, ['聖マルコ', '大祈願祭'])
                self.assertFalse(any(
                    summary.startswith(' ') for summary in summaries))

    def test_descriptions_are_not_prefixed(self):
        for date in [
            dt.date(2026, 9, 10),
            dt.date(2026, 9, 23),
            dt.date(2026, 10, 4),
            dt.date(2026, 10, 7),
        ]:
            for events in [self.plain_events, self.html_events]:
                for event in events[date]:
                    with self.subTest(
                            html=events is self.html_events, date=date):
                        self.assertFalse(
                            str(event.get('DESCRIPTION')).startswith(' '))
                        self.assertIsNone(event.get('X-ALT-DESC'))

    def test_english_and_french_summaries_are_not_prefixed(self):
        for lang in ['en', 'fr']:
            calendar_output = LiturgicalCalendar(2026, lang=lang)
            for html_formatting in [False, True]:
                events = _events_by_date(
                    calendar_output,
                    html_formatting=html_formatting,
                )
                with self.subTest(
                        lang=lang, html=html_formatting):
                    self.assertFalse(any(
                        str(event.get('SUMMARY')).startswith(' ')
                        for day_events in events.values()
                        for event in day_events
                    ))

    def test_existing_unprefixed_uids_are_reused(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            old_ical = LiturgicalCalendar(2026, lang='ja').to_ical(
                html_formatting=True)
            parsed_old = IcsCalendar.from_ical(old_ical)
            for event in parsed_old.walk('VEVENT'):
                summary = str(event.get('SUMMARY'))
                if summary.startswith(' '):
                    event['SUMMARY'] = summary[1:]
            old_ical = parsed_old.to_ical()
            filename = Path(tmp_dir) / 'old-ja.ics'
            filename.write_bytes(old_ical)
            old_events = _events_by_date_from_ical(old_ical)

            updated = LiturgicalCalendar(
                2026, reuse_uids_from=filename, lang='ja')
            new_outputs = [
                _events_by_date_from_ical(updated.to_ical()),
                _events_by_date_from_ical(
                    updated.to_ical(html_formatting=True)),
            ]

            old_uids = {
                (date, str(event.get('SUMMARY'))): str(event.get('UID'))
                for date, events in old_events.items()
                for event in events
            }
            for events in new_outputs:
                new_uids = {
                    (date, str(event.get('SUMMARY')).removeprefix(' ')):
                    str(event.get('UID'))
                    for date, day_events in events.items()
                    for event in day_events
                }
                with self.subTest(html=events is new_outputs[1]):
                    self.assertEqual(old_uids, new_uids)

    def test_plain_and_html_summaries_share_uids(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            plain_ical = LiturgicalCalendar(2026, lang='ja').to_ical()
            filename = Path(tmp_dir) / 'plain-ja.ics'
            filename.write_bytes(plain_ical)
            updated = LiturgicalCalendar(
                2026, reuse_uids_from=filename, lang='ja')
            plain_events = _events_by_date_from_ical(updated.to_ical())
            html_events = _events_by_date_from_ical(
                updated.to_ical(html_formatting=True))

        def uid_map(events):
            return {
                (date, str(event.get('SUMMARY'))): str(event.get('UID'))
                for date, day_events in events.items()
                for event in day_events
            }

        self.assertEqual(uid_map(plain_events), uid_map(html_events))


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

    def test_february_22_shared_st_peters_chair_remains(self):
        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 2, 22)
            matches = [
                event
                for event in LiturgicalCalendar([year], lang='ja')[date]
                if event.name == 'Chair of St. Peter'
            ]
            with self.subTest(year=year):
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0].rank, 2)
                self.assertEqual(matches[0].color, 'White')
                self.assertEqual(
                    matches[0].description_append,
                    '聖パウロも同じミサで記念されます。',
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


class TestJapaneseAdditionalLinks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ja_calendar = LiturgicalCalendar([2025, 2026, 2027, 2028], lang='ja')
        cls.ja_events = _events_by_date(cls.ja_calendar)
        cls.ja_html_events = _events_by_date(
            cls.ja_calendar, html_formatting=True)

    def descriptions_for(self, date, events=None):
        events = events or self.ja_events
        return [
            str(event.get('DESCRIPTION') or '')
            for event in events.get(date, [])
        ]

    def summary_description(self, date, summary_part, events=None):
        events = events or self.ja_events
        for event in events.get(date, []):
            if summary_part in str(event.get('SUMMARY')):
                return str(event.get('DESCRIPTION') or '')
        self.fail(f'No event containing {summary_part!r} on {date}.')

    def assert_ordered(self, text, *parts):
        positions = [text.index(part) for part in parts]
        self.assertEqual(positions, sorted(positions))

    def test_japanese_and_existing_english_links_are_grouped(self):
        description = self.summary_description(dt.date(2026, 1, 14), '聖ヒラリオ')

        self.assertIn('日本語の解説', description)
        self.assertIn('英語の解説', description)
        self.assertIn('季節の解説（英語）', description)
        self.assertIn(
            'https://www.pauline.or.jp/calendariosanti/gen_saint50.php?id=011301',
            description
        )
        self.assertIn('https://en.wikipedia.org/wiki/Hilary_of_Poitiers',
                      description)
        self.assertIn('http://www.newadvent.org/cathen/07349b.htm',
                      description)
        self.assert_ordered(
            description,
            '日本語の解説',
            '英語の解説',
            '季節の解説（英語）',
        )

    def test_event_without_japanese_link_keeps_english_links_only(self):
        description = self.summary_description(
            dt.date(2025, 11, 29), '聖サトゥルニノ')

        self.assertNotIn('日本語の解説', description)
        self.assertIn('英語の解説', description)
        self.assertIn('https://en.wikipedia.org/wiki/Saturnin', description)

    def test_japanese_added_event_has_japanese_links(self):
        description = self.summary_description(dt.date(2026, 9, 10), 'スピノラ')

        self.assertIn('日本語の解説', description)
        self.assertNotIn('英語の解説', description)
        self.assertIn(
            'https://www.pauline.or.jp/calendariosanti/gen_saint365.php?id=091001',
            description
        )
        self.assertIn(
            'https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%AB%E3%83%AD'
            '%E3%83%BB%E3%82%B9%E3%83%94%E3%83%8E%E3%83%A9',
            description
        )
        self.assertIn('季節の解説（英語）', description)
        self.assertIn('https://fisheaters.com/customstimeafterpentecost1.html',
                      description)
        self.assert_ordered(
            description,
            '日本語の解説',
            'https://www.pauline.or.jp/calendariosanti/gen_saint365.php?id=091001',
            'https://ja.wikipedia.org/wiki/%E3%82%AB%E3%83%AB%E3%83%AD',
            '季節の解説（英語）',
            'https://fisheaters.com/customstimeafterpentecost1.html',
        )

    def test_english_additional_link_is_grouped_as_english(self):
        description = self.summary_description(
            dt.date(2026, 9, 13), 'アポリナリス')

        self.assertNotIn('日本語の解説', description)
        self.assertIn('英語の解説', description)
        self.assertIn(
            'https://www.catholicnewsagency.com/saint/'
            'blessed-apollinaris-franco-592',
            description
        )
        self.assert_ordered(
            description,
            '英語の解説',
            'https://www.catholicnewsagency.com/saint/',
            '季節の解説（英語）',
        )

    def test_st_aloysius_gonzaga_has_one_japanese_url(self):
        description = self.summary_description(
            dt.date(2026, 6, 21), '聖アロイジオ')
        representative_url = (
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint365.php?id=062101'
        )

        self.assertIn(representative_url, description)
        self.assertEqual(description.count('gen_saint365.php?id=062101'), 1)
        self.assertNotIn('gen_saint50.php?id=062101', description)

    def test_urls_are_not_duplicated_or_added_to_summaries(self):
        description = self.summary_description(
            dt.date(2026, 6, 21), '聖アロイジオ')
        self.assertEqual(
            description.count(
                'https://www.pauline.or.jp/calendariosanti/'
                'gen_saint365.php?id=062101'
            ),
            1
        )

        for events in self.ja_events.values():
            for event in events:
                self.assertNotIn('http://', str(event.get('SUMMARY')))
                self.assertNotIn('https://', str(event.get('SUMMARY')))

    def test_camillus_kotobank_url_starts_on_bullet_line(self):
        description = self.summary_description(
            dt.date(2026, 9, 16), 'コスタンゾ')
        kotobank_url = (
            'https://kotobank.jp/word/%E5%A4%AA%E7%94%B0%E3%81%82'
            '%E3%81%86%E3%81%90%E3%81%99%E3%81%A1%E3%81%AE-1060415'
        )
        kotobank_lines = [
            line for line in description.splitlines()
            if 'kotobank.jp' in line
        ]

        self.assertEqual(kotobank_lines, ['• ' + kotobank_url])
        self.assertNotIn('•\n' + kotobank_url, description)
        self.assertIn('英語の解説', description)
        self.assertIn('https://en.wikipedia.org/wiki/Camillus_Costanzo',
                      description)
        self.assert_ordered(
            description,
            '日本語の解説',
            kotobank_url,
            '英語の解説',
            'https://en.wikipedia.org/wiki/Camillus_Costanzo',
            '季節の解説（英語）',
        )

    def test_additional_link_url_normalization_preserves_encoded_spaces(self):
        url = (
            ' \t\r\nhttps://example.com/a%20b'
            '\r\nc\t \n'
        )

        self.assertEqual(
            _normalize_additional_link_url(url),
            'https://example.com/a%20bc'
        )

    def test_same_name_seven_sorrows_links_only_fixed_september_feast(self):
        september_description = self.summary_description(
            dt.date(2026, 9, 15), '童貞聖マリアの七つの御苦しみ')
        lent_description = self.summary_description(
            dt.date(2026, 3, 27), '童貞聖マリアの七つの御苦しみ')
        url = (
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint365.php?id=091501'
        )

        self.assertIn(url, september_description)
        self.assertNotIn(url, lent_description)

    def test_all_souls_link_follows_actual_movable_dates(self):
        url = (
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint365.php?id=110201'
        )
        for date in [
            dt.date(2025, 11, 3),
            dt.date(2026, 11, 2),
            dt.date(2027, 11, 2),
        ]:
            with self.subTest(date=date):
                descriptions = self.descriptions_for(date)
                self.assertTrue(any(url in desc for desc in descriptions))

    def test_st_francis_link_attaches_to_single_shared_event(self):
        names = [
            event.name
            for event in self.ja_calendar[dt.date(2026, 10, 4)]
        ]
        description = self.summary_description(dt.date(2026, 10, 4), 'フランシスコ')

        self.assertEqual(names.count('St. Francis of Assisi'), 1)
        self.assertIn(
            'https://www.pauline.or.jp/calendariosanti/gen_saint365.php?id=100401',
            description
        )
        self.assertEqual(description.count('gen_saint365.php?id=100401'), 1)
        self.assertNotIn('gen_saint50.php?id=100401', description)

    def test_hidden_events_are_not_restored_by_additional_links(self):
        data = self.ja_calendar.to_ical().decode('utf-8')

        self.assertNotIn('St. Brigid', data)
        self.assertNotIn('https://www.pauline.or.jp/calendariosanti/'
                         'gen_saint365.php?id=020101', data)
        self.assertNotIn('Halloween', data)

    def test_plain_text_and_html_outputs_use_same_sections(self):
        plain_description = self.summary_description(
            dt.date(2026, 1, 14), '聖ヒラリオ')
        html_description = self.summary_description(
            dt.date(2026, 1, 14), '聖ヒラリオ', self.ja_html_events)

        self.assertIn('日本語の解説', plain_description)
        self.assertIn('日本語の解説', html_description)
        self.assertIn(
            '<a href=https://www.pauline.or.jp/calendariosanti/'
            'gen_saint50.php?id=011301>',
            html_description
        )
        self.assertIn('<a href=https://en.wikipedia.org/wiki/Hilary_of_Poitiers>',
                      html_description)

    def test_english_and_french_descriptions_do_not_use_japanese_links(self):
        cases = [
            ('en', 'St. Hilary', 'More information'),
            ('fr', 'St Hilaire', "Plus d'informations"),
        ]
        for lang, summary, heading in cases:
            calendar = LiturgicalCalendar([2026], lang=lang)
            events = _events_by_date(calendar)
            description = self.summary_description(
                dt.date(2026, 1, 14), summary, events)

            self.assertIn(heading, description)
            self.assertNotIn('日本語の解説', description)
            self.assertNotIn(
                'https://www.pauline.or.jp/calendariosanti/'
                'gen_saint50.php?id=011301',
                description
            )


class TestJapaneseDescriptionOverrides(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.years = [2025, 2026, 2027]
        cls.ja_calendar = LiturgicalCalendar(
            cls.years + [2028], lang='ja')
        cls.plain_events = _events_by_date(cls.ja_calendar)
        cls.html_events = _events_by_date(
            cls.ja_calendar, html_formatting=True)
        cls.override_rows = cls._read_ja_csv('description_overrides.csv')
        cls.commemoration_rows = [
            row for row in cls.override_rows
            if row['description_lead'] == '記念'
        ]
        cls.proper_mass_rows = [
            row for row in cls.override_rows
            if row['description_lead'] == '日本の固有ミサ。'
        ]
        cls.append_rows = [
            row for row in cls.override_rows
            if row['description_append']
        ]

    @staticmethod
    def _read_ja_csv(filename):
        content = (
            resources.files('tridentine_calendar.i18n.ja') / filename
        ).read_bytes()
        return list(csv.DictReader(io.StringIO(
            _decode_ja_csv_content(content))))

    @staticmethod
    def _date_for(year, date_key):
        day, month_abbr = date_key.split('-')
        month = list(calendar.month_abbr).index(month_abbr)
        return dt.date(year, month, int(day))

    def _date_for_row(self, year, row):
        if row.get('match_type') == 'movable_name':
            day = 26 if calendar.isleap(year) else 25
            return dt.date(year, 2, day)
        return self._date_for(year, row.get('date') or row['dates_en'])

    def _component_for(self, year, row, events=None):
        events = events or self.plain_events
        date = self._date_for_row(year, row)
        internal = [
            event for event in self.ja_calendar[date]
            if event.name == row['english_name']
        ]
        self.assertEqual(len(internal), 1)
        translated_name = (
            internal[0].summary_override
            or self.ja_calendar.translator.format_summary(
                row['english_name'])
        )
        matches = [
            event
            for event in events.get(date, [])
            if _bare_summary(str(event.get('SUMMARY'))) == translated_name
        ]
        self.assertEqual(
            len(matches),
            1,
            f"{date}: expected one {row['english_name']!r} event",
        )
        return matches[0]

    def _internal_event(self, year, row):
        date = self._date_for_row(year, row)
        matches = [
            event
            for event in self.ja_calendar[date]
            if event.name == row['english_name']
        ]
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_all_56_overrides_apply_in_each_year(self):
        self.assertEqual(len(self.commemoration_rows), 56)
        self.assertEqual(len({
            (row['date'], row['english_name'])
            for row in self.commemoration_rows
        }), 56)

        matched_occurrences = 0
        for year in self.years:
            for row in self.commemoration_rows:
                with self.subTest(
                    year=year,
                    date=row['date'],
                    name=row['english_name'],
                ):
                    component = self._component_for(year, row)
                    summary = str(component.get('SUMMARY'))
                    description = str(component.get('DESCRIPTION'))
                    internal_event = self._internal_event(year, row)

                    self.assertTrue(summary.startswith('› '))
                    self.assertNotIn('記念', summary)
                    self.assertTrue(description.startswith('記念\n'))
                    self.assertNotIn('第四級', description)
                    self.assertEqual(internal_event.rank, 4)
                    if internal_event.color:
                        self.assertIn(
                            self.ja_calendar.translator.format_color(
                                internal_event.color),
                            description,
                        )

                    html_component = self._component_for(
                        year, row, self.html_events)
                    html_description = str(
                        html_component.get('DESCRIPTION'))
                    self.assertTrue(html_description.startswith('記念\n'))
                    self.assertNotIn('第四級', html_description)
                    matched_occurrences += 1

        self.assertEqual(matched_occurrences, 56 * len(self.years))

    def test_override_data_is_unique_and_matches_local_sources(self):
        self.assertEqual(len(self.override_rows), 78)
        self.assertEqual(len(self.commemoration_rows), 56)
        self.assertEqual(len(self.proper_mass_rows), 16)
        self.assertEqual(len(self.append_rows), 3)
        self.assertEqual(
            [
                (
                    row['match_type'],
                    row['date'],
                    row['english_name'],
                    row['uid_alias'],
                )
                for row in self.override_rows
                if row['uid_alias'] and not row['description_append']
            ],
            [
                (
                    'exact_date_and_name',
                    '7-Oct',
                    'The Holy Rosary',
                    '童貞聖マリアの聖なるロザリオ',
                ),
                (
                    'exact_date_and_name',
                    '2-Sep',
                    'St. Stephen I',
                    '聖ステファノ一世教皇',
                ),
                (
                    'exact_date_and_name',
                    '21-Jan',
                    'St. Agnes',
                    '聖アグネス（第二の祝日）',
                ),
            ],
        )

        keys = [
            (row['match_type'], row['date'], row['english_name'])
            for row in self.override_rows
        ]
        self.assertEqual(len(keys), len(set(keys)))

        fixed_rows = self._read_ja_csv('fixed_feasts_local.csv')
        movable_rows = self._read_ja_csv('movable_feasts_local.csv')
        expected_fixed = {
            ('exact_date_and_name', row['dates_en'], row['en'])
            for row in fixed_rows
        }
        expected_movable = {
            ('movable_name', '', row['en'])
            for row in movable_rows
        }
        actual = {
            (row['match_type'], row['date'], row['english_name'])
            for row in self.proper_mass_rows
        }

        self.assertEqual(len(expected_fixed), 15)
        self.assertEqual(len(expected_movable), 1)
        self.assertEqual(actual, expected_fixed | expected_movable)

    def test_all_16_proper_mass_overrides_apply_in_each_year(self):
        matched_occurrences = 0
        for year in self.years:
            for row in self.proper_mass_rows:
                with self.subTest(
                    year=year,
                    date=row['date'],
                    name=row['english_name'],
                ):
                    component = self._component_for(year, row)
                    summary = str(component.get('SUMMARY'))
                    description = str(component.get('DESCRIPTION'))
                    internal_event = self._internal_event(year, row)

                    self.assertEqual(
                        description.splitlines()[0],
                        '日本の固有ミサ。',
                    )
                    self.assertFalse(description.startswith('今年は'))
                    self.assertFalse(
                        description.startswith('今日は記念日です。'))
                    self.assertNotIn('日本の固有ミサ。', summary)
                    self.assertEqual(
                        _bare_summary(summary),
                        self.ja_calendar.translator.format_summary(
                            row['english_name']),
                    )
                    self.assertEqual(internal_event.rank, 4)
                    if internal_event.color:
                        self.assertIn(
                            self.ja_calendar.translator.format_color(
                                internal_event.color),
                            description,
                        )

                    html_component = self._component_for(
                        year, row, self.html_events)
                    html_description = str(
                        html_component.get('DESCRIPTION'))
                    self.assertEqual(
                        html_description.splitlines()[0],
                        '日本の固有ミサ。',
                    )
                    matched_occurrences += 1

        self.assertEqual(matched_occurrences, 16 * len(self.years))

    def test_proper_mass_summary_markers_are_preserved(self):
        cases = [
            (
                {'date': '5-Feb',
                 'english_name': 'Twenty-six Martyrs of Japan'},
                '› 日本二十六聖人殉教者（聖パウロ三木と同志殉教者）',
            ),
            (
                {'date': '7-Sep',
                 'english_name': (
                     'Bls. Thomas Tsuji, Michael Nakajima ＆ Companions')},
                '福者トマ辻と福者ミカエル中島等殉教者',
            ),
            (
                {'date': '10-Sep',
                 'english_name': (
                     'Bls. Charles Spinola, Sebastian Kimura ＆ Companions')},
                '› 福者カルロ・スピノラ、'
                '福者セバスチアノ木村等殉教者',
            ),
        ]
        for row, expected in cases:
            component = self._component_for(2026, row)
            with self.subTest(date=row['date']):
                self.assertEqual(str(component.get('SUMMARY')), expected)

    def test_proper_mass_links_and_season_information_remain(self):
        spinola = self._component_for(2026, {
            'date': '10-Sep',
            'english_name': (
                'Bls. Charles Spinola, Sebastian Kimura ＆ Companions'),
        })
        spinola_description = str(spinola.get('DESCRIPTION'))
        self.assertIn('日本語の解説', spinola_description)
        self.assertIn(
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint365.php?id=091001',
            spinola_description,
        )
        self.assertIn('季節の解説（英語）', spinola_description)
        self.assertIn(
            'https://fisheaters.com/customstimeafterpentecost1.html',
            spinola_description,
        )

        apollinaris = self._component_for(2026, {
            'date': '13-Sep',
            'english_name': 'Bls. Apollinaris & Companions',
        })
        apollinaris_description = str(apollinaris.get('DESCRIPTION'))
        self.assertIn('英語の解説', apollinaris_description)
        self.assertIn(
            'https://www.catholicnewsagency.com/saint/'
            'blessed-apollinaris-franco-592',
            apollinaris_description,
        )
        self.assertIn('季節の解説（英語）', apollinaris_description)

    def test_movable_proper_mass_uses_february_26_in_leap_year(self):
        row = next(
            row for row in self.proper_mass_rows
            if row['match_type'] == 'movable_name'
        )
        leap_calendar = LiturgicalCalendar(2028, lang='ja')
        leap_events = _events_by_date(leap_calendar)
        translated_name = leap_calendar.translator.format_summary(
            row['english_name'])
        target_date = dt.date(2028, 2, 26)
        matches = [
            event
            for event in leap_events[target_date]
            if _bare_summary(str(event.get('SUMMARY'))) == translated_name
        ]

        self.assertEqual(len(matches), 1)
        self.assertEqual(
            str(matches[0].get('DESCRIPTION')).splitlines()[0],
            '日本の固有ミサ。',
        )
        self.assertNotIn(
            row['english_name'],
            [event.name for event in leap_calendar[dt.date(2028, 2, 25)]],
        )
        internal = [
            event for event in leap_calendar[target_date]
            if event.name == row['english_name']
        ]
        self.assertEqual(len(internal), 1)
        self.assertEqual(internal[0].rank, 4)

    def test_existing_links_and_season_information_remain(self):
        martyrs = self._component_for(2026, {
            'date': '12-Jun',
            'english_name': 'SS. Basilides, Cyrinus, Nabor, & Nazarius',
        })
        martyrs_description = str(martyrs.get('DESCRIPTION'))
        self.assertIn('英語の解説', martyrs_description)
        self.assertIn(
            'https://en.wikipedia.org/wiki/'
            'Basilides,_Cyrinus,_Nabor_and_Nazarius',
            martyrs_description,
        )
        self.assertIn('季節の解説（英語）', martyrs_description)

    def test_html_output_uses_the_same_commemoration_lead(self):
        event = self._component_for(
            2026,
            {
                'date': '12-Jun',
                'english_name': (
                    'SS. Basilides, Cyrinus, Nabor, & Nazarius'),
            },
            self.html_events,
        )
        summary = str(event.get('SUMMARY'))
        description = str(event.get('DESCRIPTION'))

        self.assertEqual(
            summary,
            '› 聖バジリデ、聖チリノ、聖ナボレ、聖ナザリオ',
        )
        self.assertTrue(description.startswith('記念\n'))
        self.assertNotIn('第四級', description)
        self.assertIn(
            '<a href=https://en.wikipedia.org/wiki/'
            'Basilides,_Cyrinus,_Nabor_and_Nazarius>',
            description,
        )

    def test_removed_commemorations_are_not_override_targets(self):
        removed = {
            ('25-Jan', 'St. Peter'),
            ('22-Feb', 'St. Paul'),
        }
        actual = {
            (row['date'], row['english_name'])
            for row in self.commemoration_rows
        }
        self.assertTrue(removed.isdisjoint(actual))

    def test_existing_first_through_third_class_terms_are_unchanged(self):
        translator = Translator(lang='ja')
        expected = {
            1: 'この祝日は一級の祝日です。',
            2: 'この祝日は二級の祝日です。',
            3: 'この祝日は三級の祝日です。',
        }
        for rank, text in expected.items():
            with self.subTest(rank=rank):
                self.assertEqual(
                    translator.format_class_feria(
                        'この祝日', rank, is_feast=True),
                    text,
                )

    def test_remaining_explicit_exclusion_is_unchanged(self):
        excluded = [
            (dt.date(2026, 12, 4), 'St. Barbara'),
        ]
        self.assertNotIn(
            ('30-Jun', 'St. Peter'),
            {
                (row['date'], row['english_name'])
                for row in self.override_rows
            },
        )
        for date, name in excluded:
            matches = [
                event for event in self.ja_calendar[date]
                if event.name == name
            ]
            with self.subTest(date=date, name=name):
                self.assertEqual(len(matches), 1)
                self.assertIsNone(matches[0].description_lead)

    def test_christmas_octave_commemorations_keep_names_colors_and_links(self):
        cases = [
            (
                dt.date(2025, 12, 29),
                'St. Thomas Becket',
                '聖トマス・ベケット',
                'Red',
                'https://www.pauline.or.jp/calendariosanti/'
                'gen_saint365.php?id=122901',
                'https://en.wikipedia.org/wiki/Thomas_Becket',
            ),
            (
                dt.date(2025, 12, 31),
                'Pope Sylvester I',
                '聖シルヴェストロ一世教皇',
                'White',
                'https://www.pauline.or.jp/calendariosanti/'
                'gen_saint365.php?id=123101',
                'https://en.wikipedia.org/wiki/Pope_Sylvester_I',
            ),
        ]
        calendar = LiturgicalCalendar([2026], lang='ja')
        for html_formatting in [False, True]:
            events = _events_by_date(calendar, html_formatting)
            for date, name, summary, color, ja_url, en_url in cases:
                internal = [event for event in calendar[date] if event.name == name]
                components = [
                    event for event in events[date]
                    if _bare_summary(str(event['SUMMARY'])) == summary
                ]
                with self.subTest(
                    html=html_formatting, date=date, name=name,
                ):
                    self.assertEqual(len(internal), 1)
                    self.assertEqual(internal[0].rank, 4)
                    self.assertEqual(internal[0].color, color)
                    self.assertEqual(len(components), 1)
                    self.assertEqual(str(components[0]['SUMMARY']), '› ' + summary)
                    description = str(components[0]['DESCRIPTION'])
                    self.assertTrue(description.startswith('記念\n'))
                    self.assertIn(
                        calendar.translator.format_color(color), description)
                    self.assertIn(ja_url, description)
                    self.assertIn(en_url, description)
                    self.assertNotIn('同じミサで記念されます', description)

    def test_st_dorothy_commemoration_is_unchanged(self):
        date = dt.date(2026, 2, 6)
        calendar = LiturgicalCalendar([2026], lang='ja')
        events = _events_by_date(calendar)[date]
        dorothy = [
            event for event in events
            if _bare_summary(str(event['SUMMARY'])) == '聖ドロテア'
        ]
        self.assertEqual(len(dorothy), 1)
        self.assertEqual(str(dorothy[0]['SUMMARY']), '› 聖ドロテア')
        self.assertTrue(
            str(dorothy[0]['DESCRIPTION']).startswith('記念\n典礼色は赤です。'))

    def test_st_anastasia_has_japanese_name_description_and_link(self):
        expected_description = (
            '記念\n'
            '我らの主イエズス・キリストの御降誕の大祝日の第二ミサ'
            '（暁のミサ）で記念されます。\n'
            'このミサの典礼色は白です。'
        )
        pauline_url = (
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint50.php?id=122501'
        )
        christmas_urls = {
            'https://fisheaters.com/customschristmas2.html',
            'https://en.wikipedia.org/wiki/Christmas',
            'http://www.newadvent.org/cathen/03724b.htm',
        }

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 12, 25)
            calendar = LiturgicalCalendar(
                [year + 1], lang='ja')
            internal = calendar[date]
            for html_formatting in [False, True]:
                components = _events_by_date(
                    calendar, html_formatting)[date]
                christmas, anastasia = components
                with self.subTest(year=year, html=html_formatting):
                    self.assertEqual(
                        str(christmas['SUMMARY']).lstrip(),
                        '我らの主イエズス・キリストの御降誕の大祝日',
                    )
                    self.assertEqual(
                        str(anastasia['SUMMARY']), '› 聖アナスタジア')
                    self.assertTrue(
                        str(anastasia['DESCRIPTION']).startswith(
                            expected_description + '\n\n'))
                    self.assertIn(
                        pauline_url, str(anastasia['DESCRIPTION']))
                    self.assertNotIn(
                        pauline_url, str(christmas['DESCRIPTION']))
                    for url in christmas_urls:
                        self.assertIn(url, str(christmas['DESCRIPTION']))
                        self.assertNotIn(url, str(anastasia['DESCRIPTION']))
                    self.assertNotEqual(
                        str(christmas['UID']), str(anastasia['UID']))

            self.assertEqual(
                [event.name for event in internal],
                ['Christmas', 'St. Anastasia'],
            )

    def test_special_christmas_commemoration_does_not_leak(self):
        cases = [
            (dt.date(2026, 2, 6), 'St. Dorothy'),
            (dt.date(2025, 12, 29), 'St. Thomas Becket'),
            (dt.date(2025, 12, 31), 'Pope Sylvester I'),
        ]
        calendar = LiturgicalCalendar([2026, 2027], lang='ja')
        for date, name in cases:
            event = next(
                event for event in calendar[date] if event.name == name)
            description = event.generate_description(ranking_feast=True)
            with self.subTest(date=date, name=name):
                self.assertIsNone(event.special_commemoration)
                self.assertNotIn('第二ミサ', description)
                self.assertNotIn('暁のミサ', description)

    def test_other_excluded_events_are_unchanged(self):
        seven_sorrows = [
            event
            for event in self.ja_calendar[mf.SevenSorrows.date(2026)]
            if event.name == 'The Seven Sorrows'
        ]
        self.assertEqual(len(seven_sorrows), 1)
        self.assertIsNone(seven_sorrows[0].description_lead)

        june_30_events = self.ja_calendar[dt.date(2026, 6, 30)]
        self.assertEqual(
            [event.name for event in june_30_events],
            ['St. Paul'],
        )
        self.assertIsNone(june_30_events[0].description_lead)
        self.assertEqual(
            june_30_events[0].description_append,
            '聖ペトロも同じミサで記念されます。',
        )

        april_mark = [
            event
            for event in self.ja_calendar[dt.date(2026, 4, 25)]
            if event.name == 'St. Mark'
        ]
        self.assertEqual(len(april_mark), 1)
        self.assertIsNone(april_mark[0].description_lead)

    def test_apostle_commemorations_are_merged_for_all_three_years(self):
        cases = [
            {
                'month': 1,
                'day': 25,
                'name': 'Conversion of St. Paul',
                'removed_name': 'St. Peter',
                'summary': '使徒聖パウロの回心',
                'append': '聖ペトロも同じミサで記念されます。',
                'rank': 3,
                'color': 'White',
                'daily_counts': {2025: 1, 2026: 2, 2027: 1},
            },
            {
                'month': 2,
                'day': 22,
                'name': 'Chair of St. Peter',
                'removed_name': 'St. Paul',
                'summary': '使徒聖ペトロが教座を定めた祝日',
                'append': '聖パウロも同じミサで記念されます。',
                'rank': 2,
                'color': 'White',
                'daily_counts': {2025: 1, 2026: 2, 2027: 1},
            },
            {
                'month': 6,
                'day': 30,
                'name': 'St. Paul',
                'removed_name': 'Commemoration of St. Paul',
                'summary': '使徒聖パウロの記念',
                'append': '聖ペトロも同じミサで記念されます。',
                'rank': 3,
                'color': 'Red',
                'daily_counts': {2025: 1, 2026: 1, 2027: 1},
            },
        ]

        for year in self.years:
            for case in cases:
                date = dt.date(year, case['month'], case['day'])
                internal = self.ja_calendar[date]
                principal = [
                    event for event in internal
                    if event.name == case['name']
                ]
                component = self._component_for(year, {
                    'date': f"{case['day']}-{calendar.month_abbr[case['month']]}",
                    'english_name': case['name'],
                })
                summary = str(component.get('SUMMARY'))
                description = str(component.get('DESCRIPTION'))

                with self.subTest(year=year, date=date):
                    self.assertEqual(
                        len(self.plain_events[date]),
                        case['daily_counts'][year],
                    )
                    self.assertEqual(len(principal), 1)
                    self.assertNotIn(
                        case['removed_name'],
                        [event.name for event in internal],
                    )
                    self.assertEqual(_bare_summary(summary), case['summary'])
                    self.assertNotIn(case['append'], summary)
                    self.assertEqual(description.count(case['append']), 1)
                    self.assertNotIn('祝日の祝日', description)
                    self.assertEqual(principal[0].rank, case['rank'])
                    self.assertEqual(principal[0].color, case['color'])

    def test_apostle_append_text_precedes_links_and_preserves_order(self):
        cases = [
            {
                'date': dt.date(2026, 1, 25),
                'summary': '使徒聖パウロの回心',
                'append': '聖ペトロも同じミサで記念されます。',
                'urls': [
                    'gen_saint365.php?id=012501',
                    'gen_saint50.php?id=062901',
                    'https://fisheaters.com/conversionofstpaul.html',
                    'https://en.wikipedia.org/wiki/'
                    'Conversion_of_Paul_the_Apostle',
                    'https://fisheaters.com/customstimeafterepiphany1.html',
                ],
            },
            {
                'date': dt.date(2026, 2, 22),
                'summary': '使徒聖ペトロが教座を定めた祝日',
                'append': '聖パウロも同じミサで記念されます。',
                'urls': [
                    'gen_saint50.php?id=022201',
                    'gen_saint50.php?id=062902',
                    'https://fisheaters.com/customslent1.html',
                ],
            },
            {
                'date': dt.date(2026, 6, 30),
                'summary': '使徒聖パウロの記念',
                'append': '聖ペトロも同じミサで記念されます。',
                'urls': [
                    'gen_saint50.php?id=062902',
                    'gen_saint50.php?id=062901',
                    'https://en.wikipedia.org/wiki/Paul_the_Apostle',
                    'http://www.newadvent.org/cathen/11567b.htm',
                    'https://fisheaters.com/customstimeafterpentecost1.html',
                ],
            },
        ]

        for case in cases:
            matches = [
                event for event in self.plain_events[case['date']]
                if _bare_summary(str(event.get('SUMMARY'))) == case['summary']
            ]
            self.assertEqual(len(matches), 1)
            description = str(matches[0].get('DESCRIPTION'))
            positions = [description.index(url) for url in case['urls']]

            with self.subTest(date=case['date']):
                self.assertEqual(positions, sorted(positions))
                self.assertLess(
                    description.index(case['append']),
                    description.index('日本語の解説'),
                )
                for url in case['urls']:
                    self.assertEqual(description.count(url), 1)
                self.assertIn('季節の解説（英語）', description)

    def test_apostle_append_text_is_used_in_html_output(self):
        cases = [
            (
                dt.date(2026, 1, 25),
                '使徒聖パウロの回心',
                '聖ペトロも同じミサで記念されます。',
                'gen_saint50.php?id=062901',
            ),
            (
                dt.date(2026, 2, 22),
                '使徒聖ペトロが教座を定めた祝日',
                '聖パウロも同じミサで記念されます。',
                'gen_saint50.php?id=062902',
            ),
            (
                dt.date(2026, 6, 30),
                '使徒聖パウロの記念',
                '聖ペトロも同じミサで記念されます。',
                'gen_saint50.php?id=062901',
            ),
        ]

        for date, summary, append, url in cases:
            matches = [
                event for event in self.html_events[date]
                if _bare_summary(str(event.get('SUMMARY'))) == summary
            ]
            self.assertEqual(len(matches), 1)
            description = str(matches[0].get('DESCRIPTION'))
            with self.subTest(date=date):
                self.assertEqual(description.count(append), 1)
                self.assertIn(f'<a href=https://www.pauline.or.jp/'
                              f'calendariosanti/{url}>', description)
                self.assertLess(
                    description.index(append),
                    description.index('日本語の解説'),
                )

    def test_apostle_override_data_and_local_rows_are_consistent(self):
        self.assertEqual(
            {
                (
                    row['match_type'],
                    row['date'],
                    row['english_name'],
                    row['description_append'],
                )
                for row in self.append_rows
            },
            {
                (
                    'exact_date_and_name',
                    '25-Jan',
                    'Conversion of St. Paul',
                    '聖ペトロも同じミサで記念されます。',
                ),
                (
                    'exact_date_and_name',
                    '22-Feb',
                    'Chair of St. Peter',
                    '聖パウロも同じミサで記念されます。',
                ),
                (
                    'exact_date_and_name',
                    '30-Jun',
                    'St. Paul',
                    '聖ペトロも同じミサで記念されます。',
                ),
            },
        )

        missing_rows = self._read_ja_csv('fixed_feasts_missing.csv')
        keyed_rows = {
            (row['dates_en'], row['en']): row
            for row in missing_rows
        }
        self.assertNotIn(
            ('22-Feb', 'Chair of St. Peter at Antioch'),
            keyed_rows,
        )
        self.assertNotIn(('22-Feb', 'Chair of St. Peter'), keyed_rows)
        chair_override = next(
            row for row in self.append_rows
            if row['english_name'] == 'Chair of St. Peter'
        )
        self.assertEqual(
            chair_override['summary_override'],
            '使徒聖ペトロが教座を定めた祝日',
        )
        self.assertEqual(
            chair_override['description_full_name'],
            '使徒聖ペトロが教座を定めた祝日',
        )
        self.assertEqual(
            chair_override['uid_alias'],
            'アンティオキアにおける聖ペトロの使徒座',
        )
        for removed_key in [
            ('25-Jan', 'St. Peter'),
            ('22-Feb', 'St. Paul'),
            ('30-Jun', 'Commemoration of St. Paul'),
        ]:
            self.assertNotIn(removed_key, keyed_rows)

    def test_june_29_feast_is_unchanged(self):
        for year in self.years:
            date = dt.date(year, 6, 29)
            internal = [
                event for event in self.ja_calendar[date]
                if event.name == 'SS. Peter & Paul'
            ]
            component = self._component_for(year, {
                'date': '29-Jun',
                'english_name': 'SS. Peter & Paul',
            })
            description = str(component.get('DESCRIPTION'))
            with self.subTest(year=year):
                self.assertEqual(len(internal), 1)
                self.assertEqual(internal[0].rank, 1)
                self.assertEqual(internal[0].color, 'Red')
                self.assertIsNone(internal[0].description_append)
                self.assertEqual(
                    description.count('gen_saint365.php?id=062901'), 1)
                self.assertEqual(
                    description.count('gen_saint365.php?id=062902'), 1)

    def test_changed_japanese_summaries_reuse_principal_uids(self):
        old_events = [
            (
                dt.date(2026, 1, 25),
                '› 使徒聖パウロの回心',
                'old-principal-jan@example.test',
            ),
            (
                dt.date(2026, 2, 22),
                '› アンティオキアにおける聖ペトロの使徒座',
                'old-principal-feb@example.test',
            ),
            (
                dt.date(2026, 6, 30),
                '› 聖パウロ',
                'old-principal-jun@example.test',
            ),
            (
                dt.date(2026, 1, 25),
                '› 聖ペトロ',
                'old-removed-jan@example.test',
            ),
            (
                dt.date(2026, 2, 22),
                '› 聖パウロ',
                'old-removed-feb@example.test',
            ),
            (
                dt.date(2026, 6, 30),
                ' 聖パウロの記念',
                'old-removed-jun@example.test',
            ),
        ]
        expected = {
            (dt.date(2026, 1, 25), '使徒聖パウロの回心'):
                'old-principal-jan@example.test',
            (dt.date(2026, 2, 22), '使徒聖ペトロが教座を定めた祝日'):
                'old-principal-feb@example.test',
            (dt.date(2026, 6, 30), '使徒聖パウロの記念'):
                'old-principal-jun@example.test',
        }

        old_calendar = IcsCalendar()
        old_calendar.add('prodid', '-//UID reuse test//EN')
        old_calendar.add('version', '2.0')
        for date, summary, uid in old_events:
            event = IcsEvent()
            event.add('summary', summary)
            event.add('dtstart', date)
            event.add('uid', uid)
            old_calendar.add_component(event)

        with tempfile.TemporaryDirectory() as tmp_dir:
            old_path = Path(tmp_dir) / 'old.ics'
            old_path.write_bytes(old_calendar.to_ical())
            updated = LiturgicalCalendar(
                2026, reuse_uids_from=old_path, lang='ja')
            updated_events = _events_by_date(updated)

        output_uids = {
            str(event.get('UID'))
            for events in updated_events.values()
            for event in events
        }
        for (date, summary), expected_uid in expected.items():
            matches = [
                event for event in updated_events[date]
                if _bare_summary(str(event.get('SUMMARY'))) == summary
            ]
            with self.subTest(date=date, summary=summary):
                self.assertEqual(len(matches), 1)
                self.assertEqual(str(matches[0].get('UID')), expected_uid)
        self.assertTrue({
            'old-removed-jan@example.test',
            'old-removed-feb@example.test',
            'old-removed-jun@example.test',
        }.isdisjoint(output_uids))

    def test_japanese_overrides_do_not_leak_into_english_or_french(self):
        shared_append = {
            'en': 'St. Paul is also commemorated in the same Mass.',
            'fr': (
                'St Paul est également commémoré au cours de la même messe.'),
        }
        for lang in ['en', 'fr']:
            calendar_output = LiturgicalCalendar(
                self.years, lang=lang)
            ical_text = calendar_output.to_ical().decode('utf-8')
            appended_events = [
                event
                for year in calendar_output.liturgical_years.values()
                for events in year.calendar.values()
                for event in events
                if event.description_append is not None
            ]
            shared_lead_events = [
                event
                for year in calendar_output.liturgical_years.values()
                for events in year.calendar.values()
                for event in events
                if event.description_lead is not None
            ]
            with self.subTest(lang=lang):
                self.assertNotIn('記念', ical_text)
                self.assertNotIn('日本の固有ミサ。', ical_text)
                self.assertTrue(all(
                    event.name == 'St. Anastasia'
                    and event.special_commemoration
                    == 'christmas_second_mass'
                    for event in shared_lead_events
                ))
                self.assertEqual(len(shared_lead_events), len(self.years))
                self.assertEqual(len(appended_events), len(self.years))
                self.assertTrue(all(
                    event.name == 'Chair of St. Peter'
                    and event.description_append == shared_append[lang]
                    for event in appended_events
                ))
                self.assertTrue(all(
                    event.summary_override is None
                    for year in calendar_output.liturgical_years.values()
                    for events in year.calendar.values()
                    for event in events
                ))
                shared_day_names = {
                    'Fifth Day within the Octave of Christmas',
                    'Sixth Day within the Octave of Christmas',
                    'Seventh Day within the Octave of Christmas',
                }
                self.assertTrue(all(
                    event.description_full_name_override is None
                    or (
                        event.name in shared_day_names
                        and event.description_full_name_override
                        == calendar_output.translator.format_summary(
                            event.name)
                    )
                    for year in calendar_output.liturgical_years.values()
                    for events in year.calendar.values()
                    for event in events
                ))


class TestJapaneseSameNameDateOverrides(unittest.TestCase):
    years = [2025, 2026, 2027, 2028]

    @staticmethod
    def _components_for(calendar, date, html_formatting=False):
        events = _events_by_date(calendar, html_formatting=html_formatting)
        return events[date]

    def test_st_stephen_dates_remain_distinct(self):
        for year in self.years:
            calendar = LiturgicalCalendar([year, year + 1], lang='ja')
            for html_formatting in [False, True]:
                august_events = self._components_for(
                    calendar, dt.date(year, 8, 2), html_formatting)
                september_events = self._components_for(
                    calendar, dt.date(year, 9, 2), html_formatting)

                august_matches = [
                    event for event in august_events
                    if _bare_summary(str(event.get('SUMMARY')))
                    == '聖ステファノ一世教皇'
                ]
                september_matches = [
                    event for event in september_events
                    if _bare_summary(str(event.get('SUMMARY')))
                    == '聖ステファノ王'
                ]

                with self.subTest(
                    year=year, html_formatting=html_formatting
                ):
                    self.assertEqual(len(august_matches), 1)
                    self.assertEqual(len(september_matches), 1)
                    self.assertNotIn(
                        '聖ステファノ一世教皇',
                        [
                            _bare_summary(str(event.get('SUMMARY')))
                            for event in september_events
                        ],
                    )
                    september_description = str(
                        september_matches[0].get('DESCRIPTION'))
                    self.assertTrue(
                        september_description.startswith(
                            '聖ステファノ王 (証聖者)の祝日は'
                            '三級の祝日です。典礼色は白です。'
                        )
                    )
                    self.assertNotIn(
                        '聖ステファノ一世教皇',
                        september_description,
                    )
                    self.assertIn(
                        'https://en.wikipedia.org/wiki/Stephen_I_of_Hungary',
                        september_description,
                    )

    def test_st_agnes_dates_remain_distinct(self):
        for year in self.years:
            calendar = LiturgicalCalendar([year, year + 1], lang='ja')
            for html_formatting in [False, True]:
                january_21 = self._components_for(
                    calendar, dt.date(year, 1, 21), html_formatting)
                january_28 = self._components_for(
                    calendar, dt.date(year, 1, 28), html_formatting)

                with self.subTest(
                    year=year, html_formatting=html_formatting
                ):
                    self.assertEqual(len(january_21), 1)
                    self.assertEqual(
                        _bare_summary(str(january_21[0].get('SUMMARY'))),
                        '聖アグネス',
                    )
                    self.assertNotIn(
                        '第二の祝日',
                        str(january_21[0].get('SUMMARY')),
                    )
                    january_21_description = str(
                        january_21[0].get('DESCRIPTION'))
                    self.assertTrue(
                        january_21_description.startswith(
                            '聖アグネス (童貞、殉教者)の祝日は'
                            '三級の祝日です。典礼色は赤です。'
                        )
                    )
                    january_21_internal = [
                        event
                        for event in calendar[dt.date(year, 1, 21)]
                        if event.name == 'St. Agnes'
                    ]
                    self.assertEqual(len(january_21_internal), 1)
                    self.assertEqual(january_21_internal[0].rank, 3)
                    self.assertEqual(january_21_internal[0].color, 'Red')

                    self.assertEqual(len(january_28), 2)
                    peter_nolasco = [
                        event for event in january_28
                        if _bare_summary(str(event.get('SUMMARY')))
                        == '聖ペトロ・ノラスコ'
                    ]
                    self.assertEqual(len(peter_nolasco), 1)
                    self.assertTrue(
                        str(peter_nolasco[0].get('DESCRIPTION')).startswith(
                            '聖ペトロ・ノラスコ (証聖者)の祝日は'
                            '三級の祝日です。典礼色は白です。'
                        )
                    )
                    second_feast = [
                        event for event in january_28
                        if _bare_summary(str(event.get('SUMMARY')))
                        == '聖アグネス（第二の祝日）'
                    ]
                    self.assertEqual(len(second_feast), 1)
                    self.assertEqual(
                        str(second_feast[0].get('DESCRIPTION')).splitlines()[:2],
                        ['記念', '典礼色は赤です。'],
                    )

    def test_st_stephen_summary_change_reuses_the_previous_uid(self):
        previous_uid = 'existing-september-stephen@example.test'
        previous_calendar = IcsCalendar()
        previous_calendar.add('prodid', '-//UID reuse test//JA')
        previous_calendar.add('version', '2.0')
        previous_event = IcsEvent()
        previous_event.add('summary', '聖ステファノ一世教皇')
        previous_event.add('dtstart', dt.date(2026, 9, 2))
        previous_event.add('uid', previous_uid)
        previous_calendar.add_component(previous_event)

        with tempfile.TemporaryDirectory() as tmp_dir:
            previous_path = Path(tmp_dir) / 'previous.ics'
            previous_path.write_bytes(previous_calendar.to_ical())
            updated = LiturgicalCalendar(
                [2026, 2027], reuse_uids_from=previous_path, lang='ja')
            updated_events = _events_by_date(updated)

        matches = [
            event for event in updated_events[dt.date(2026, 9, 2)]
            if _bare_summary(str(event.get('SUMMARY'))) == '聖ステファノ王'
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(str(matches[0].get('UID')), previous_uid)

    def test_st_agnes_summary_change_reuses_the_previous_uid(self):
        previous_uid = 'existing-january-agnes@example.test'
        previous_calendar = IcsCalendar()
        previous_calendar.add('prodid', '-//UID reuse test//JA')
        previous_calendar.add('version', '2.0')
        previous_event = IcsEvent()
        previous_event.add('summary', '聖アグネス（第二の祝日）')
        previous_event.add('dtstart', dt.date(2026, 1, 21))
        previous_event.add('uid', previous_uid)
        previous_calendar.add_component(previous_event)

        with tempfile.TemporaryDirectory() as tmp_dir:
            previous_path = Path(tmp_dir) / 'previous.ics'
            previous_path.write_bytes(previous_calendar.to_ical())
            updated = LiturgicalCalendar(
                [2026, 2027], reuse_uids_from=previous_path, lang='ja')
            updated_events = _events_by_date(updated)

        matches = [
            event for event in updated_events[dt.date(2026, 1, 21)]
            if _bare_summary(str(event.get('SUMMARY'))) == '聖アグネス'
        ]
        self.assertEqual(len(matches), 1)
        self.assertEqual(str(matches[0].get('UID')), previous_uid)

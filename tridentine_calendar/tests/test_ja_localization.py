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


class TestJapaneseSameDaySummaryOrdering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.years = [2025, 2026, 2027]
        cls.ja_calendar = LiturgicalCalendar(cls.years, lang='ja')
        cls.plain_ical = cls.ja_calendar.to_ical()
        cls.html_ical = cls.ja_calendar.to_ical(html_formatting=True)
        cls.plain_events = _events_by_date_from_ical(cls.plain_ical)
        cls.html_events = _events_by_date_from_ical(cls.html_ical)

    @staticmethod
    def summaries(events, date):
        return [str(event.get('SUMMARY')) for event in events.get(date, [])]

    def test_representative_same_day_summaries(self):
        self.assertEqual(
            self.summaries(self.plain_events, dt.date(2026, 10, 4)),
            [
                ' 聖霊降臨後第十九主日',
                '› アッシジの聖フランシスコ',
                '» 祈り（ポンペイの聖母）',
            ],
        )
        self.assertEqual(
            self.summaries(self.plain_events, dt.date(2026, 9, 10)),
            [
                ' トレンティーノの聖ニコラオ',
                '› 福者カルロ・スピノラ、福者セバスチアノ木村等殉教者',
            ],
        )
        september_23 = self.summaries(
            self.plain_events, dt.date(2026, 9, 23))
        self.assertEqual(
            september_23,
            [' 9月の四季の斎日', '› 聖リノ教皇', '› 聖テクラ'],
        )
        self.assertFalse(any('Pio' in summary for summary in september_23))

    def test_prefix_and_mark_codepoints_are_exact(self):
        for date, events in self.plain_events.items():
            summaries = [str(event.get('SUMMARY')) for event in events]
            if len(summaries) < 2:
                continue
            has_marker = any(
                summary.startswith(('› ', '» ')) for summary in summaries)
            if not has_marker:
                continue
            for summary in summaries:
                with self.subTest(date=date, summary=repr(summary)):
                    if summary.startswith('› '):
                        self.assertEqual(ord(summary[0]), 0x203A)
                    elif summary.startswith('» '):
                        self.assertEqual(ord(summary[0]), 0x00BB)
                    else:
                        self.assertEqual(repr(summary[:1]), repr(' '))
                        self.assertEqual(ord(summary[0]), 0x0020)
                        self.assertFalse(summary.startswith('  '))

    def test_single_event_summary_is_not_prefixed(self):
        date = dt.date(2026, 9, 9)
        summaries = self.summaries(self.plain_events, date)
        self.assertEqual(len(summaries), 1)
        self.assertFalse(summaries[0].startswith(' '))

    def test_multiple_unmarked_events_are_not_prefixed(self):
        summaries = self.summaries(
            self.plain_events, dt.date(2026, 4, 25))
        self.assertEqual(summaries, ['聖マルコ', '大祈願祭'])
        self.assertFalse(any(summary.startswith(' ') for summary in summaries))

    def test_descriptions_and_html_summaries_are_not_prefixed(self):
        for date in [
            dt.date(2026, 9, 10),
            dt.date(2026, 9, 23),
            dt.date(2026, 10, 4),
        ]:
            for event in self.plain_events[date]:
                self.assertFalse(str(event.get('DESCRIPTION')).startswith(' '))
            for summary in self.summaries(self.html_events, date):
                self.assertFalse(summary.startswith(' '))

        self.assertEqual(
            self.summaries(self.html_events, dt.date(2026, 10, 4)),
            [
                '聖霊降臨後第十九主日',
                '› アッシジの聖フランシスコ',
                '» 祈り（ポンペイの聖母）',
            ],
        )

    def test_english_and_french_summaries_are_not_prefixed(self):
        for lang in ['en', 'fr']:
            events = _events_by_date(LiturgicalCalendar(2026, lang=lang))
            with self.subTest(lang=lang):
                self.assertFalse(any(
                    str(event.get('SUMMARY')).startswith(' ')
                    for day_events in events.values()
                    for event in day_events
                ))

    def test_existing_unprefixed_uids_are_reused(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            old_ical = LiturgicalCalendar(2026, lang='ja').to_ical(
                html_formatting=True)
            filename = Path(tmp_dir) / 'old-ja.ics'
            filename.write_bytes(old_ical)
            old_events = _events_by_date_from_ical(old_ical)

            updated = LiturgicalCalendar(
                2026, reuse_uids_from=filename, lang='ja')
            new_events = _events_by_date_from_ical(updated.to_ical())

            old_uids = {
                (date, str(event.get('SUMMARY'))): str(event.get('UID'))
                for date, events in old_events.items()
                for event in events
            }
            new_uids = {
                (date, str(event.get('SUMMARY')).removeprefix(' ')):
                str(event.get('UID'))
                for date, events in new_events.items()
                for event in events
            }
            self.assertEqual(old_uids, new_uids)


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
        translated_name = self.ja_calendar.translator.format_summary(
            row['english_name'])
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
        self.assertEqual(len(self.override_rows), 72)
        self.assertEqual(len(self.commemoration_rows), 56)
        self.assertEqual(len(self.proper_mass_rows), 16)

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
        peter = self._component_for(2026, {
            'date': '25-Jan',
            'english_name': 'St. Peter',
        })
        peter_description = str(peter.get('DESCRIPTION'))
        self.assertIn(
            'https://www.pauline.or.jp/calendariosanti/'
            'gen_saint50.php?id=062901',
            peter_description,
        )
        self.assertIn('季節の解説（英語）', peter_description)
        self.assertIn(
            'https://fisheaters.com/customstimeafterepiphany1.html',
            peter_description,
        )

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
            {'date': '25-Jan', 'english_name': 'St. Peter'},
            self.html_events,
        )
        summary = str(event.get('SUMMARY'))
        description = str(event.get('DESCRIPTION'))

        self.assertEqual(summary, '› 聖ペトロ')
        self.assertTrue(description.startswith('記念\n'))
        self.assertNotIn('第四級', description)
        self.assertIn(
            '<a href=https://www.pauline.or.jp/calendariosanti/'
            'gen_saint50.php?id=062901>',
            description,
        )

    def test_blank_colors_are_not_inferred(self):
        cases = [
            {'date': '25-Jan', 'english_name': 'St. Peter'},
            {'date': '22-Feb', 'english_name': 'St. Paul'},
        ]
        for row in cases:
            component = self._component_for(2026, row)
            internal_event = self._internal_event(2026, row)
            description = str(component.get('DESCRIPTION'))
            with self.subTest(date=row['date'], name=row['english_name']):
                self.assertEqual(internal_event.color, '')
                self.assertNotIn('典礼色は', description)

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

    def test_four_explicit_exclusions_are_unchanged(self):
        excluded = [
            (dt.date(2026, 12, 4), 'St. Barbara'),
            (dt.date(2026, 12, 29), 'St. Thomas Becket'),
            (dt.date(2026, 12, 31), 'Pope Sylvester I'),
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
            ['Commemoration of St. Paul', 'St. Paul'],
        )
        self.assertTrue(all(
            event.description_lead is None for event in june_30_events))

        april_mark = [
            event
            for event in self.ja_calendar[dt.date(2026, 4, 25)]
            if event.name == 'St. Mark'
        ]
        self.assertEqual(len(april_mark), 1)
        self.assertIsNone(april_mark[0].description_lead)

        christmas_names = [
            event.name
            for event in self.ja_calendar[dt.date(2026, 12, 25)]
        ]
        self.assertNotIn('St. Anastasia', christmas_names)

    def test_english_and_french_are_not_affected(self):
        for lang in ['en', 'fr']:
            calendar_output = LiturgicalCalendar(
                self.years, lang=lang)
            ical_text = calendar_output.to_ical().decode('utf-8')
            with self.subTest(lang=lang):
                self.assertNotIn('記念', ical_text)
                self.assertNotIn('日本の固有ミサ。', ical_text)
                self.assertTrue(all(
                    event.description_lead is None
                    for year in calendar_output.liturgical_years.values()
                    for events in year.calendar.values()
                    for event in events
                ))

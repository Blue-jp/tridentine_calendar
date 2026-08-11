import datetime as dt
import tempfile
import unittest
import os
import icalendar as ical

from .. import movable_feasts as mf
from .. import utils
from ..tridentine_calendar import LiturgicalCalendar
from ..tridentine_calendar import LiturgicalCalendarEvent
from ..tridentine_calendar import LiturgicalCalendarEventUrl
from ..tridentine_calendar import LiturgicalSeason
from ..tridentine_calendar import LiturgicalYear
from ..tridentine_calendar import _feast_sort_key


class TestLiturgicalCalendarEventUrl(unittest.TestCase):

    def test_init(self):
        feast_link = LiturgicalCalendarEventUrl(
            'https://en.wikipedia.org/Saturnin', 'Saturnin')
        self.assertEqual(feast_link.url, 'https://en.wikipedia.org/Saturnin')
        self.assertEqual(feast_link.description, 'Saturnin')

    def test_from_json(self):
        json_obj = {
            'url': 'https://en.wikipedia.org/Saturnin',
            'description': 'Saturnin',
        }
        feast_link = LiturgicalCalendarEventUrl.from_json(json_obj)
        self.assertEqual(feast_link.url, 'https://en.wikipedia.org/Saturnin')
        self.assertEqual(feast_link.description, 'Saturnin (Wikipedia)')

        json_obj = 'https://en.wikipedia.org/Saturnin'
        feast_link = LiturgicalCalendarEventUrl.from_json(json_obj)
        self.assertEqual(feast_link.url, 'https://en.wikipedia.org/Saturnin')
        self.assertEqual(feast_link.description, 'Saturnin (Wikipedia)')

        json_obj = 'http://www.newadvent.org/cathen/01471a.htm'
        feast_link = LiturgicalCalendarEventUrl.from_json(
            json_obj, default='Saturninus')
        self.assertEqual(feast_link.url, 'http://www.newadvent.org/cathen/01471a.htm')
        self.assertEqual(feast_link.description, 'Saturninus (New Advent)')

        json_obj = 'https://fisheaters.com/customsadvent2a.html'
        feast_link = LiturgicalCalendarEventUrl.from_json(
            json_obj, default='St. Barbara')
        self.assertEqual(feast_link.url, 'https://fisheaters.com/customsadvent2a.html')
        self.assertEqual(feast_link.description, 'St. Barbara (Fish Eaters)')

        json_obj = 'https://en.wikipedia.org/Saint_Nicholas'
        feast_link = LiturgicalCalendarEventUrl.from_json(json_obj)
        self.assertEqual(feast_link.url, 'https://en.wikipedia.org/Saint_Nicholas')
        self.assertEqual(feast_link.description, 'Saint Nicholas (Wikipedia)')

        json_obj = 'https://en.wikipedia.org/wiki/Saint_Sylvester%27s_Day'
        feast_link = LiturgicalCalendarEventUrl.from_json(json_obj)
        self.assertEqual(
            feast_link.url, 'https://en.wikipedia.org/wiki/Saint_Sylvester%27s_Day')
        self.assertEqual(feast_link.description, 'Saint Sylvester\'s Day (Wikipedia)')

    def test_to_href(self):
        feast_link = LiturgicalCalendarEventUrl(
            'https://en.wikipedia.org/Saturnin', 'Saturnin (Wikipedia)')
        self.assertEqual(
            feast_link.to_href(),
            '<a href=https://en.wikipedia.org/Saturnin>Saturnin (Wikipedia)</a>',
        )


class TestLiturgicalCalendarSeason(unittest.TestCase):

    def test_init(self):
        season = LiturgicalSeason('Advent')
        self.assertEqual(season.name, 'Advent')

    def test_from_json_key(self):
        season = LiturgicalSeason.from_json_key('Advent')
        self.assertEqual(season.name, 'Advent')
        self.assertEqual(season.color, 'Violet')

    def test_from_date(self):
        date = dt.date(2018, 12, 4)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Advent')
        self.assertEqual(season.color, 'Violet')

        date = dt.date(2018, 12, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Christmastide')
        self.assertEqual(season.color, 'White')

        date = dt.date(2019, 1, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Time after Epiphany')
        self.assertEqual(season.color, 'Green')

        date = dt.date(2019, 2, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Septuagesima')
        self.assertEqual(season.color, 'Violet')

        date = dt.date(2019, 3, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Lent')
        self.assertEqual(season.color, 'Violet')

        date = dt.date(2019, 4, 8)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Passiontide')
        self.assertEqual(season.color, 'Violet')

        date = dt.date(2019, 4, 15)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Holy Week')
        self.assertEqual(season.color, 'Violet')

        date = dt.date(2019, 4, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Eastertide')
        self.assertEqual(season.color, 'White')

        date = dt.date(2019, 6, 25)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Time after Pentecost')
        self.assertEqual(season.color, 'Green')

        date = dt.date(2019, 11, 2)
        season = LiturgicalSeason.from_date(date)
        self.assertEqual(season.name, 'Hallowtide')

    def test_full_name(self):
        season = LiturgicalSeason('Advent')
        self.assertEqual(season.full_name(capitalize=True), 'Advent')

        season = LiturgicalSeason('Time after Pentecost')
        self.assertEqual(season.full_name(capitalize=True), 'The Time after Pentecost')

        season = LiturgicalSeason('Time after Epiphany')
        self.assertEqual(season.full_name(capitalize=False), 'the Time after Epiphany')


class TestLiturgicalCalendarEvent(unittest.TestCase):

    def test_from_json_st_nicholas(self):
        date = dt.date(2018, 12, 6)
        json_obj = {
            'name': 'St. Nicholas',
            'titles': ['Bishop', 'Confessor'],
            'urls': [
                'https://fisheaters.com/customsadvent3.html',
                'https://en.wikipedia.org/wiki/Saint_Nicholas',
            ],
            'obligation': False,
            'class': 3,
            'liturgical_event': True,
        }
        event = LiturgicalCalendarEvent.from_json(date, json_obj)

        self.assertEqual(event.name, 'St. Nicholas')
        self.assertEqual(event.rank, 3)
        self.assertEqual(event.liturgical_event, True)
        self.assertEqual(event.holy_day, False)
        self.assertEqual(event.urls[0].description, 'St. Nicholas (Fish Eaters)')
        self.assertEqual(event.urls[1].description, 'Saint Nicholas (Wikipedia)')
        self.assertEqual(event.color, 'White')
        self.assertEqual(event.feast, True)

    def test_from_json_st_saturninus(self):
        date = dt.date(2018, 11, 30)
        json_obj = {
            'name': 'St. Andrew',
            'titles': ['Apostle'],
            'urls': [
                'https://en.wikipedia.org/wiki/Andrew_the_Apostle',
            ],
            'obligation': False,
            'class': 2,
            'liturgical_event': True,
        }
        event = LiturgicalCalendarEvent.from_json(date, json_obj)

        self.assertEqual(event.name, 'St. Andrew')
        self.assertEqual(event.rank, 2)
        self.assertEqual(event.liturgical_event, True)
        self.assertEqual(event.feast, True)
        self.assertEqual(event.holy_day, False)
        self.assertEqual(event.urls[0].description, 'Andrew the Apostle (Wikipedia)')
        self.assertEqual(event.color, 'Red')

    def test_full_name(self):
        date = dt.date(2018, 12, 6)
        event = LiturgicalCalendarEvent(date, 'St. Nicholas', rank=3)
        expected_output = 'The Feast of St. Nicholas'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

        expected_output = 'the Feast of St. Nicholas'
        self.assertEqual(event.full_name(capitalize=False), expected_output)

        date = dt.date(2019, 10, 27)
        event = LiturgicalCalendarEvent(date, 'Christ the King', rank=3)
        expected_output = 'The Feast of Christ the King'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

        date = dt.date(2019, 6, 28)
        event = LiturgicalCalendarEvent(date, 'Vigil of SS. Peter & Paul', rank=2)
        expected_output = 'The Vigil of the Feast of SS. Peter & Paul'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

        date = dt.date(2019, 8, 14)
        event = LiturgicalCalendarEvent(date, 'Vigil of the Assumption', rank=2)
        expected_output = 'The Vigil of the Assumption'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

        date = dt.date(2020, 1, 5)
        event = LiturgicalCalendarEvent(date, 'Twelfth Night', rank=1)
        expected_output = 'Twelfth Night'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

        date = dt.date(2020, 1, 19)
        event = LiturgicalCalendarEvent(date, 'Second Sunday after Epiphany', rank=2)
        expected_output = 'The Second Sunday after Epiphany'
        self.assertEqual(event.full_name(capitalize=True), expected_output)

    def test_generate_description(self):
        url = LiturgicalCalendarEventUrl(
            'https://fisheaters.com/customsadvent5.html',
            description='Feast of the Immaculate Conception',
        )
        event = LiturgicalCalendarEvent(
            dt.date(2018, 12, 8),
            'The Immaculate Conception',
            liturgical_event=True,
            holy_day=True,
            urls=[url],
            rank=1,
            color='White',
            feast=True,
        )

        expected_description = (
            'The Feast of the Immaculate Conception is a Holy Day of Obligation. '
            'Today is a Class I feast. '
            'The liturgical color is white.\n\n'
            'More information about the Feast of the Immaculate Conception:\n'
            '• https://fisheaters.com/customsadvent5.html\n\n'
            'More information about Advent:\n'
        )
        description = event.generate_description(html_formatting=False)
        self.assertTrue(description.startswith(expected_description))

    def test_is_fixed(self):
        event = LiturgicalCalendarEvent(
            dt.date(2018, 12, 8),
            'The Immaculate Conception',
        )
        self.assertTrue(event.is_fixed())

        event = LiturgicalCalendarEvent(dt.date(2019, 4, 21), 'Easter')
        self.assertFalse(event.is_fixed())


class TestFeastComparison(unittest.TestCase):

    def test_feast_comparison(self):
        feast = LiturgicalCalendarEvent(
            dt.date(2018, 4, 1), name='Easter', rank=1, liturgical_event=True)
        self.assertEqual(_feast_sort_key(feast), 1)

        feast = LiturgicalCalendarEvent(
            dt.date(2018, 10, 31), name='Halloween', liturgical_event=False)
        self.assertEqual(_feast_sort_key(feast), 4)


class TestLiturgicalYearSmoke(unittest.TestCase):

    def test_liturgical_year(self):
        self.assertIsNotNone(LiturgicalYear(2018))


class TestLiturgicalYearSundayDates(unittest.TestCase):

    def test_liturgical_year_sunday_dates(self):
        litcal_2018 = LiturgicalYear(2018)
        self.assertEqual(
            litcal_2018[dt.date(2018, 9, 2)][0].name,
            'Fifteenth Sunday after Pentecost',
        )
        self.assertEqual(
            litcal_2018[dt.date(2018, 11, 25)][0].name,
            'Last Sunday after Pentecost',
        )


class TestLiturgicalYearIcal(unittest.TestCase):
    def test_to_ical_smoke(self):
        ics_calendar = LiturgicalYear(2019).to_ical()
        self.assertIsNotNone(ics_calendar)


class TestLiturgicalCalendar(unittest.TestCase):
    def _event_uid_map(self, ical_data):
        calendar = ical.Calendar.from_ical(ical_data)
        return {
            (
                str(event['summary']),
                ical.vDDDTypes.from_ical(event['dtstart']),
            ): str(event['uid'])
            for event in calendar.walk('VEVENT')
        }

    def test_liturgical_calendar_init_single_year(self):
        litcal = LiturgicalCalendar(2018)
        self.assertIsNotNone(litcal)

    def test_liturgical_calendar_init_multiple_years(self):
        litcal = LiturgicalCalendar([2018, 2019])
        self.assertIsNotNone(litcal)

    def test_liturgical_calendar_getitem(self):
        litcal = LiturgicalCalendar([2018, 2019])
        event = litcal[dt.date(2018, 12, 25)][0]
        self.assertEqual(event.name, 'Christmas')
        event = litcal[dt.date(2019, 4, 21)][0]
        self.assertEqual(event.name, 'Easter')

    def test_january_1_octave_day_name_and_uid_alias(self):
        years = [2025, 2026, 2027, 2028]
        summaries = {
            'en': 'Octave Day of the Nativity of the Lord',
            'fr': "L'Octave de la Nativité du Seigneur",
            'ja': 'わが主のご降誕後の八日目',
        }
        old_summaries = {
            'en': 'The Circumcision',
            'fr': 'La Circoncision',
            'ja': '主イエズス・キリストの御割礼の祝日',
        }
        description_prefixes = {
            'en': (
                'Octave Day of the Nativity of the Lord is a Holy Day of '
                'Obligation. Today is a Class I feast. The liturgical color '
                'is white.'),
            'fr': (
                "La fête de l'Octave de la Nativité du Seigneur est un jour "
                "d'obligation. Aujourd'hui est une fête de Ire classe. "
                'La couleur liturgique est le blanc.'),
            'ja': (
                'わが主のご降誕後の八日目は守るべき祝日です。'
                '今日は一級の祝日です。典礼色は白です。'),
        }
        urls = [
            'https://fisheaters.com/customschristmas7.html',
            'https://en.wikipedia.org/wiki/Feast_of_the_Circumcision_of_Christ',
            'http://www.newadvent.org/cathen/03779a.htm',
            'https://fisheaters.com/customschristmas1.html',
        ]

        for lang in ['en', 'fr', 'ja']:
            old_calendar = ical.Calendar()
            expected_uids = {}
            for year in years:
                event_date = dt.date(year, 1, 1)
                uid = f'old-january-1-{lang}-{year}@example.test'
                old_event = ical.Event()
                old_event.add('summary', old_summaries[lang])
                old_event.add('dtstart', event_date)
                old_event.add('uid', uid)
                old_calendar.add_component(old_event)
                expected_uids[event_date] = uid

            with tempfile.TemporaryDirectory() as tmp_dir:
                old_path = os.path.join(tmp_dir, 'old.ics')
                with open(old_path, 'wb') as fp:
                    fp.write(old_calendar.to_ical())
                calendar = LiturgicalCalendar(
                    years, reuse_uids_from=old_path, lang=lang)

                for html_formatting in [False, True]:
                    output = ical.Calendar.from_ical(
                        calendar.to_ical(html_formatting))
                    all_output_uids = [
                        str(event['UID'])
                        for event in output.walk('VEVENT')
                    ]
                    for year in years:
                        event_date = dt.date(year, 1, 1)
                        internal = calendar[event_date]
                        components = [
                            event for event in output.walk('VEVENT')
                            if ical.vDDDTypes.from_ical(
                                event['DTSTART']) == event_date
                        ]
                        with self.subTest(
                            lang=lang, year=year, html=html_formatting,
                        ):
                            self.assertEqual(len(internal), 1)
                            self.assertEqual(
                                internal[0].name,
                                'Octave Day of the Nativity of the Lord',
                            )
                            self.assertEqual(internal[0].rank, 1)
                            self.assertEqual(internal[0].color, 'White')
                            self.assertTrue(internal[0].liturgical_event)
                            self.assertTrue(internal[0].feast)
                            self.assertTrue(internal[0].holy_day)
                            self.assertIn(
                                'The Circumcision', internal[0].uid_aliases)
                            self.assertEqual(len(components), 1)
                            self.assertEqual(
                                str(components[0]['SUMMARY']), summaries[lang])
                            self.assertNotEqual(
                                str(components[0]['SUMMARY']),
                                old_summaries[lang],
                            )
                            description = str(components[0]['DESCRIPTION'])
                            self.assertTrue(
                                description.startswith(
                                    description_prefixes[lang]))
                            for url in urls:
                                self.assertIn(url, description)
                            if html_formatting:
                                self.assertIn(
                                    '>The Circumcision (Fish Eaters)</a>',
                                    description,
                                )
                                self.assertIn(
                                    '>The Circumcision (New Advent)</a>',
                                    description,
                                )
                            uid = expected_uids[event_date]
                            self.assertEqual(str(components[0]['UID']), uid)
                            self.assertEqual(all_output_uids.count(uid), 1)

    def test_january_18_chair_is_removed_but_st_prisca_remains(self):
        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 1, 18)
            for lang in ['en', 'fr', 'ja']:
                with self.subTest(year=year, lang=lang):
                    names = [
                        event.name
                        for event in LiturgicalCalendar([year], lang=lang)[date]
                    ]
                    self.assertNotIn("St. Peter's Chair", names)
                    self.assertIn('St. Prisca', names)

    def test_st_george_commemoration_uses_martyr_red(self):
        summaries = {
            'en': 'St. George',
            'fr': 'St Georges',
            'ja': '聖ジェオルジオ',
        }
        description_leads = {
            'en': (
                'Today is a commemoration. '
                'The liturgical color is red.'
            ),
            'fr': (
                "Aujourd'hui, c'est une commémoraison. "
                'La couleur liturgique est le rouge.'
            ),
            'ja': '記念\n典礼色は赤です。',
        }
        urls = {
            'https://www.fisheaters.com/feastofstgeorge.html',
            'https://en.wikipedia.org/wiki/Saint_George',
            'http://www.newadvent.org/cathen/06453a.htm',
        }

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 4, 23)
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar(
                    [utils.liturgical_year(date)], lang=lang)
                internal = [
                    event for event in calendar[date]
                    if event.name == 'St. George'
                ]
                with self.subTest(year=year, lang=lang, internal=True):
                    self.assertEqual(len(internal), 1)
                    event = internal[0]
                    self.assertEqual(event.rank, 4)
                    self.assertEqual(event.titles, ['Martyr'])
                    self.assertEqual(event.color, 'Red')
                    self.assertTrue(event.liturgical_event)
                    self.assertTrue(event.feast)
                    self.assertEqual(
                        {link.url for link in event.urls}, urls)

                for html_formatting in [False, True]:
                    components = [
                        component for component in ical.Calendar.from_ical(
                            calendar.to_ical(html_formatting)
                        ).walk('VEVENT')
                        if ical.vDDDTypes.from_ical(
                            component['DTSTART']) == date
                        and str(component['SUMMARY']).lstrip(' ›»')
                        == summaries[lang]
                    ]
                    with self.subTest(
                        year=year,
                        lang=lang,
                        html=html_formatting,
                    ):
                        self.assertEqual(len(components), 1)
                        description = str(components[0]['DESCRIPTION'])
                        if lang == 'ja' or year in [2026, 2027]:
                            self.assertTrue(
                                description.startswith(
                                    description_leads[lang]))
                        elif lang == 'en':
                            self.assertIn(
                                'Commemoration of St. George', description)
                        else:
                            self.assertIn(
                                'commémoraison de St Georges', description)
                        if lang == 'en':
                            self.assertNotIn(
                                'liturgical color is white', description)
                        elif lang == 'fr':
                            self.assertNotIn(
                                'couleur liturgique est le blanc', description)
                        else:
                            self.assertNotIn('典礼色は白です', description)

    def test_february_22_chair_and_st_paul_commemoration(self):
        summaries = {
            'en': 'Chair of St. Peter',
            'fr': 'La Chaire de St Pierre',
            'ja': '使徒聖ペトロが教座を定めた祝日',
        }
        commemorations = {
            'en': 'St. Paul is also commemorated in the same Mass.',
            'fr': (
                'St Paul est également commémoré au cours de la même messe.'),
            'ja': '聖パウロも同じミサで記念されます。',
        }

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 2, 22)
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar([year], lang=lang)
                matches = [
                    event for event in calendar[date]
                    if event.name == 'Chair of St. Peter'
                ]
                components = [
                    event for event in ical.Calendar.from_ical(
                        calendar.to_ical()).walk('VEVENT')
                    if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                    and str(event['SUMMARY']).lstrip(' ›»') == summaries[lang]
                ]
                with self.subTest(year=year, lang=lang):
                    self.assertEqual(len(matches), 1)
                    self.assertEqual(matches[0].rank, 2)
                    self.assertEqual(matches[0].color, 'White')
                    self.assertEqual(
                        matches[0].description_append,
                        commemorations[lang],
                    )
                    self.assertEqual(len(components), 1)
                    self.assertIn(
                        commemorations[lang],
                        str(components[0]['DESCRIPTION']),
                    )
                    self.assertNotIn(
                        'St. Paul',
                        [event.name for event in calendar[date]],
                    )
                    if year == 2026:
                        self.assertTrue(
                            str(components[0]['SUMMARY']).startswith('› '))

    def test_st_anastasia_is_a_special_christmas_commemoration(self):
        summaries = {
            'en': ('Christmas', 'St. Anastasia'),
            'fr': ('Noël', 'Ste Anastasie'),
            'ja': (
                '我らの主イエズス・キリストの御降誕の大祝日',
                '聖アナスタジア',
            ),
        }
        descriptions = {
            'en': (
                'Commemoration\n'
                'St. Anastasia is commemorated at the Second Mass of '
                'Christmas (Mass at Dawn).\n'
                'The liturgical color of this Mass is white.'
            ),
            'fr': (
                'Commémoraison\n'
                'Ste Anastasie est commémorée à la deuxième messe de Noël '
                "(messe de l'aurore).\n"
                'La couleur liturgique de cette messe est le blanc.'
            ),
            'ja': (
                '記念\n'
                '我らの主イエズス・キリストの御降誕の大祝日の第二ミサ'
                '（暁のミサ）で記念されます。\n'
                'このミサの典礼色は白です。'
            ),
        }

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 12, 25)
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar(
                    [utils.liturgical_year(date)], lang=lang)
                internal = calendar[date]
                with self.subTest(year=year, lang=lang, internal=True):
                    self.assertEqual(
                        [event.name for event in internal],
                        ['Christmas', 'St. Anastasia'],
                    )
                    christmas, anastasia = internal
                    self.assertEqual(christmas.rank, 1)
                    self.assertEqual(christmas.color, 'White')
                    self.assertTrue(christmas.holy_day)
                    self.assertEqual(anastasia.rank, 4)
                    self.assertEqual(anastasia.color, 'White')
                    self.assertEqual(anastasia.titles, ['Martyr'])
                    self.assertTrue(anastasia.liturgical_event)
                    self.assertTrue(anastasia.feast)
                    self.assertFalse(anastasia.holy_day)
                    self.assertEqual(
                        anastasia.special_commemoration,
                        'christmas_second_mass',
                    )

                for html_formatting in [False, True]:
                    components = [
                        event for event in ical.Calendar.from_ical(
                            calendar.to_ical(html_formatting)).walk('VEVENT')
                        if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                    ]
                    with self.subTest(
                        year=year, lang=lang, html=html_formatting,
                    ):
                        self.assertEqual(len(components), 2)
                        self.assertEqual(
                            str(components[0]['SUMMARY']).lstrip(),
                            summaries[lang][0],
                        )
                        self.assertEqual(
                            str(components[1]['SUMMARY']),
                            '› ' + summaries[lang][1],
                        )
                        christmas_description = str(
                            components[0]['DESCRIPTION'])
                        anastasia_description = str(
                            components[1]['DESCRIPTION'])
                        self.assertNotIn(
                            'Anastasia', christmas_description)
                        self.assertNotIn(
                            'アナスタジア', christmas_description)
                        self.assertTrue(
                            anastasia_description.startswith(
                                descriptions[lang] + '\n\n'))
                        self.assertNotIn('Class IV', anastasia_description)
                        self.assertNotIn('IVe classe', anastasia_description)
                        self.assertNotIn('第四', anastasia_description)

    def test_st_barbara_is_a_shared_commemoration(self):
        summaries = {
            'en': 'St. Barbara',
            'fr': 'Ste Barbe',
            'ja': '聖バルバラ',
        }
        description_leads = {
            'en': (
                'Today is a commemoration.\n'
                'The liturgical color is red.'
            ),
            'fr': (
                "Aujourd'hui, c'est une commémoraison.\n"
                'La couleur liturgique est le rouge.'
            ),
            'ja': (
                '一般ローマ暦では記念です。\n'
                '聖バルバラの固有ミサの典礼色は赤です。'
            ),
        }
        japanese_uncertainty = (
            '日本固有暦では同日に福者イエロニモ・デ・アンジェリス、'
            'シモン遠甫等殉教者の固有ミサがありますが、その等級を確認'
            'できないため、聖バルバラが実際にミサで記念されるかは未確定'
            'です。'
        )
        urls = [
            'https://fisheaters.com/customsadvent2a.html',
            'https://en.wikipedia.org/wiki/Saint_Barbara',
            'https://www.newadvent.org/cathen/02284d.htm',
        ]
        local_name = 'Bs. Jerome de Angelis, Simon Empo & Companions'

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 12, 4)
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar(
                    [utils.liturgical_year(date)], lang=lang)
                expected_names = ['St. Peter Chrysologus', 'St. Barbara']
                if lang == 'ja':
                    expected_names.append(local_name)
                with self.subTest(year=year, lang=lang, internal=True):
                    self.assertEqual(
                        [event.name for event in calendar[date]],
                        expected_names,
                    )
                    peter, barbara = calendar[date][:2]
                    self.assertEqual(peter.rank, 3)
                    self.assertEqual(peter.color, 'White')
                    self.assertEqual(barbara.rank, 4)
                    self.assertEqual(barbara.color, 'Red')
                    self.assertEqual(barbara.titles, ['Virgin', 'Martyr'])
                    self.assertTrue(barbara.liturgical_event)
                    self.assertTrue(barbara.feast)
                    self.assertFalse(barbara.holy_day)
                    self.assertEqual(
                        [url.url for url in barbara.urls], urls)
                    if lang == 'ja':
                        local = calendar[date][2]
                        self.assertEqual(local.rank, 4)
                        self.assertEqual(local.color, 'Red')
                        self.assertEqual(local.titles, ['Martyr'])
                        self.assertTrue(local.liturgical_event)

                for html_formatting in [False, True]:
                    components = [
                        event for event in ical.Calendar.from_ical(
                            calendar.to_ical(html_formatting)).walk('VEVENT')
                        if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                    ]
                    barbara_components = [
                        event for event in components
                        if str(event['SUMMARY']).lstrip(' ›»') == summaries[lang]
                    ]
                    with self.subTest(
                        year=year, lang=lang, html=html_formatting,
                    ):
                        self.assertEqual(len(barbara_components), 1)
                        barbara_component = barbara_components[0]
                        self.assertEqual(
                            str(barbara_component['SUMMARY']),
                            '› ' + summaries[lang],
                        )
                        description = str(barbara_component['DESCRIPTION'])
                        self.assertTrue(
                            description.startswith(
                                description_leads[lang] + '\n\n'))
                        self.assertNotIn('has no special liturgy', description)
                        self.assertNotIn("n'a pas de liturgie spéciale", description)
                        self.assertNotIn('特別な典礼はありません', description)
                        self.assertNotIn('Class IV', description)
                        self.assertNotIn('IVe classe', description)
                        self.assertNotIn('四級', description)
                        if lang == 'ja':
                            self.assertNotIn(
                                japanese_uncertainty, description)
                        for url in urls:
                            self.assertEqual(description.count(url), 1)

    def test_st_barbara_keeps_reference_display_on_advent_sunday(self):
        date = dt.date(2033, 12, 4)
        summaries = {
            'en': 'St. Barbara',
            'fr': 'Ste Barbe',
            'ja': '聖バルバラ',
        }
        japanese_description = (
            '一般ローマ暦では記念です。\n'
            '聖バルバラの固有ミサの典礼色は赤です。'
        )
        japanese_uncertainty = (
            '日本固有暦では同日に福者イエロニモ・デ・アンジェリス、'
            'シモン遠甫等殉教者の固有ミサがありますが、その等級を確認'
            'できないため、聖バルバラが実際にミサで記念されるかは未確定'
            'です。'
        )
        for lang in ['en', 'fr', 'ja']:
            calendar = LiturgicalCalendar(
                [utils.liturgical_year(date)], lang=lang)
            self.assertEqual(calendar[date][0].rank, 1)
            for html_formatting in [False, True]:
                components = [
                    event for event in ical.Calendar.from_ical(
                        calendar.to_ical(html_formatting)).walk('VEVENT')
                    if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                ]
                barbara = [
                    event for event in components
                    if str(event['SUMMARY']).lstrip(' ›»') == summaries[lang]
                ]
                with self.subTest(lang=lang, html=html_formatting):
                    self.assertEqual(len(barbara), 1)
                    self.assertEqual(
                        str(barbara[0]['SUMMARY']), '› ' + summaries[lang])
                    description = str(barbara[0]['DESCRIPTION'])
                    if lang == 'en':
                        self.assertIn('is outranked by', description)
                        self.assertNotIn(
                            'Today is a commemoration', description)
                    elif lang == 'fr':
                        self.assertIn('est omise', description)
                        self.assertNotIn(
                            "Aujourd'hui, c'est une commémoraison",
                            description,
                        )
                    else:
                        self.assertTrue(
                            description.startswith(
                                japanese_description + '\n\n'))
                        self.assertNotIn(
                            japanese_uncertainty, description)

    def test_st_barbara_reuses_nonliturgical_uids(self):
        summaries = {
            'en': {
                'St. Peter Chrysologus': 'St. Peter Chrysologus',
                'St. Barbara': '» St. Barbara',
            },
            'fr': {
                'St. Peter Chrysologus': 'St Pierre Chrysologue',
                'St. Barbara': '» Ste Barbe',
            },
            'ja': {
                'St. Peter Chrysologus': ' 聖ペトロ・クリゾロゴ',
                'St. Barbara': '» 聖バルバラ',
                'Bs. Jerome de Angelis, Simon Empo & Companions': (
                    '› 福者イエロニモ・デ・アンジェリス、シモン遠甫等殉教者'),
            },
        }

        for lang, named_summaries in summaries.items():
            old_calendar = ical.Calendar()
            expected = {}
            for year in [2025, 2026, 2027, 2028]:
                date = dt.date(year, 12, 4)
                for internal_name, summary in named_summaries.items():
                    uid = f'old-{lang}-{year}-{internal_name}@example.test'
                    event = ical.Event()
                    event.add('summary', summary)
                    event.add('dtstart', date)
                    event.add('uid', uid)
                    old_calendar.add_component(event)
                    expected[(date, internal_name)] = uid

            with tempfile.TemporaryDirectory() as tmp_dir:
                old_path = os.path.join(tmp_dir, 'old.ics')
                with open(old_path, 'wb') as fp:
                    fp.write(old_calendar.to_ical())
                for html_formatting in [False, True]:
                    calendar = LiturgicalCalendar(
                        [2026, 2027, 2028, 2029],
                        reuse_uids_from=old_path,
                        lang=lang,
                    )
                    components = ical.Calendar.from_ical(
                        calendar.to_ical(html_formatting)).walk('VEVENT')
                    output_uids = [
                        str(event['UID']) for event in components
                        if event.name == 'VEVENT'
                    ]
                    self.assertEqual(len(output_uids), len(set(output_uids)))
                    for (date, internal_name), old_uid in expected.items():
                        bare_summary = named_summaries[internal_name].lstrip(' ›»')
                        matches = [
                            event for event in components
                            if event.name == 'VEVENT'
                            and ical.vDDDTypes.from_ical(event['DTSTART']) == date
                            and str(event['SUMMARY']).lstrip(' ›»') == bare_summary
                        ]
                        with self.subTest(
                            lang=lang,
                            html=html_formatting,
                            date=date,
                            name=internal_name,
                        ):
                            self.assertEqual(len(matches), 1)
                            self.assertEqual(str(matches[0]['UID']), old_uid)

    def test_passiontide_friday_and_seven_sorrows_commemoration(self):
        summaries = {
            'en': (
                'Friday after the First Sunday in Passiontide',
                'The Seven Sorrows',
            ),
            'fr': (
                'Vendredi après le premier dimanche de la Passion',
                'Les sept Douleurs de la B.V.M.',
            ),
            'ja': (
                'ご受難の主日後の金曜日',
                '童貞聖マリアの七つの御苦しみ',
            ),
        }
        descriptions = {
            'en': (
                'Commemoration\n'
                'The Seven Sorrows is commemorated in the Mass of Friday '
                'after the First Sunday in Passiontide.\n'
                'The liturgical color of this Mass is violet.'
            ),
            'fr': (
                'Commémoraison\n'
                'À la messe du vendredi après le premier dimanche de la '
                'Passion, les sept Douleurs de la B.V.M. sont commémorées.\n'
                'La couleur liturgique de cette messe est le violet.'
            ),
            'ja': (
                '記念\n'
                '童貞聖マリアの七つの御苦しみはご受難の主日後の金曜日の'
                'ミサで記念されます。\n'
                'このミサの典礼色は紫です。'
            ),
        }
        unobserved_descriptions = {
            'en': (
                'Commemoration\n'
                'This year the Class I feast of St. Joseph takes precedence, '
                'so the Seven Sorrows is not commemorated in the Mass.'
            ),
            'fr': (
                'Commémoraison\n'
                'Cette année, la fête de St Joseph de Ire classe a préséance ; '
                'les sept Douleurs de la B.V.M. ne sont donc pas commémorées '
                'à la messe.'
            ),
            'ja': (
                '記念\n'
                '今年は聖ヨゼフの一級祝日が優先するため、'
                '童貞聖マリアの七つの御苦しみはミサでは記念されません。'
            ),
        }
        outranked_main_descriptions = {
            'en': (
                'This year Friday after the First Sunday in Passiontide is '
                'outranked by the Feast of St. Joseph'
            ),
            'fr': (
                'Cette année, Vendredi après le premier dimanche de la '
                'Passion est omise.'
            ),
            'ja': (
                '今年は聖ヨゼフがご受難の主日後の金曜日に優先します。'
                'この平日は三級の平日です。'
            ),
        }
        expected_names = {
            2025: [
                'Friday after the First Sunday in Passiontide',
                'Pope Leo the Great',
                'The Seven Sorrows',
            ],
            2026: [
                'Friday after the First Sunday in Passiontide',
                'St. John Damascene',
                'The Seven Sorrows',
            ],
            2027: [
                'St. Joseph',
                'Friday after the First Sunday in Passiontide',
                'The Seven Sorrows',
            ],
            2028: [
                'Friday after the First Sunday in Passiontide',
                'The Seven Sorrows',
            ],
        }
        expected_dates = {
            2025: dt.date(2025, 4, 11),
            2026: dt.date(2026, 3, 27),
            2027: dt.date(2027, 3, 19),
            2028: dt.date(2028, 4, 7),
        }

        for year, date in expected_dates.items():
            self.assertEqual(
                mf.FridayAfterFirstSundayInPassiontide.date(year), date)
            self.assertEqual(mf.SevenSorrows.date(year), date)
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar([year], lang=lang)
                events = calendar[date]
                main_name = 'Friday after the First Sunday in Passiontide'
                main = next(
                    event for event in events
                    if event.name == main_name
                )
                seven_sorrows = next(
                    event for event in events
                    if event.name == 'The Seven Sorrows'
                )
                with self.subTest(year=year, lang=lang, internal=True):
                    self.assertEqual(
                        [event.name for event in events], expected_names[year])
                    self.assertEqual(main.rank, 3)
                    self.assertEqual(main.color, 'Violet')
                    self.assertTrue(main.liturgical_event)
                    self.assertFalse(main.feast)
                    self.assertEqual(seven_sorrows.rank, 4)
                    self.assertEqual(seven_sorrows.color, 'Violet')
                    self.assertTrue(seven_sorrows.liturgical_event)
                    self.assertTrue(seven_sorrows.feast)
                    self.assertEqual(
                        seven_sorrows.special_commemoration,
                        'passiontide_friday',
                    )
                    self.assertEqual(
                        seven_sorrows.special_commemoration_observed,
                        year != 2027,
                    )
                    self.assertEqual(
                        seven_sorrows.special_commemoration_top_rank_threshold,
                        3,
                    )
                    if year == 2027:
                        self.assertEqual(events[0].name, 'St. Joseph')
                        self.assertEqual(events[0].rank, 1)
                        self.assertEqual(events[0].color, 'White')
                    self.assertEqual(
                        {url.url for url in seven_sorrows.urls},
                        {
                            'https://fisheaters.com/customslent10.html',
                            'https://en.wikipedia.org/wiki/Friday_of_Sorrows',
                            'https://en.wikipedia.org/wiki/Our_Lady_of_Sorrows',
                            'http://www.newadvent.org/cathen/14151b.htm',
                        },
                    )

                for html_formatting in [False, True]:
                    components = [
                        event for event in ical.Calendar.from_ical(
                            calendar.to_ical(html_formatting)).walk('VEVENT')
                        if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                    ]
                    by_summary = {
                        str(event['SUMMARY']).lstrip(' ›»'): event
                        for event in components
                    }
                    with self.subTest(
                        year=year, lang=lang, html=html_formatting,
                    ):
                        self.assertIn(summaries[lang][0], by_summary)
                        self.assertIn(summaries[lang][1], by_summary)
                        self.assertTrue(
                            str(by_summary[summaries[lang][1]]['SUMMARY'])
                            .startswith('› ')
                        )
                        description = str(
                            by_summary[summaries[lang][1]]['DESCRIPTION'])
                        expected_description = (
                            unobserved_descriptions[lang]
                            if year == 2027 else descriptions[lang]
                        )
                        self.assertTrue(
                            description.startswith(
                                expected_description + '\n\n'))
                        self.assertNotIn('Class III feast', description)
                        self.assertNotIn('三級の祝日', description)
                        self.assertNotIn('受難週の金曜日', description)
                        if year == 2027:
                            self.assertNotIn(
                                'is commemorated in the Mass', description)
                            self.assertNotIn(
                                'ミサで記念されます', description)
                            self.assertNotIn(
                                'sont commémorées', description)
                            self.assertNotIn(
                                'liturgical color of this Mass', description)
                            self.assertNotIn(
                                'このミサの典礼色は紫', description)
                            self.assertNotIn(
                                'couleur liturgique de cette messe',
                                description,
                            )
                            main_description = str(
                                by_summary[
                                    summaries[lang][0]]['DESCRIPTION'])
                            self.assertTrue(
                                main_description.startswith(
                                    outranked_main_descriptions[lang]))

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 9, 15)
            for lang in ['en', 'fr', 'ja']:
                event = next(
                    event for event in LiturgicalCalendar([year], lang=lang)[date]
                    if event.name == 'The Seven Sorrows'
                )
                with self.subTest(year=year, lang=lang, september=True):
                    self.assertEqual(event.rank, 2)
                    self.assertEqual(event.color, 'White')
                    self.assertIsNone(event.special_commemoration)

    def test_passiontide_seven_sorrows_reuses_its_previous_uid(self):
        summaries = {
            'en': 'The Seven Sorrows',
            'fr': 'Les sept Douleurs de la B.V.M.',
            'ja': '童貞聖マリアの七つの御苦しみ',
        }
        main_summaries = {
            'en': 'Friday after the First Sunday in Passiontide',
            'fr': 'Vendredi après le premier dimanche de la Passion',
            'ja': 'ご受難の主日後の金曜日',
        }

        for lang in ['en', 'fr', 'ja']:
            old_calendar = ical.Calendar()
            old_uids = {}
            for year in [2025, 2026, 2027, 2028]:
                date = mf.SevenSorrows.date(year)
                old_summary = summaries[lang]
                if year == 2027:
                    old_summary = '› ' + old_summary
                elif lang == 'ja' and year in [2025, 2026]:
                    old_summary = ' ' + old_summary
                old_uid = f'old-seven-sorrows-{lang}-{year}@example.test'
                old_event = ical.Event()
                old_event.add('summary', old_summary)
                old_event.add('dtstart', date)
                old_event.add('uid', old_uid)
                old_calendar.add_component(old_event)
                old_uids[date] = old_uid

            with tempfile.TemporaryDirectory() as tmp_dir:
                old_path = os.path.join(tmp_dir, 'old.ics')
                with open(old_path, 'wb') as fp:
                    fp.write(old_calendar.to_ical())
                calendar = LiturgicalCalendar(
                    [2025, 2026, 2027, 2028],
                    reuse_uids_from=old_path,
                    lang=lang,
                )
                for html_formatting in [False, True]:
                    components = ical.Calendar.from_ical(
                        calendar.to_ical(html_formatting))
                    for date, old_uid in old_uids.items():
                        date_components = [
                            event for event in components.walk('VEVENT')
                            if ical.vDDDTypes.from_ical(
                                event['DTSTART']) == date
                        ]
                        by_summary = {
                            str(event['SUMMARY']).lstrip(' ›»'): event
                            for event in date_components
                        }
                        with self.subTest(
                            lang=lang, html=html_formatting, date=date,
                        ):
                            self.assertEqual(
                                str(by_summary[summaries[lang]]['UID']),
                                old_uid,
                            )
                            self.assertNotEqual(
                                str(by_summary[main_summaries[lang]]['UID']),
                                old_uid,
                            )

    def test_st_anastasia_does_not_replace_the_christmas_uid(self):
        summaries = {
            'en': 'Christmas',
            'fr': 'Noël',
            'ja': '我らの主イエズス・キリストの御降誕の大祝日',
        }
        anastasia_summaries = {
            'en': 'St. Anastasia',
            'fr': 'Ste Anastasie',
            'ja': '聖アナスタジア',
        }

        for year in [2025, 2026, 2027, 2028]:
            date = dt.date(year, 12, 25)
            for lang in ['en', 'fr', 'ja']:
                old_uid = f'old-christmas-{lang}-{year}@example.test'
                old_calendar = ical.Calendar()
                old_event = ical.Event()
                old_event.add('summary', summaries[lang])
                old_event.add('dtstart', date)
                old_event.add('uid', old_uid)
                old_calendar.add_component(old_event)

                with tempfile.TemporaryDirectory() as tmp_dir:
                    old_path = os.path.join(tmp_dir, 'old.ics')
                    with open(old_path, 'wb') as fp:
                        fp.write(old_calendar.to_ical())
                    calendar = LiturgicalCalendar(
                        [utils.liturgical_year(date)],
                        reuse_uids_from=old_path,
                        lang=lang,
                    )
                    for html_formatting in [False, True]:
                        components = [
                            event for event in ical.Calendar.from_ical(
                                calendar.to_ical(html_formatting)
                            ).walk('VEVENT')
                            if ical.vDDDTypes.from_ical(
                                event['DTSTART']) == date
                        ]
                        by_summary = {
                            str(event['SUMMARY']).lstrip(' ›»'):
                            str(event['UID'])
                            for event in components
                        }
                        with self.subTest(
                            year=year, lang=lang, html=html_formatting,
                        ):
                            self.assertEqual(
                                by_summary[summaries[lang]], old_uid)
                            self.assertNotEqual(
                                by_summary[anastasia_summaries[lang]],
                                old_uid,
                            )

    def test_christmas_octave_days_and_commemorations(self):
        summaries = {
            'en': {
                'Fifth Day within the Octave of Christmas': (
                    'Fifth Day within the Octave of Christmas'),
                'Sixth Day within the Octave of Christmas': (
                    'Sixth Day within the Octave of Christmas'),
                'Seventh Day within the Octave of Christmas': (
                    'Seventh Day within the Octave of Christmas'),
                'St. Thomas Becket': 'St. Thomas Becket',
                'Pope Sylvester I': 'Pope Sylvester I',
            },
            'fr': {
                'Fifth Day within the Octave of Christmas': (
                    "Cinquième jour dans l'Octave de Noël"),
                'Sixth Day within the Octave of Christmas': (
                    "Sixième jour dans l'Octave de Noël"),
                'Seventh Day within the Octave of Christmas': (
                    "Septième jour dans l'Octave de Noël"),
                'St. Thomas Becket': 'St Thomas Becket',
                'Pope Sylvester I': 'St Sylvestre Ier',
            },
            'ja': {
                'Fifth Day within the Octave of Christmas': (
                    '御降誕の大祝日の八日間中の五日目'),
                'Sixth Day within the Octave of Christmas': (
                    '御降誕の大祝日の八日間中の六日目'),
                'Seventh Day within the Octave of Christmas': (
                    '御降誕の大祝日の八日間中の七日目'),
                'St. Thomas Becket': '聖トマス・ベケット',
                'Pope Sylvester I': '聖シルヴェストロ一世教皇',
            },
        }
        cases = [
            (dt.date(2025, 12, 29),
             'Fifth Day within the Octave of Christmas',
             'St. Thomas Becket', 'Red'),
            (dt.date(2025, 12, 30),
             'Sixth Day within the Octave of Christmas', None, None),
            (dt.date(2025, 12, 31),
             'Seventh Day within the Octave of Christmas',
             'Pope Sylvester I', 'White'),
        ]
        descriptions = {
            'en': '{} is Class II. The liturgical color is white.',
            'fr': "Le {} est de IIe classe. La couleur liturgique est le blanc.",
            'ja': '{}は二級です。典礼色は白です。',
        }
        forbidden_day_types = {
            'en': ('feria',),
            'fr': ('férie',),
            'ja': ('平日', '\u5e73\u4f11\u65e5'),
        }

        for lang in ['en', 'fr', 'ja']:
            calendar = LiturgicalCalendar([2026], lang=lang)
            for html_formatting in [False, True]:
                components = ical.Calendar.from_ical(
                    calendar.to_ical(html_formatting))
                for date, day_name, saint_name, saint_color in cases:
                    events = calendar[date]
                    date_components = [
                        event for event in components.walk('VEVENT')
                        if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                    ]
                    with self.subTest(
                        lang=lang, date=date, html=html_formatting,
                    ):
                        self.assertEqual(
                            events[0].liturgical_day_kind,
                            'day_within_octave',
                        )
                        self.assertEqual(events[0].name, day_name)
                        self.assertEqual(events[0].rank, 2)
                        self.assertEqual(events[0].color, 'White')
                        self.assertTrue(events[0].liturgical_event)
                        self.assertFalse(events[0].feast)
                        translated_name = summaries[lang][day_name]
                        self.assertEqual(
                            str(date_components[0]['SUMMARY']).lstrip(),
                            translated_name,
                        )
                        description_name = translated_name
                        if lang == 'fr':
                            description_name = (
                                description_name[0].lower()
                                + description_name[1:]
                            )
                        expected = descriptions[lang].format(description_name)
                        description = str(date_components[0]['DESCRIPTION'])
                        self.assertIn(expected, description)
                        for forbidden in forbidden_day_types[lang]:
                            self.assertNotIn(forbidden, description.lower())

                        if saint_name is None:
                            self.assertEqual(len(events), 1)
                            self.assertEqual(len(date_components), 1)
                            continue

                        self.assertEqual(len(events), 2)
                        self.assertEqual(events[1].name, saint_name)
                        self.assertEqual(events[1].rank, 4)
                        self.assertEqual(events[1].color, saint_color)
                        self.assertTrue(events[1].liturgical_event)
                        self.assertTrue(events[1].feast)
                        self.assertEqual(
                            str(date_components[1]['SUMMARY']),
                            '› ' + summaries[lang][saint_name],
                        )
                        saint_description = str(
                            date_components[1]['DESCRIPTION'])
                        self.assertNotIn('Class IV', saint_description)
                        self.assertNotIn('IVe classe', saint_description)
                        self.assertNotIn(
                            'also commemorated in the same Mass',
                            saint_description,
                        )

    def test_christmas_octave_japanese_names_reuse_previous_uids(self):
        names = [
            (
                'Fifth Day within the Octave of Christmas',
                '主の御降誕の八日間内第五日',
                '御降誕の大祝日の八日間中の五日目',
                29,
            ),
            (
                'Sixth Day within the Octave of Christmas',
                '主の御降誕の八日間内第六日',
                '御降誕の大祝日の八日間中の六日目',
                30,
            ),
            (
                'Seventh Day within the Octave of Christmas',
                '主の御降誕の八日間内第七日',
                '御降誕の大祝日の八日間中の七日目',
                31,
            ),
        ]
        old_calendar = ical.Calendar()
        old_uids = {}
        for year in [2025, 2026, 2027, 2028]:
            for internal_name, old_summary, _, day in names:
                date = dt.date(year, 12, day)
                if date.weekday() == 6:
                    continue
                uid = f'old-ja-{year}-{day}@example.test'
                old_event = ical.Event()
                old_event.add('summary', old_summary)
                old_event.add('dtstart', date)
                old_event.add('uid', uid)
                old_calendar.add_component(old_event)
                old_uids[(date, internal_name)] = uid

        with tempfile.TemporaryDirectory() as tmp_dir:
            old_path = os.path.join(tmp_dir, 'old.ics')
            with open(old_path, 'wb') as fp:
                fp.write(old_calendar.to_ical())
            calendar = LiturgicalCalendar(
                [2026, 2027, 2028, 2029],
                reuse_uids_from=old_path,
                lang='ja',
            )
            for html_formatting in [False, True]:
                components = ical.Calendar.from_ical(
                    calendar.to_ical(html_formatting))
                used_uids = [
                    str(event['UID']) for event in components.walk('VEVENT')
                ]
                for (date, internal_name), old_uid in old_uids.items():
                    _, old_summary, new_summary, _ = next(
                        row for row in names if row[0] == internal_name)
                    matches = [
                        event for event in components.walk('VEVENT')
                        if ical.vDDDTypes.from_ical(event['DTSTART']) == date
                        and str(event['SUMMARY']).lstrip(' ›»') == new_summary
                    ]
                    with self.subTest(
                        date=date,
                        internal_name=internal_name,
                        html=html_formatting,
                    ):
                        self.assertEqual(len(matches), 1)
                        self.assertEqual(str(matches[0]['UID']), old_uid)
                        self.assertEqual(used_uids.count(old_uid), 1)
                        self.assertNotIn(old_summary, str(matches[0]['SUMMARY']))
                        self.assertIn(
                            new_summary
                            + 'は二級です。典礼色は白です。',
                            str(matches[0]['DESCRIPTION']),
                        )

    def test_christmas_octave_weekdays_are_omitted_on_sunday(self):
        cases = [
            (dt.date(2024, 12, 29),
             'Fifth Day within the Octave of Christmas',
             'St. Thomas Becket'),
            (dt.date(2028, 12, 31),
             'Seventh Day within the Octave of Christmas',
             'Pope Sylvester I'),
            (dt.date(2029, 12, 30),
             'Sixth Day within the Octave of Christmas', None),
        ]
        for date, omitted_name, saint_name in cases:
            for lang in ['en', 'fr', 'ja']:
                calendar = LiturgicalCalendar(
                    [utils.liturgical_year(date)], lang=lang)
                names = [event.name for event in calendar[date]]
                with self.subTest(date=date, lang=lang):
                    self.assertEqual(
                        names[0], 'Sunday within the Octave of Christmas')
                    self.assertNotIn(omitted_name, names)
                    if saint_name:
                        self.assertEqual(names[1:], [saint_name])
                        self.assertEqual(calendar[date][1].rank, 4)
                    else:
                        self.assertEqual(len(names), 1)

    def test_christmas_commemoration_uids_survive_new_order_marker(self):
        summaries = {
            'en': ('St. Thomas Becket', 'Pope Sylvester I'),
            'fr': ('St Thomas Becket', 'St Sylvestre Ier'),
            'ja': ('聖トマス・ベケット', '聖シルヴェストロ一世教皇'),
        }
        internal_names = ('St. Thomas Becket', 'Pope Sylvester I')

        for lang in ['en', 'fr', 'ja']:
            old_calendar = ical.Calendar()
            old_uids = {}
            for year in [2025, 2026, 2027, 2028]:
                for month, day, summary, internal_name in [
                    (12, 29, summaries[lang][0], internal_names[0]),
                    (12, 31, summaries[lang][1], internal_names[1]),
                ]:
                    event_date = dt.date(year, month, day)
                    uid = f'old-{lang}-{year}-{internal_name}@example.test'
                    event = ical.Event()
                    event.add('summary', summary)
                    event.add('dtstart', event_date)
                    event.add('uid', uid)
                    old_calendar.add_component(event)
                    old_uids[(event_date, internal_name)] = uid

            with tempfile.TemporaryDirectory() as tmp_dir:
                old_path = os.path.join(tmp_dir, 'old.ics')
                with open(old_path, 'wb') as fp:
                    fp.write(old_calendar.to_ical())
                for html_formatting in [False, True]:
                    calendar = LiturgicalCalendar(
                        [2026, 2027, 2028, 2029],
                        reuse_uids_from=old_path,
                        lang=lang,
                    )
                    components = ical.Calendar.from_ical(
                        calendar.to_ical(html_formatting))
                    for (event_date, internal_name), old_uid in old_uids.items():
                        date_components = [
                            event for event in components.walk('VEVENT')
                            if ical.vDDDTypes.from_ical(
                                event['DTSTART']) == event_date
                        ]
                        saint_summary = summaries[lang][
                            internal_names.index(internal_name)]
                        saint = [
                            event for event in date_components
                            if str(event['SUMMARY']).lstrip(' ›»') == saint_summary
                        ]
                        with self.subTest(
                            lang=lang,
                            html=html_formatting,
                            date=event_date,
                            name=internal_name,
                        ):
                            self.assertEqual(len(saint), 1)
                            self.assertEqual(str(saint[0]['UID']), old_uid)
                            self.assertNotEqual(
                                str(date_components[0]['UID']), old_uid)

    def test_liturgical_calendar_description(self):
        litcal = LiturgicalCalendar(2019)
        event = litcal[dt.date(2018, 12, 8)][0]
        description = event.generate_description(
            html_formatting=False, ranking_feast=True
        )
        self.assertTrue(
            description.startswith(
                'The Feast of the Immaculate Conception is a Holy Day of Obligation.'
            ),
        )

    def test_liturgical_calendar_to_ics(self):
        ics_calendar = LiturgicalYear(2019).to_ical()
        self.assertIsNotNone(ics_calendar)

    def test_japanese_calendar_metadata(self):
        expected_name = '1962年版ローマ・ミサ典書（1960年教会暦）'
        expected_desc = (
            '1960年に公布され、1961年1月1日より施行された教会暦'
            '（典礼暦）。この暦は、1962年版ローマ・ミサ典書に'
            '採用された。'
        )

        for year in [2025, 2026, 2027]:
            with self.subTest(year=year):
                ical_data = LiturgicalCalendar(year, lang='ja').to_ical()
                calendar = ical.Calendar.from_ical(ical_data)

                self.assertEqual(str(calendar.get('X-WR-CALNAME')), expected_name)
                self.assertEqual(str(calendar.get('X-WR-CALDESC')), expected_desc)
                self.assertEqual(
                    str(calendar.get('PRODID')),
                    '-//Joe Antognini//Tridentine Calendar//JA'
                )
                self.assertEqual(str(calendar.get('VERSION')), '2.0')
                self.assertIsNone(calendar.get('CALSCALE'))
                self.assertIsNone(calendar.get('METHOD'))
                self.assertIsNone(calendar.get('X-WR-TIMEZONE'))
                self.assertNotIn(b'X-WR-CALNAME;LANGUAGE=ja', ical_data)
                self.assertNotIn(b'X-WR-CALDESC;LANGUAGE=ja', ical_data)

    def test_english_and_french_calendar_metadata_is_unchanged(self):
        for lang in ['en', 'fr']:
            calendar = ical.Calendar.from_ical(
                LiturgicalCalendar(2026, lang=lang).to_ical())

            self.assertEqual(str(calendar.get('X-WR-CALNAME')),
                             'Tridentine calendar')
            self.assertEqual(
                str(calendar.get('X-WR-CALDESC')),
                'Liturgical calendar using the 1962 Roman Catholic rubrics.'
            )
            self.assertEqual(
                str(calendar.get('PRODID')),
                f'-//Joe Antognini//Tridentine Calendar//{lang.upper()}'
            )
            self.assertEqual(str(calendar.get('VERSION')), '2.0')

    def test_extend_existing_ics(self):
        litcal = LiturgicalCalendar(2018)

        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, 'cal.ics')
            with open(filename, 'wb') as fp:
                fp.write(litcal.to_ical())

            before_events = self._event_uid_map(litcal.to_ical())
            new_litcal = LiturgicalCalendar(2019)
            new_litcal.extend_existing_ical(filename, use_html_formatting=False)

            with open(filename, 'rb') as fp:
                extended_calendar = ical.Calendar.from_ical(fp.read())
            event_dates = [
                ical.vDDDTypes.from_ical(event['dtstart'])
                for event in extended_calendar.walk('VEVENT')
            ]

            self.assertGreater(len(event_dates), len(before_events))
            self.assertIn(2019, {date.year for date in event_dates})

    def test_reuse_uids(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cal1 = LiturgicalCalendar(2018)
            ical1_out = cal1.to_ical()
            fn = os.path.join(tmp_dir, 'cal.ics')
            with open(fn, 'wb') as fp:
                fp.write(ical1_out)

            cal2 = LiturgicalCalendar(2018, reuse_uids_from=fn)
            ical2_out = cal2.to_ical()

            uids1 = self._event_uid_map(ical1_out)
            uids2 = self._event_uid_map(ical2_out)

            self.assertEqual(uids1, uids2)
            self.assertIn(('› St. Francis Xavier', dt.date(2017, 12, 3)), uids2)
            self.assertIn(('» Las Posadas', dt.date(2017, 12, 16)), uids2)
            self.assertIn(('› St. Francis Xavier', dt.date(2017, 12, 3)),
                          cal2.uid_map)
            self.assertIn(('» Las Posadas', dt.date(2017, 12, 16)),
                          cal2.uid_map)

    def test_reuse_uids_with_japanese_summaries(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cal1 = LiturgicalCalendar(2018, lang='ja')
            ical1_out = cal1.to_ical()
            fn = os.path.join(tmp_dir, 'cal.ics')
            with open(fn, 'wb') as fp:
                fp.write(ical1_out)

            cal2 = LiturgicalCalendar(2018, reuse_uids_from=fn, lang='ja')
            ical2_out = cal2.to_ical()

            uids1 = self._event_uid_map(ical1_out)
            uids2 = self._event_uid_map(ical2_out)
            japanese_keys = [
                key for key in uids1
                if any(ord(ch) > 127 and ch not in '›»' for ch in key[0])
            ]

            self.assertEqual(uids1, uids2)
            self.assertTrue(japanese_keys)
            self.assertIn(japanese_keys[0], cal2.uid_map)

    def test_titles_in_parentheses(self):
        from tridentine_calendar.i18n import Translator
        # English test
        event_en = LiturgicalCalendarEvent(
            dt.date(2018, 7, 14),
            'St. Bonaventure',
            titles=['Bishop', 'Confessor', 'Doctor of the Church'],
            rank=3,
            color='White',
            liturgical_event=True,
            feast=True,
            lang='en',
            translator=Translator(lang='en')
        )
        desc_en = event_en.generate_description()
        self.assertIn(
            'The Feast of St. Bonaventure (Bishop, Confessor, Doctor of the '
            'Church) is a Class III feast.',
            desc_en
        )
        self.assertIn('The liturgical color is white.', desc_en)
        # Verify that titles are not repeated at the end
        self.assertFalse(desc_en.strip().endswith('Doctor of the Church.'))

        # Test subsequent name occurrence (e.g. in URL info) has no titles
        event_en.urls = [
            LiturgicalCalendarEventUrl('https://example.com', 'Bonaventure')
        ]
        desc_en_with_urls = event_en.generate_description()
        self.assertIn(
            'More information about the Feast of St. Bonaventure:',
            desc_en_with_urls
        )
        self.assertNotIn(
            'More information about the Feast of St. Bonaventure (Bishop, '
            'Confessor, Doctor of the Church):',
            desc_en_with_urls
        )

        # French test
        event_fr = LiturgicalCalendarEvent(
            dt.date(2018, 7, 14),
            'St. Bonaventure',
            titles=['Bishop', 'Confessor', 'Doctor of the Church'],
            rank=3,
            color='White',
            liturgical_event=True,
            feast=True,
            lang='fr',
            translator=Translator(lang='fr')
        )
        desc_fr = event_fr.generate_description()
        # Verify capitalization and placement.
        self.assertIn(
            'La fête de St Bonaventure (évêque, confesseur, docteur de '
            'l\'Église) est une fête de III',
            desc_fr
        )
        self.assertIn('La couleur liturgique est le blanc.', desc_fr)

        event_fr.urls = [
            LiturgicalCalendarEventUrl('https://example.com', 'Bonaventure')
        ]
        desc_fr_with_urls = event_fr.generate_description()
        self.assertIn(
            "Plus d'informations sur la fête de St Bonaventure :",
            desc_fr_with_urls
        )
        self.assertNotIn(
            "Plus d'informations sur la fête de st Bonaventure (évêque, "
            "confesseur, docteur de l'Église) :",
            desc_fr_with_urls
        )

        # Japanese test
        event_ja = LiturgicalCalendarEvent(
            dt.date(2018, 7, 14),
            'St. Bonaventure',
            titles=['Bishop', 'Confessor', 'Doctor of the Church'],
            rank=3,
            color='White',
            liturgical_event=True,
            feast=True,
            lang='ja',
            translator=Translator(lang='ja')
        )
        desc_ja = event_ja.generate_description()
        # Print for debugging or assert basic structure
        self.assertIn('聖ボナヴェントゥラ', desc_ja)
        self.assertIn('司教', desc_ja)
        self.assertIn('証聖者', desc_ja)
        self.assertIn('教会博士', desc_ja)
        self.assertIn('(', desc_ja)
        self.assertIn(')', desc_ja)

        event_ja.urls = [
            LiturgicalCalendarEventUrl('https://example.com', 'Bonaventure')
        ]
        desc_ja_with_urls = event_ja.generate_description()
        self.assertIn('英語の解説', desc_ja_with_urls)
        self.assertIn('https://example.com', desc_ja_with_urls)
        self.assertNotIn(
            '聖ボナヴェントゥラ (司教、証聖者、教会博士)の祝日についての詳細情報：',
            desc_ja_with_urls
        )

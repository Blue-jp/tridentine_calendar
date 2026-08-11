import datetime as dt
from tridentine_calendar.i18n import Translator
from tridentine_calendar.tridentine_calendar import LiturgicalCalendar


def test_fr_translator_basic():
    translator = Translator(lang='fr')
    assert translator.translate('Monday') == 'Lundi'
    assert translator.translate('Advent') == "l'Avent"
    assert translator.translate('White') == 'Blanc'
    assert translator.get_ordinal(1) == 'premier'
    assert translator.get_ordinal(2) == 'deuxième'


def test_fr_feast_full_name():
    translator = Translator(lang='fr')
    # Normal feast
    assert translator.format_feast_full_name(
        'St. Hilary', 3) == 'la fête de St Hilaire'
    # Elision
    assert translator.format_feast_full_name(
        'The Annunciation', 1) == "la fête de l'Annonciation"
    # Already has "La"
    assert translator.format_feast_full_name(
        'The Circumcision', 1) == 'la fête de la Circoncision'
    assert translator.format_feast_full_name(
        'Octave Day of the Nativity of the Lord', 1
    ) == "la fête de l'Octave de la Nativité du Seigneur"
    # Commemoration
    assert translator.format_feast_full_name(
        'St. Hilary', 4) == 'la commémoraison de St Hilaire'


def test_fr_class_feria():
    translator = Translator(lang='fr')
    assert translator.format_class_feria(
        "Aujourd'hui", 1, True) == "Aujourd'hui est une fête de Ire classe."
    assert translator.format_class_feria(
        'Cette férie', 3, False) == 'Cette férie est une férie de IIIe classe.'
    assert translator.format_liturgical_day_class(
        "Cinquième jour dans l'Octave de Noël", 2, 'day_within_octave'
    ) == "Le cinquième jour dans l'Octave de Noël est de IIe classe."


def test_fr_liturgical_calendar_output():
    # Test generation for a specific date in French
    cal = LiturgicalCalendar(2024, lang='fr')
    # Jan 1st 2024 is the Octave Day of the Nativity
    date = dt.date(2024, 1, 1)
    events = cal[date]
    assert len(events) > 0
    assert events[0].name == 'Octave Day of the Nativity of the Lord'
    assert events[0].full_name() == (
        "La fête de l'Octave de la Nativité du Seigneur")

    description = events[0].generate_description()
    assert 'La couleur liturgique est le blanc.' in description
    # Since it is a holy day of obligation, "Aujourd'hui" is used instead of
    # the full name in the class_feria string
    assert "Aujourd'hui est une fête de Ire classe." in description


def test_fr_plural_agreement():
    translator = Translator(lang='fr')

    # Test "Les"
    assert "sont" in translator.format_class_feria("Les martyrs", 2, True)
    assert "n'ont pas" in translator.format_no_special_liturgy("Les Grandes Ô")

    # Test "Sts"
    assert "sont" in translator.format_class_feria("Sts Abdon et Sennen", 3, True)

    # Test "Stes"
    assert "sont" in translator.format_class_feria("Stes Perpétue et Félicité", 3, True)

    # Test outranking plural
    outranking = translator.format_outranking("Les martyrs", "Une fête", True)
    assert "sont omises" in outranking

    # Test holy day plural
    holy = translator.format_holy_day("Les Grandes Ô")
    assert "sont" in holy


def test_fr_christmas_octave_day_names():
    translator = Translator(lang='fr')
    assert translator.translate(
        'Fifth Day within the Octave of Christmas'
    ) == "Cinquième jour dans l'Octave de Noël"
    assert translator.translate(
        'Sixth Day within the Octave of Christmas'
    ) == "Sixième jour dans l'Octave de Noël"
    assert translator.translate(
        'Seventh Day within the Octave of Christmas'
    ) == "Septième jour dans l'Octave de Noël"


def test_fr_st_anastasia_name_and_special_commemoration():
    translator = Translator(lang='fr')
    assert translator.translate('St. Anastasia') == 'Ste Anastasie'
    assert translator.format_special_commemoration(
        'christmas_second_mass', 'St. Anastasia', 'White'
    ) == (
        'Commémoraison\n'
        'Ste Anastasie est commémorée à la deuxième messe de Noël '
        "(messe de l'aurore).\n"
        'La couleur liturgique de cette messe est le blanc.'
    )


def test_fr_passiontide_friday_and_seven_sorrows_commemoration():
    translator = Translator(lang='fr')
    assert translator.translate(
        'Friday after the First Sunday in Passiontide'
    ) == 'Vendredi après le premier dimanche de la Passion'
    assert translator.format_special_commemoration(
        'passiontide_friday', 'The Seven Sorrows', 'Violet'
    ) == (
        'Commémoraison\n'
        'À la messe du vendredi après le premier dimanche de la Passion, '
        'les sept Douleurs de la B.V.M. sont commémorées.\n'
        'La couleur liturgique de cette messe est le violet.'
    )
    assert translator.format_unobserved_special_commemoration(
        'passiontide_friday', 'The Seven Sorrows', 'St. Joseph', 1
    ) == (
        'Commémoraison\n'
        'Cette année, la fête de St Joseph de Ire classe a préséance ; '
        'les sept Douleurs de la B.V.M. ne sont donc pas commémorées à la '
        'messe.'
    )

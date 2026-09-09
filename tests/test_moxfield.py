from api.moxfield import parse_decklist


def test_parse_decklist_quantity_with_x():
    text = "2x Lightning Bolt"
    assert parse_decklist(text) == [("Lightning Bolt", 2)]


def test_parse_decklist_quantity_without_x():
    text = "4 Brainstorm"
    assert parse_decklist(text) == [("Brainstorm", 4)]


def test_parse_decklist_quantity_omitted():
    text = "Black Lotus"
    assert parse_decklist(text) == [("Black Lotus", 1)]


def test_parse_decklist_strips_moxfield_link():
    text = "1 [Ancient Tomb](https://moxfield.com/cards/ancient-tomb)"
    assert parse_decklist(text) == [("Ancient Tomb", 1)]


def test_parse_decklist_strips_link_without_quantity():
    text = "[Sol Ring](https://moxfield.com/cards/sol-ring)"
    assert parse_decklist(text) == [("Sol Ring", 1)]


def test_parse_decklist_ignores_comments_and_blank_lines():
    text = "\n".join(
        [
            "// Creatures",
            "",
            "# Note personale",
            "1 Solitude",
            "",
        ]
    )
    assert parse_decklist(text) == [("Solitude", 1)]


def test_parse_decklist_multiple_lines():
    text = "\n".join(
        [
            "1x Ragavan, Nimble Pilferer",
            "// Spells",
            "4 Lightning Bolt",
            "Ancient Tomb",
        ]
    )
    assert parse_decklist(text) == [
        ("Ragavan, Nimble Pilferer", 1),
        ("Lightning Bolt", 4),
        ("Ancient Tomb", 1),
    ]

import pytest

from app.lenses.definitions import FORMAT_INSTRUCTION, LENSES, get_all_lenses, get_lens


def test_all_20_lenses_defined():
    assert len(LENSES) == 20


def test_lens_indices_sequential():
    for i, lens in enumerate(LENSES):
        assert lens["index"] == i


def test_all_lenses_have_required_fields():
    required = {"index", "name", "emoji", "color", "bg", "system_prompt"}
    for lens in LENSES:
        assert required.issubset(lens.keys()), f"Missing fields in {lens['name']}"


def test_all_system_prompts_end_with_format_instruction():
    for lens in LENSES:
        assert lens["system_prompt"].endswith(FORMAT_INSTRUCTION), (
            f"{lens['name']} system prompt doesn't end with format instruction"
        )


def test_get_lens_valid():
    lens = get_lens(0)
    assert lens["name"] == "The Comedian"
    lens = get_lens(19)
    assert lens["name"] == "Your Dog"


def test_get_lens_invalid():
    with pytest.raises(ValueError):
        get_lens(-1)
    with pytest.raises(ValueError):
        get_lens(40)


def test_get_lens_delegates_to_voice_packs():
    lens = get_lens(20)
    assert lens["name"] == "Dale Carnegie"
    lens = get_lens(39)
    assert lens["name"] == "Frida Kahlo"


def test_get_all_lenses():
    all_lenses = get_all_lenses()
    assert len(all_lenses) == 20


def test_lens_names_match_spec():
    expected_names = [
        "The Comedian", "The Stoic", "The Nihilist", "The Optimist",
        "The Pessimist", "Your Best Friend", "The Poet", "A Five-Year-Old",
        "The CEO", "The Therapist", "Your Grandma", "The Alien",
        "The Historian", "The Philosopher", "Future You", "Drill Sergeant",
        "The Monk", "The Scientist", "Conspiracy Theorist", "Your Dog",
    ]
    for lens, name in zip(LENSES, expected_names):
        assert lens["name"] == name


def test_lens_colors_match_spec():
    expected_colors = [
        "#ff6b9d", "#c9a84c", "#8a8690", "#3ecf8e", "#ff4757",
        "#4a7cff", "#9b6dff", "#f0c832", "#f0ece4", "#00d4aa",
        "#e8653a", "#4affb4", "#d4a843", "#b08aff", "#6e9fff",
        "#c8c0b4", "#40dfb0", "#5a8cff", "#e8b830", "#f0a070",
    ]
    for lens, color in zip(LENSES, expected_colors):
        assert lens["color"] == color, f"{lens['name']} color mismatch"

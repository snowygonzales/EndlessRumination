import pytest

from app.lenses.definitions import FORMAT_INSTRUCTION
from app.lenses.voice_packs import (
    VOICE_PACKS,
    get_all_packs,
    get_pack_for_index,
    get_voice,
    is_pack_index,
)


def test_four_packs_defined():
    assert len(VOICE_PACKS) == 4


def test_each_pack_has_five_voices():
    for pack in VOICE_PACKS:
        assert len(pack["voices"]) == 5, f"{pack['name']} has {len(pack['voices'])} voices"


def test_voice_indices_20_to_39():
    all_indices = []
    for pack in VOICE_PACKS:
        for voice in pack["voices"]:
            all_indices.append(voice["index"])
    assert sorted(all_indices) == list(range(20, 40))


def test_all_voices_have_required_fields():
    required = {"index", "name", "years", "emoji", "color", "bg", "desc", "system_prompt"}
    for pack in VOICE_PACKS:
        for voice in pack["voices"]:
            assert required.issubset(voice.keys()), (
                f"Missing fields in {voice['name']}"
            )


def test_all_packs_have_required_fields():
    required = {"pack_id", "name", "subtitle", "icon", "color", "bg", "accent", "product_id", "voices"}
    for pack in VOICE_PACKS:
        assert required.issubset(pack.keys()), f"Missing fields in {pack['name']}"


def test_all_voice_system_prompts_end_with_format_instruction():
    for pack in VOICE_PACKS:
        for voice in pack["voices"]:
            assert voice["system_prompt"].endswith(FORMAT_INSTRUCTION), (
                f"{voice['name']} system prompt doesn't end with format instruction"
            )


def test_get_voice_valid():
    voice = get_voice(20)
    assert voice["name"] == "Dale Carnegie"
    voice = get_voice(39)
    assert voice["name"] == "Frida Kahlo"


def test_get_voice_invalid():
    with pytest.raises(ValueError):
        get_voice(0)
    with pytest.raises(ValueError):
        get_voice(19)
    with pytest.raises(ValueError):
        get_voice(40)


def test_is_pack_index():
    assert not is_pack_index(0)
    assert not is_pack_index(19)
    assert is_pack_index(20)
    assert is_pack_index(39)
    assert not is_pack_index(40)


def test_get_pack_for_index():
    assert get_pack_for_index(20) == "com.endlessrumination.pack.strategists"
    assert get_pack_for_index(24) == "com.endlessrumination.pack.strategists"
    assert get_pack_for_index(25) == "com.endlessrumination.pack.revolutionaries"
    assert get_pack_for_index(30) == "com.endlessrumination.pack.philosophers"
    assert get_pack_for_index(35) == "com.endlessrumination.pack.creators"


def test_get_all_packs():
    packs = get_all_packs()
    assert len(packs) == 4
    names = [p["name"] for p in packs]
    assert "The Strategists" in names
    assert "The Revolutionaries" in names
    assert "The Philosophers" in names
    assert "The Creators" in names


def test_pack_product_ids_unique():
    ids = [p["product_id"] for p in VOICE_PACKS]
    assert len(ids) == len(set(ids))


def test_voice_names_match_packs():
    expected = {
        "strategists": ["Dale Carnegie", "Machiavelli", "Sun Tzu", "Benjamin Franklin", "P.T. Barnum"],
        "revolutionaries": ["Vladimir Lenin", "Oscar Wilde", "Mark Twain", "Sigmund Freud", "Cleopatra"],
        "philosophers": ["Immanuel Kant", "Nietzsche", "Kierkegaard", "Epictetus", "Lao Tzu"],
        "creators": ["Leonardo da Vinci", "Emily Dickinson", "Miyamoto Musashi", "Walt Whitman", "Frida Kahlo"],
    }
    for pack in VOICE_PACKS:
        voice_names = [v["name"] for v in pack["voices"]]
        assert voice_names == expected[pack["pack_id"]], (
            f"{pack['name']} voice names don't match expected"
        )

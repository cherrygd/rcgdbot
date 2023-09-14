import enum

class DifficultyByEmoji(enum.Enum):
    NA = "<:na:1141747387849781260>"
    Auto = "<:auto:1142464075964629002>"
    Easy = "<:easy:1141747285118701598>"
    Normal = "<:normal:1141747304798371851>"
    Hard = "<:hard:1141747319759437834>"
    Harder = "<:harder:1141747334384988201>"
    Insane = "<:insane:1141747349673218138>"
    Demon = "<:demon:1141747367696154645>"

class DifficultyCalculator:
    _difficulty_ranges = {
        range(0, 1): DifficultyByEmoji.NA,
        range(1, 2): DifficultyByEmoji.Auto,
        range(2, 3): DifficultyByEmoji.Easy,
        range(3, 4): DifficultyByEmoji.Normal,
        range(4, 6): DifficultyByEmoji.Hard,
        range(6, 8): DifficultyByEmoji.Harder,
        range(8, 10): DifficultyByEmoji.Insane,
        range(10, 11): DifficultyByEmoji.Demon,
    }

    @staticmethod
    def get_difficulty_by_stars(_stars: int) -> str:
        for _range, emoji in DifficultyCalculator._difficulty_ranges.items():
            if _stars in _range:
                return emoji.value

        raise ValueError(f"Не удалось получить emoji по заданным звёздам: {_stars}")
        
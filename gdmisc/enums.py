import enum

class Emojies(enum.Enum):
    # СТАТУС
    NO  = "<:no:1141747496813609011>"
    YES = "<:yes:1141747509899841637>"
    REP = "<:report:1141769582378496091>"

    # МНОГО ОБЪЕКТОВ
    HO = "<:ho:1141757802138833058>"

    # ЗВЁЗДЫ
    STAR   = "<:starrate:1141747404283056248>"
    STAR2  = "<:staar:1141766298997637190>"
    FEATUR = "<:featured:1141747420808626236>"
    EPIC   = "<:epic:1141747435639668906>"
    CP     = "<:cp:1141823815081545839>"

    # СТАТИСТИКА
    DISLIKE  = "<:dislike:1141747479906373793>"
    LIKE     = "<:like:1141747466639777922>"
    DOWNLOAD = "<:download:1142445126245953576>"

    # ЦВЕТА
    GREEN = "<:green:1120494257820667924>" 
    RED   = "<:red:1120493523821670450>" 



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
        

class RatingByEmoji(enum.Enum):
    FIRST_GOLD = "<:cup1:1201670861950558229>",
    GOLD = "<:cup2:1201670932477775892>",
    SILVER = "<:cup3:1201670966443253760>",
    BRONZE = "<:cup4:1201671032403144734>"

class RatingCalculator:
    _rating_ranges = {
        range(1, 2): RatingByEmoji.FIRST_GOLD,
        range(2, 3): RatingByEmoji.GOLD,
        range(3, 4): RatingByEmoji.SILVER
    }

    @staticmethod
    def get_cup_by_place(_place: int) -> str:
        for _range, cup in RatingCalculator._rating_ranges.items():
            if _place in _range:
                return cup.value[0]

        return RatingByEmoji.BRONZE.value
        
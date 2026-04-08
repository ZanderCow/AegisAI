"""Hardcoded list of harmful keywords for pre-send content moderation."""

HARMFUL_KEYWORDS: list[str] = [
    # Violence
    "kill", "murder", "assassinate", "stab", "shoot", "bomb", "explode",
    "massacre", "slaughter", "torture", "behead", "strangle", "suffocate",
    "execute", "genocide", "terrorism", "terrorist", "attack plan",
    # Weapons
    "how to make a bomb", "build a weapon", "make a gun", "illegal weapon",
    "silencer", "pipe bomb", "molotov", "landmine", "nerve agent", "sarin",
    # Self-harm
    "how to kill myself", "how to commit suicide", "suicide method",
    "self harm", "cut myself", "end my life", "overdose on",
    # Exploitation
    "child pornography", "child porn", "csam", "lolita", "underage sex",
    "minor sex", "exploit children",
    # Illegal activities
    "how to hack", "ddos attack", "ransomware", "steal credit card",
    "make meth", "make heroin", "synthesize drugs", "drug synthesis",
    "launder money", "money laundering", "human trafficking",
    # Hate
    "ethnic cleansing", "white supremacy", "nazi", "jihad", "infidel kill",
]

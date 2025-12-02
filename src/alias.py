from uuid import UUID
from typing import List, Optional

ADJECTIVES = [
    "Ancient",
    "Blue",
    "Cosmic",
    "Dancing",
    "Electric",
    "Flying",
    "Green",
    "Happy",
    "Iron",
    "Jolly",
    "Kind",
    "Little",
    "Misty",
    "Neon",
    "Orange",
    "Purple",
    "Quiet",
    "Red",
    "Silent",
    "Tiny",
    "Urban",
    "Violet",
    "Wild",
    "Yellow",
    "Zealous",
    "Brave",
    "Calm",
    "Eager",
    "Fancy",
    "Gentle",
    "Heavy",
    "Icy",
    "Lucky",
    "Merry",
    "Noble",
    "Proud",
    "Rapid",
    "Sharp",
    "Tough",
    "Vivid",
]

NOUNS = [
    "Bear",
    "Cat",
    "Dog",
    "Eagle",
    "Fox",
    "Goat",
    "Hawk",
    "Ibex",
    "Jay",
    "Koala",
    "Lion",
    "Mouse",
    "Newt",
    "Owl",
    "Pig",
    "Quail",
    "Rat",
    "Snake",
    "Tiger",
    "Urchin",
    "Viper",
    "Wolf",
    "Yak",
    "Zebra",
    "Apple",
    "Book",
    "Cloud",
    "Desk",
    "Echo",
    "Fire",
    "Gate",
    "Hill",
    "Island",
    "Jewel",
    "Kite",
    "Leaf",
    "Moon",
    "Note",
    "Ocean",
    "Path",
]


def generate_alias(uuid_obj: UUID) -> str:
    """
    Generates a deterministic 'Adjective-Noun' alias from a UUID.
    Uses the first byte for the adjective and the second byte for the noun.
    """
    # Get bytes
    b = uuid_obj.bytes

    # Use first byte for adjective index
    adj_idx = b[0] % len(ADJECTIVES)

    # Use second byte for noun index
    noun_idx = b[1] % len(NOUNS)

    return f"{ADJECTIVES[adj_idx]}-{NOUNS[noun_idx]}"


def resolve_alias(alias: str, candidates: List[UUID]) -> Optional[tuple]:
    """
    Finds the UUID that corresponds to the given alias from a list of candidates.
    Returns a tuple (UUID, version_number) where version_number is None for current
    version,
    or an integer for a specific historical version (e.g., "Misty-Rat-2" -> (uuid, 2)).
    """
    # Normalize alias (case-insensitive)
    target = alias.lower()

    # Check for version suffix (e.g., "Misty-Rat-2")
    version_number = None
    if target[-1].isdigit():
        # Find the last dash before the number
        parts = target.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            target = parts[0]
            version_number = int(parts[1])

    for cand in candidates:
        if generate_alias(cand).lower() == target:
            return (cand, version_number)

    return None

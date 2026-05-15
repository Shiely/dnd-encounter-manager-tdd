# DOMAIN LAYER: stdlib imports only.
from dataclasses import dataclass
from fractions import Fraction

VALID_CR_STRINGS = {
    "0",
    "1/8",
    "1/4",
    "1/2",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
}


@dataclass(frozen=True)
class ChallengeRating:
    value: str  # stored as string e.g. "1/4"

    def __post_init__(self) -> None:
        if self.value not in VALID_CR_STRINGS:
            raise ValueError(f"Invalid CR: {self.value!r}")

    @property
    def decimal(self) -> float:
        return float(Fraction(self.value))

# tests/unit/domain/test_value_objects.py
# DOMAIN LAYER TEST

import pytest
from dnd_encounter.domain.value_objects.challenge_rating import ChallengeRating
from dnd_encounter.domain.value_objects.dice_expression import DiceExpression
from dnd_encounter.domain.value_objects.ability_scores import AbilityScores


def test_challenge_rating_decimal():
    assert ChallengeRating("1/4").decimal == 0.25


def test_challenge_rating_invalid():
    with pytest.raises(ValueError):
        ChallengeRating("invalid")


def test_dice_expression_valid():
    assert DiceExpression("2d6+4").value == "2d6+4"
    assert DiceExpression("10").value == "10"


def test_dice_expression_invalid():
    with pytest.raises(ValueError):
        DiceExpression("bad")


def test_ability_scores_dex_modifier_positive():
    scores = AbilityScores(8, 14, 10, 10, 8, 8)
    assert scores.dex_modifier == 2


def test_ability_scores_dex_modifier_negative():
    scores = AbilityScores(8, 9, 10, 10, 8, 8)
    assert scores.dex_modifier == -1

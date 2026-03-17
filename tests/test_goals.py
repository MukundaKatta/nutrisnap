"""Tests for daily goals and nutrition advisor."""

import pytest

from nutrisnap.goals.advisor import NutritionAdvisor, Priority
from nutrisnap.goals.daily import ActivityLevel, DailyGoals, Sex
from nutrisnap.models import NutritionInfo


class TestDailyGoals:
    def test_default_male(self):
        goals = DailyGoals()
        assert goals.calorie_goal > 2000
        assert goals.protein_goal > 0
        assert goals.fat_goal > 0
        assert goals.carb_goal > 0

    def test_female(self):
        goals = DailyGoals(sex=Sex.FEMALE, weight_kg=60, height_cm=165)
        assert goals.calorie_goal > 1500
        assert goals.calorie_goal < goals.calorie_goal + 1  # sanity

    def test_sedentary_vs_active(self):
        sedentary = DailyGoals(activity_level=ActivityLevel.SEDENTARY)
        active = DailyGoals(activity_level=ActivityLevel.VERY_ACTIVE)
        assert active.calorie_goal > sedentary.calorie_goal

    def test_rda_targets(self):
        goals = DailyGoals()
        targets = goals.get_rda_targets()
        assert targets.vitamin_a == 900.0  # male default
        assert targets.vitamin_c == 90.0
        assert targets.calcium == 1000.0
        assert targets.iron == 8.0  # male

    def test_female_rda(self):
        goals = DailyGoals(sex=Sex.FEMALE, age=25)
        targets = goals.get_rda_targets()
        assert targets.vitamin_a == 700.0
        assert targets.iron == 18.0
        assert targets.fiber_goal == 25.0

    def test_fiber_older_male(self):
        goals = DailyGoals(sex=Sex.MALE, age=55)
        assert goals.fiber_goal == 30.0

    def test_summary_keys(self):
        goals = DailyGoals()
        s = goals.summary()
        assert "calories" in s
        assert "protein_g" in s
        assert "fat_g" in s


class TestNutritionAdvisor:
    def test_deficit_detected(self):
        advisor = NutritionAdvisor()
        # Very low intake
        intake = NutritionInfo(
            calories=500, protein=10, carbs=50, fat=10, fiber=3,
            vitamin_c=5, calcium=100, iron=1,
        )
        advice = advisor.analyse(intake)
        assert len(advice) > 0
        nutrients = {a.nutrient for a in advice}
        assert "protein" in nutrients
        assert "fiber" in nutrients

    def test_good_intake_fewer_warnings(self):
        advisor = NutritionAdvisor()
        targets = advisor.goals.get_rda_targets()
        # Meet 90% of all targets
        intake = targets.scale(0.9)
        advice = advisor.analyse(intake)
        high_priority = [a for a in advice if a.priority == Priority.HIGH]
        assert len(high_priority) == 0

    def test_suggest_foods(self):
        advisor = NutritionAdvisor()
        suggestions = advisor.suggest_foods("protein", top_k=5)
        assert len(suggestions) == 5
        # Top protein foods should have high values
        assert all(val > 10 for _, val in suggestions)

    def test_meal_suggestions(self):
        advisor = NutritionAdvisor()
        intake = NutritionInfo(
            calories=500, protein=10, carbs=50, fat=10, fiber=3
        )
        suggestions = advisor.get_meal_suggestions(intake)
        assert len(suggestions) > 0

    def test_excess_sodium_warning(self):
        advisor = NutritionAdvisor()
        intake = NutritionInfo(
            calories=2000, protein=60, carbs=250, fat=70, fiber=30,
            sodium=5000,  # well above 2300 limit
        )
        advice = advisor.analyse(intake)
        sodium_advice = [a for a in advice if a.nutrient == "sodium"]
        assert len(sodium_advice) == 1
        assert sodium_advice[0].priority == Priority.HIGH

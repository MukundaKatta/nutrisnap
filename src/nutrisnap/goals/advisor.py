"""Nutrition advisor that suggests dietary improvements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from nutrisnap.database.usda import USDADatabase
from nutrisnap.goals.daily import DailyGoals
from nutrisnap.models import NutritionInfo


class Priority(str, Enum):
    """Advice priority level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Advice:
    """A single dietary recommendation."""

    message: str
    priority: Priority
    nutrient: str
    deficit_pct: float  # how far below/above target, as a percentage


class NutritionAdvisor:
    """Analyses daily intake against goals and suggests improvements.

    Identifies nutrient deficits and excesses, then recommends specific
    foods from the USDA database to address shortfalls.
    """

    # Thresholds for triggering advice (percentage of RDA)
    _DEFICIT_HIGH = 0.50    # less than 50% of target -> high priority
    _DEFICIT_MEDIUM = 0.75  # less than 75% of target -> medium priority
    _EXCESS_THRESHOLD = 1.5  # more than 150% of target -> warning

    def __init__(
        self,
        goals: DailyGoals | None = None,
        db: USDADatabase | None = None,
    ) -> None:
        self.goals = goals or DailyGoals()
        self.db = db or USDADatabase()
        self._targets = self.goals.get_rda_targets()

    def analyse(self, intake: NutritionInfo) -> list[Advice]:
        """Analyse daily intake and generate advice.

        Args:
            intake: Actual nutrition consumed so far today.

        Returns:
            List of Advice objects sorted by priority (high first).
        """
        advice_list: list[Advice] = []
        checks = [
            ("calories", intake.calories, self._targets.calories),
            ("protein", intake.protein, self._targets.protein),
            ("carbs", intake.carbs, self._targets.carbs),
            ("fat", intake.fat, self._targets.fat),
            ("fiber", intake.fiber, self._targets.fiber),
            ("vitamin_a", intake.vitamin_a, self._targets.vitamin_a),
            ("vitamin_c", intake.vitamin_c, self._targets.vitamin_c),
            ("vitamin_d", intake.vitamin_d, self._targets.vitamin_d),
            ("calcium", intake.calcium, self._targets.calcium),
            ("iron", intake.iron, self._targets.iron),
            ("potassium", intake.potassium, self._targets.potassium),
        ]

        for nutrient, actual, target in checks:
            if target <= 0:
                continue
            ratio = actual / target
            deficit_pct = round((1 - ratio) * 100, 1)

            if ratio < self._DEFICIT_HIGH:
                advice_list.append(Advice(
                    message=self._deficit_message(nutrient, deficit_pct),
                    priority=Priority.HIGH,
                    nutrient=nutrient,
                    deficit_pct=deficit_pct,
                ))
            elif ratio < self._DEFICIT_MEDIUM:
                advice_list.append(Advice(
                    message=self._deficit_message(nutrient, deficit_pct),
                    priority=Priority.MEDIUM,
                    nutrient=nutrient,
                    deficit_pct=deficit_pct,
                ))

        # Check for excess sodium
        if self._targets.sodium > 0:
            sodium_ratio = intake.sodium / self._targets.sodium
            if sodium_ratio > self._EXCESS_THRESHOLD:
                excess_pct = round((sodium_ratio - 1) * 100, 1)
                advice_list.append(Advice(
                    message=(
                        f"Sodium intake is {excess_pct}% above the recommended limit. "
                        "Consider reducing processed foods and added salt."
                    ),
                    priority=Priority.HIGH,
                    nutrient="sodium",
                    deficit_pct=-excess_pct,
                ))

        # Sort: HIGH first, then MEDIUM, then LOW
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        advice_list.sort(key=lambda a: priority_order[a.priority])
        return advice_list

    def suggest_foods(self, nutrient: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Suggest foods rich in a specific nutrient.

        Args:
            nutrient: Nutrient name (e.g. "protein", "vitamin_c", "iron").
            top_k: Number of suggestions.

        Returns:
            List of (food_name, nutrient_value_per_100g) tuples, highest first.
        """
        scored: list[tuple[str, float]] = []
        for food_name in self.db.all_foods():
            info = self.db.lookup(food_name)
            if info is None:
                continue
            value = getattr(info, nutrient, None)
            if value is not None and value > 0:
                scored.append((food_name, value))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_meal_suggestions(self, intake: NutritionInfo) -> list[str]:
        """Suggest specific meal ideas to fill nutritional gaps.

        Args:
            intake: Current day's nutrition totals.

        Returns:
            List of human-readable meal suggestions.
        """
        advice = self.analyse(intake)
        suggestions: list[str] = []

        deficient_nutrients = [a.nutrient for a in advice if a.deficit_pct > 25]

        if "protein" in deficient_nutrients:
            suggestions.append(
                "Add a protein-rich food: grilled chicken breast, salmon, "
                "Greek yogurt, lentils, or eggs."
            )
        if "fiber" in deficient_nutrients:
            suggestions.append(
                "Boost fiber with: oats, chia seeds, black beans, broccoli, "
                "or raspberries."
            )
        if "vitamin_c" in deficient_nutrients:
            suggestions.append(
                "Increase vitamin C with: bell peppers, kiwi, strawberries, "
                "oranges, or broccoli."
            )
        if "vitamin_a" in deficient_nutrients:
            suggestions.append(
                "Boost vitamin A with: sweet potato, carrots, spinach, kale, "
                "or cantaloupe."
            )
        if "calcium" in deficient_nutrients:
            suggestions.append(
                "Add calcium-rich foods: Greek yogurt, cheese, sardines, "
                "tofu, or kale."
            )
        if "iron" in deficient_nutrients:
            suggestions.append(
                "Increase iron intake with: spinach, lentils, beef, "
                "pumpkin seeds, or fortified cereals."
            )
        if "potassium" in deficient_nutrients:
            suggestions.append(
                "Boost potassium with: banana, avocado, sweet potato, "
                "spinach, or salmon."
            )

        if not suggestions:
            suggestions.append(
                "Your nutrition looks well-balanced! Keep up the good work."
            )

        return suggestions

    @staticmethod
    def _deficit_message(nutrient: str, deficit_pct: float) -> str:
        """Generate a human-readable deficit message."""
        name = nutrient.replace("_", " ").title()
        return (
            f"{name} intake is {deficit_pct}% below your daily target. "
            f"Consider adding foods rich in {nutrient.replace('_', ' ')}."
        )

"""Daily nutritional goals based on RDA guidelines."""

from __future__ import annotations

from enum import Enum

from nutrisnap.models import NutritionInfo


class ActivityLevel(str, Enum):
    """Physical activity level categories."""

    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class Sex(str, Enum):
    """Biological sex for RDA calculation."""

    MALE = "male"
    FEMALE = "female"


# Activity level multipliers for BMR (Mifflin-St Jeor)
_ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}


class DailyGoals:
    """Calculates and stores daily Recommended Dietary Allowance targets.

    Uses the Mifflin-St Jeor equation for calorie estimation and USDA/NIH
    Recommended Dietary Allowances for micronutrients.
    """

    def __init__(
        self,
        age: int = 30,
        sex: Sex = Sex.MALE,
        weight_kg: float = 70.0,
        height_cm: float = 175.0,
        activity_level: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
    ) -> None:
        self.age = age
        self.sex = sex
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.activity_level = activity_level

    @property
    def bmr(self) -> float:
        """Basal Metabolic Rate via Mifflin-St Jeor equation (kcal/day)."""
        if self.sex == Sex.MALE:
            return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5
        return 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161

    @property
    def tdee(self) -> float:
        """Total Daily Energy Expenditure (kcal/day)."""
        return round(self.bmr * _ACTIVITY_MULTIPLIERS[self.activity_level], 0)

    @property
    def calorie_goal(self) -> float:
        """Daily calorie target."""
        return self.tdee

    @property
    def protein_goal(self) -> float:
        """Daily protein target in grams (0.8 g/kg body weight RDA)."""
        return round(self.weight_kg * 0.8, 1)

    @property
    def fat_goal(self) -> float:
        """Daily fat target in grams (25-35% of calories; using 30%)."""
        return round(self.tdee * 0.30 / 9, 1)

    @property
    def carb_goal(self) -> float:
        """Daily carb target in grams (remaining calories after protein+fat)."""
        protein_cal = self.protein_goal * 4
        fat_cal = self.fat_goal * 9
        remaining = self.tdee - protein_cal - fat_cal
        return round(max(remaining, 0) / 4, 1)

    @property
    def fiber_goal(self) -> float:
        """Daily fiber target in grams (RDA)."""
        if self.sex == Sex.MALE:
            return 38.0 if self.age <= 50 else 30.0
        return 25.0 if self.age <= 50 else 21.0

    def get_rda_targets(self) -> NutritionInfo:
        """Return full RDA targets as a NutritionInfo object.

        Vitamin and mineral targets are based on NIH RDA for adults.
        """
        is_male = self.sex == Sex.MALE
        return NutritionInfo(
            calories=self.calorie_goal,
            protein=self.protein_goal,
            carbs=self.carb_goal,
            fat=self.fat_goal,
            fiber=self.fiber_goal,
            vitamin_a=900.0 if is_male else 700.0,       # mcg RAE
            vitamin_c=90.0 if is_male else 75.0,          # mg
            vitamin_d=15.0 if self.age < 70 else 20.0,    # mcg
            vitamin_e=15.0,                                 # mg
            vitamin_k=120.0 if is_male else 90.0,          # mcg
            vitamin_b6=1.3 if self.age <= 50 else 1.7,     # mg
            vitamin_b12=2.4,                                # mcg
            calcium=1000.0 if self.age <= 70 else 1200.0,  # mg
            iron=8.0 if is_male else 18.0,                  # mg (pre-menopause)
            potassium=3400.0 if is_male else 2600.0,        # mg
            sodium=2300.0,                                   # mg (upper limit)
        )

    def summary(self) -> dict[str, float]:
        """Return a simplified summary of daily targets."""
        return {
            "calories": self.calorie_goal,
            "protein_g": self.protein_goal,
            "carbs_g": self.carb_goal,
            "fat_g": self.fat_goal,
            "fiber_g": self.fiber_goal,
        }

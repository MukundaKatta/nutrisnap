"""Meal tracking and daily intake management."""

from __future__ import annotations

from datetime import date

from nutrisnap.models import DailyLog, Food, Meal, MealType, NutritionInfo


class MealTracker:
    """Tracks daily food intake and compares against nutritional goals.

    Maintains an in-memory log of meals organized by date, supporting
    adding meals, querying history, and comparing totals against daily targets.
    """

    def __init__(self) -> None:
        self._logs: dict[date, DailyLog] = {}

    def _get_or_create_log(self, log_date: date | None = None) -> DailyLog:
        """Get existing log or create a new one for the given date."""
        d = log_date or date.today()
        if d not in self._logs:
            self._logs[d] = DailyLog(log_date=d)
        return self._logs[d]

    def add_meal(self, meal: Meal, log_date: date | None = None) -> DailyLog:
        """Record a meal to the daily log.

        Args:
            meal: The Meal to record.
            log_date: Date to log under (defaults to today).

        Returns:
            The updated DailyLog.
        """
        log = self._get_or_create_log(log_date)
        log.add_meal(meal)
        return log

    def log_food(
        self,
        foods: list[Food],
        meal_type: MealType = MealType.SNACK,
        image_path: str | None = None,
        log_date: date | None = None,
    ) -> Meal:
        """Convenience method to create a Meal from foods and log it.

        Args:
            foods: List of detected Food items.
            meal_type: Type of meal.
            image_path: Optional path to the source image.
            log_date: Date to log under.

        Returns:
            The created Meal object.
        """
        meal = Meal(meal_type=meal_type, foods=foods, image_path=image_path)
        self.add_meal(meal, log_date)
        return meal

    def get_daily_log(self, log_date: date | None = None) -> DailyLog:
        """Retrieve the log for a specific date.

        Args:
            log_date: Date to look up (defaults to today).

        Returns:
            DailyLog for the date (empty log if no data).
        """
        return self._get_or_create_log(log_date)

    def get_daily_totals(self, log_date: date | None = None) -> NutritionInfo:
        """Get aggregated nutrition totals for a day.

        Args:
            log_date: Date to total (defaults to today).

        Returns:
            Combined NutritionInfo for the day.
        """
        log = self._get_or_create_log(log_date)
        return log.total_nutrition

    def get_remaining(
        self, goals: NutritionInfo, log_date: date | None = None
    ) -> dict[str, float]:
        """Calculate remaining nutrients to reach daily goals.

        Args:
            goals: Target NutritionInfo (daily goals).
            log_date: Date to check.

        Returns:
            Dictionary of nutrient names to remaining amounts.
            Negative values mean the goal was exceeded.
        """
        totals = self.get_daily_totals(log_date)
        return {
            "calories": round(goals.calories - totals.calories, 1),
            "protein": round(goals.protein - totals.protein, 1),
            "carbs": round(goals.carbs - totals.carbs, 1),
            "fat": round(goals.fat - totals.fat, 1),
            "fiber": round(goals.fiber - totals.fiber, 1),
            "vitamin_a": round(goals.vitamin_a - totals.vitamin_a, 1),
            "vitamin_c": round(goals.vitamin_c - totals.vitamin_c, 1),
            "calcium": round(goals.calcium - totals.calcium, 1),
            "iron": round(goals.iron - totals.iron, 1),
            "potassium": round(goals.potassium - totals.potassium, 1),
        }

    def get_history(self, days: int = 7) -> list[DailyLog]:
        """Get recent daily logs sorted by date descending.

        Args:
            days: Number of days to look back.

        Returns:
            List of DailyLog objects.
        """
        today = date.today()
        logs = []
        for d, log in sorted(self._logs.items(), reverse=True):
            if (today - d).days <= days:
                logs.append(log)
        return logs

    @property
    def total_meals_logged(self) -> int:
        """Total number of meals tracked across all days."""
        return sum(log.meal_count for log in self._logs.values())

    @property
    def total_days_tracked(self) -> int:
        """Number of unique days with logged meals."""
        return len(self._logs)

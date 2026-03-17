"""Pydantic models for NutriSnap."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MealType(str, Enum):
    """Type of meal."""

    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class NutritionInfo(BaseModel):
    """Nutritional information per 100g serving."""

    calories: float = Field(ge=0, description="Energy in kcal")
    protein: float = Field(ge=0, description="Protein in grams")
    carbs: float = Field(ge=0, description="Carbohydrates in grams")
    fat: float = Field(ge=0, description="Total fat in grams")
    fiber: float = Field(ge=0, description="Dietary fiber in grams")
    vitamin_a: float = Field(ge=0, default=0.0, description="Vitamin A in mcg RAE")
    vitamin_c: float = Field(ge=0, default=0.0, description="Vitamin C in mg")
    vitamin_d: float = Field(ge=0, default=0.0, description="Vitamin D in mcg")
    vitamin_e: float = Field(ge=0, default=0.0, description="Vitamin E in mg")
    vitamin_k: float = Field(ge=0, default=0.0, description="Vitamin K in mcg")
    vitamin_b6: float = Field(ge=0, default=0.0, description="Vitamin B6 in mg")
    vitamin_b12: float = Field(ge=0, default=0.0, description="Vitamin B12 in mcg")
    calcium: float = Field(ge=0, default=0.0, description="Calcium in mg")
    iron: float = Field(ge=0, default=0.0, description="Iron in mg")
    potassium: float = Field(ge=0, default=0.0, description="Potassium in mg")
    sodium: float = Field(ge=0, default=0.0, description="Sodium in mg")

    def scale(self, factor: float) -> NutritionInfo:
        """Scale all nutrition values by a factor."""
        return NutritionInfo(
            calories=round(self.calories * factor, 1),
            protein=round(self.protein * factor, 1),
            carbs=round(self.carbs * factor, 1),
            fat=round(self.fat * factor, 1),
            fiber=round(self.fiber * factor, 1),
            vitamin_a=round(self.vitamin_a * factor, 1),
            vitamin_c=round(self.vitamin_c * factor, 1),
            vitamin_d=round(self.vitamin_d * factor, 1),
            vitamin_e=round(self.vitamin_e * factor, 1),
            vitamin_k=round(self.vitamin_k * factor, 1),
            vitamin_b6=round(self.vitamin_b6 * factor, 1),
            vitamin_b12=round(self.vitamin_b12 * factor, 1),
            calcium=round(self.calcium * factor, 1),
            iron=round(self.iron * factor, 1),
            potassium=round(self.potassium * factor, 1),
            sodium=round(self.sodium * factor, 1),
        )

    def __add__(self, other: NutritionInfo) -> NutritionInfo:
        """Add two NutritionInfo objects together."""
        return NutritionInfo(
            calories=round(self.calories + other.calories, 1),
            protein=round(self.protein + other.protein, 1),
            carbs=round(self.carbs + other.carbs, 1),
            fat=round(self.fat + other.fat, 1),
            fiber=round(self.fiber + other.fiber, 1),
            vitamin_a=round(self.vitamin_a + other.vitamin_a, 1),
            vitamin_c=round(self.vitamin_c + other.vitamin_c, 1),
            vitamin_d=round(self.vitamin_d + other.vitamin_d, 1),
            vitamin_e=round(self.vitamin_e + other.vitamin_e, 1),
            vitamin_k=round(self.vitamin_k + other.vitamin_k, 1),
            vitamin_b6=round(self.vitamin_b6 + other.vitamin_b6, 1),
            vitamin_b12=round(self.vitamin_b12 + other.vitamin_b12, 1),
            calcium=round(self.calcium + other.calcium, 1),
            iron=round(self.iron + other.iron, 1),
            potassium=round(self.potassium + other.potassium, 1),
            sodium=round(self.sodium + other.sodium, 1),
        )

    @classmethod
    def zero(cls) -> NutritionInfo:
        """Return a zeroed-out NutritionInfo."""
        return cls(calories=0, protein=0, carbs=0, fat=0, fiber=0)


class Food(BaseModel):
    """A detected food item with nutrition data."""

    name: str = Field(description="Food name")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")
    portion_grams: float = Field(gt=0, description="Estimated portion in grams")
    nutrition_per_100g: NutritionInfo
    nutrition_actual: NutritionInfo = Field(
        description="Nutrition scaled to actual portion"
    )
    category: str = Field(default="general", description="Food category")


class Meal(BaseModel):
    """A meal consisting of one or more food items."""

    meal_type: MealType
    timestamp: datetime = Field(default_factory=datetime.now)
    foods: list[Food] = Field(default_factory=list)
    image_path: Optional[str] = None

    @property
    def total_nutrition(self) -> NutritionInfo:
        """Sum nutrition across all foods in the meal."""
        total = NutritionInfo.zero()
        for food in self.foods:
            total = total + food.nutrition_actual
        return total

    @property
    def total_calories(self) -> float:
        """Total calories for the meal."""
        return self.total_nutrition.calories


class DailyLog(BaseModel):
    """A full day of tracked meals."""

    log_date: date = Field(default_factory=date.today)
    meals: list[Meal] = Field(default_factory=list)

    @property
    def total_nutrition(self) -> NutritionInfo:
        """Sum nutrition across all meals."""
        total = NutritionInfo.zero()
        for meal in self.meals:
            total = total + meal.total_nutrition
        return total

    @property
    def total_calories(self) -> float:
        """Total calories for the day."""
        return self.total_nutrition.calories

    @property
    def meal_count(self) -> int:
        """Number of meals logged."""
        return len(self.meals)

    def add_meal(self, meal: Meal) -> None:
        """Add a meal to the daily log."""
        self.meals.append(meal)

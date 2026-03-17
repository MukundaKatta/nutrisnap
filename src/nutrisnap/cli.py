"""NutriSnap CLI - Food Photo Nutrition Analyzer."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from nutrisnap.analyzer.food_detector import FoodDetector
from nutrisnap.analyzer.nutrition import NutritionCalculator
from nutrisnap.analyzer.portion import PortionEstimator
from nutrisnap.database.meals import MealTracker
from nutrisnap.database.usda import USDADatabase
from nutrisnap.goals.advisor import NutritionAdvisor
from nutrisnap.goals.daily import ActivityLevel, DailyGoals, Sex
from nutrisnap.models import MealType
from nutrisnap.report import NutritionReport

console = Console()
db = USDADatabase()
tracker = MealTracker()
report = NutritionReport(console)


@click.group()
@click.version_option(version="0.1.0", prog_name="nutrisnap")
def cli() -> None:
    """NutriSnap - Food Photo Nutrition Analyzer.

    Analyse food photos to get detailed nutritional information,
    track daily intake, and receive personalised dietary advice.
    """


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option("--top-k", default=5, help="Max number of food predictions.")
@click.option("--threshold", default=0.1, help="Minimum confidence threshold.")
@click.option(
    "--meal-type", "-m",
    type=click.Choice(["breakfast", "lunch", "dinner", "snack"]),
    default="snack",
    help="Type of meal.",
)
@click.option("--model", default=None, help="Path to trained model checkpoint.")
def analyse(
    image_path: str,
    top_k: int,
    threshold: float,
    meal_type: str,
    model: str | None,
) -> None:
    """Analyse a food photo and display nutrition information."""
    console.print(f"\n[bold cyan]Analysing:[/] {image_path}\n")

    detector = FoodDetector(model_path=model)
    calculator = NutritionCalculator(db=db)

    detections = detector.detect(image_path, top_k=top_k, confidence_threshold=threshold)
    if not detections:
        console.print("[yellow]No food items detected in the image.[/]")
        return

    foods = calculator.calculate_multiple(detections)
    if not foods:
        console.print("[yellow]Detected items not found in nutrition database.[/]")
        return

    report.print_food_analysis(foods)

    # Log the meal
    mt = MealType(meal_type)
    tracker.log_food(foods, meal_type=mt, image_path=image_path)
    console.print(f"[green]Logged as {meal_type}.[/]\n")


@cli.command()
@click.argument("food_name")
@click.option("--portion", "-p", default=None, type=float, help="Portion in grams.")
def lookup(food_name: str, portion: float | None) -> None:
    """Look up nutrition info for a specific food."""
    calculator = NutritionCalculator(db=db)

    if portion is None:
        estimator = PortionEstimator()
        portion = estimator.get_standard_portion(food_name)

    food = calculator.lookup_food(food_name, portion_grams=portion)
    if food is None:
        console.print(f"[red]Food '{food_name}' not found in database.[/]")
        console.print("[dim]Try searching with: nutrisnap search <query>[/]")
        return

    report.print_food_analysis([food])


@cli.command()
@click.argument("query")
def search(query: str) -> None:
    """Search the food database."""
    results = db.search(query)
    report.print_food_search(results, query)


@cli.command()
@click.option("--age", default=30, help="Age in years.")
@click.option("--sex", type=click.Choice(["male", "female"]), default="male")
@click.option("--weight", default=70.0, help="Weight in kg.")
@click.option("--height", default=175.0, help="Height in cm.")
@click.option(
    "--activity",
    type=click.Choice([
        "sedentary", "lightly_active", "moderately_active",
        "very_active", "extra_active",
    ]),
    default="moderately_active",
    help="Activity level.",
)
def goals(age: int, sex: str, weight: float, height: float, activity: str) -> None:
    """Display personalised daily nutrition goals."""
    daily = DailyGoals(
        age=age,
        sex=Sex(sex),
        weight_kg=weight,
        height_cm=height,
        activity_level=ActivityLevel(activity),
    )
    targets = daily.get_rda_targets()
    console.print("\n[bold magenta]Your Daily Nutrition Goals[/]\n")

    from rich.table import Table

    table = Table(show_header=True, header_style="bold")
    table.add_column("Nutrient")
    table.add_column("Target", justify="right")

    rows = [
        ("Calories", f"{targets.calories:.0f} kcal"),
        ("Protein", f"{targets.protein:.1f} g"),
        ("Carbs", f"{targets.carbs:.1f} g"),
        ("Fat", f"{targets.fat:.1f} g"),
        ("Fiber", f"{targets.fiber:.1f} g"),
        ("Vitamin A", f"{targets.vitamin_a:.0f} mcg"),
        ("Vitamin C", f"{targets.vitamin_c:.0f} mg"),
        ("Vitamin D", f"{targets.vitamin_d:.0f} mcg"),
        ("Calcium", f"{targets.calcium:.0f} mg"),
        ("Iron", f"{targets.iron:.0f} mg"),
        ("Potassium", f"{targets.potassium:.0f} mg"),
        ("Sodium (limit)", f"{targets.sodium:.0f} mg"),
    ]
    for name, val in rows:
        table.add_row(name, val)

    console.print(table)
    console.print(f"\n  TDEE: {daily.tdee:.0f} kcal/day  |  BMR: {daily.bmr:.0f} kcal/day\n")


@cli.command()
def summary() -> None:
    """Show today's nutrition summary."""
    log = tracker.get_daily_log()
    if not log.meals:
        console.print("[dim]No meals logged today. Use 'analyse' or 'lookup' first.[/]")
        return
    goals_obj = DailyGoals()
    report.print_daily_summary(log, goals_obj)


@cli.command()
def advise() -> None:
    """Get personalised nutrition advice based on today's intake."""
    log = tracker.get_daily_log()
    if not log.meals:
        console.print("[dim]No meals logged today. Log some food first.[/]")
        return

    advisor = NutritionAdvisor(db=db)
    intake = log.total_nutrition
    advice = advisor.analyse(intake)
    report.print_advice(advice)

    suggestions = advisor.get_meal_suggestions(intake)
    report.print_meal_suggestions(suggestions)


@cli.command()
def foods() -> None:
    """List all available food categories and counts."""
    console.print(f"\n[bold cyan]USDA Food Database[/] - {db.food_count} foods\n")

    from rich.table import Table

    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Count", justify="right")

    for cat in db.list_categories():
        items = db.foods_in_category(cat)
        table.add_row(cat.replace("_", " ").title(), str(len(items)))

    console.print(table)


if __name__ == "__main__":
    cli()

"""Rich-formatted nutrition reports for the terminal."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from nutrisnap.goals.advisor import Advice, NutritionAdvisor, Priority
from nutrisnap.goals.daily import DailyGoals
from nutrisnap.models import DailyLog, Food, Meal, NutritionInfo


class NutritionReport:
    """Generates rich terminal reports for food analysis results."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def print_food_analysis(self, foods: list[Food]) -> None:
        """Print a detailed analysis table for detected foods."""
        table = Table(
            title="Food Analysis Results",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Food", style="bold")
        table.add_column("Confidence", justify="right")
        table.add_column("Portion (g)", justify="right")
        table.add_column("Calories", justify="right", style="yellow")
        table.add_column("Protein (g)", justify="right", style="green")
        table.add_column("Carbs (g)", justify="right", style="blue")
        table.add_column("Fat (g)", justify="right", style="red")
        table.add_column("Fiber (g)", justify="right")

        for food in foods:
            n = food.nutrition_actual
            table.add_row(
                food.name.replace("_", " ").title(),
                f"{food.confidence:.0%}",
                f"{food.portion_grams:.0f}",
                f"{n.calories:.0f}",
                f"{n.protein:.1f}",
                f"{n.carbs:.1f}",
                f"{n.fat:.1f}",
                f"{n.fiber:.1f}",
            )

        # Totals row
        total = NutritionInfo.zero()
        for food in foods:
            total = total + food.nutrition_actual
        table.add_section()
        table.add_row(
            "TOTAL", "", "",
            f"[bold yellow]{total.calories:.0f}[/]",
            f"[bold green]{total.protein:.1f}[/]",
            f"[bold blue]{total.carbs:.1f}[/]",
            f"[bold red]{total.fat:.1f}[/]",
            f"[bold]{total.fiber:.1f}[/]",
        )

        self.console.print(table)

    def print_daily_summary(
        self,
        log: DailyLog,
        goals: DailyGoals | None = None,
    ) -> None:
        """Print a daily nutrition summary with optional goal comparison."""
        total = log.total_nutrition
        targets = goals.get_rda_targets() if goals else None

        table = Table(
            title=f"Daily Summary - {log.log_date}",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Nutrient", style="bold")
        table.add_column("Intake", justify="right")
        if targets:
            table.add_column("Goal", justify="right", style="dim")
            table.add_column("Progress", justify="right")

        rows = [
            ("Calories", total.calories, targets.calories if targets else None, "kcal"),
            ("Protein", total.protein, targets.protein if targets else None, "g"),
            ("Carbs", total.carbs, targets.carbs if targets else None, "g"),
            ("Fat", total.fat, targets.fat if targets else None, "g"),
            ("Fiber", total.fiber, targets.fiber if targets else None, "g"),
            ("Vitamin A", total.vitamin_a, targets.vitamin_a if targets else None, "mcg"),
            ("Vitamin C", total.vitamin_c, targets.vitamin_c if targets else None, "mg"),
            ("Calcium", total.calcium, targets.calcium if targets else None, "mg"),
            ("Iron", total.iron, targets.iron if targets else None, "mg"),
            ("Potassium", total.potassium, targets.potassium if targets else None, "mg"),
            ("Sodium", total.sodium, targets.sodium if targets else None, "mg"),
        ]

        for name, actual, goal, unit in rows:
            intake_str = f"{actual:.1f} {unit}"
            if targets and goal:
                goal_str = f"{goal:.1f} {unit}"
                pct = (actual / goal * 100) if goal > 0 else 0
                if name == "Sodium":
                    color = "green" if pct <= 100 else "red"
                else:
                    color = "green" if pct >= 80 else ("yellow" if pct >= 50 else "red")
                progress_str = f"[{color}]{pct:.0f}%[/]"
                table.add_row(name, intake_str, goal_str, progress_str)
            else:
                table.add_row(name, intake_str)

        self.console.print(table)
        self.console.print(
            f"\n  Meals logged: {log.meal_count}  |  "
            f"Total calories: {total.calories:.0f} kcal\n"
        )

    def print_advice(self, advice_list: list[Advice]) -> None:
        """Print nutrition advice with priority indicators."""
        if not advice_list:
            self.console.print(
                Panel("Your nutrition looks great! No issues detected.",
                      title="Nutrition Advice", border_style="green")
            )
            return

        lines: list[str] = []
        for a in advice_list:
            icon = {
                Priority.HIGH: "[bold red]!!![/]",
                Priority.MEDIUM: "[bold yellow] ! [/]",
                Priority.LOW: "[dim] . [/]",
            }[a.priority]
            lines.append(f"  {icon}  {a.message}")

        panel_text = "\n".join(lines)
        self.console.print(
            Panel(panel_text, title="Nutrition Advice", border_style="yellow")
        )

    def print_meal_suggestions(self, suggestions: list[str]) -> None:
        """Print meal improvement suggestions."""
        text = "\n".join(f"  - {s}" for s in suggestions)
        self.console.print(
            Panel(text, title="Meal Suggestions", border_style="cyan")
        )

    def print_food_search(self, results: list[str], query: str) -> None:
        """Print food search results."""
        if not results:
            self.console.print(f"[dim]No foods found matching '{query}'.[/]")
            return

        table = Table(title=f"Search Results for '{query}'")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Food Name", style="bold")

        for i, name in enumerate(results, 1):
            table.add_row(str(i), name.replace("_", " ").title())

        self.console.print(table)

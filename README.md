# NutriSnap

Food Photo Nutrition Analyzer - snap a photo of your meal and get instant, detailed nutritional breakdowns powered by deep learning and the USDA nutrition database.

## Features

- **CNN Food Detection**: 4-layer convolutional neural network that identifies 200+ food items from photos
- **USDA Nutrition Database**: Real nutrition data (calories, protein, carbs, fat, fiber, vitamins, minerals) for 200+ foods sourced from USDA FoodData Central
- **Portion Estimation**: Estimates serving sizes based on food type and image context using USDA standard reference portions
- **Daily Goal Tracking**: Personalised RDA targets calculated via the Mifflin-St Jeor equation, adjusted for age, sex, weight, height, and activity level
- **Nutrition Advisor**: Analyses intake gaps and suggests specific foods to improve your diet
- **Meal Logging**: Track breakfast, lunch, dinner, and snacks with running daily totals
- **Rich Terminal Reports**: Beautiful tables, progress bars, and colour-coded feedback via Rich

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Analyse a food photo
nutrisnap analyse photo.jpg --meal-type lunch

# Look up nutrition for a specific food
nutrisnap lookup chicken_breast --portion 200

# Search the food database
nutrisnap search "choc"

# View your personalised daily goals
nutrisnap goals --age 30 --sex male --weight 75 --height 180 --activity moderately_active

# See today's nutrition summary
nutrisnap summary

# Get dietary advice
nutrisnap advise

# Browse all food categories
nutrisnap foods
```

## Project Structure

```
nutrisnap/
  src/nutrisnap/
    cli.py                  # Click CLI with analyse/lookup/search/goals/summary/advise commands
    models.py               # Pydantic models: Food, NutritionInfo, Meal, DailyLog
    report.py               # Rich terminal reports and formatted output
    analyzer/
      food_detector.py      # FoodCNN + FoodDetector (4-layer CNN, 224x224 input)
      nutrition.py           # NutritionCalculator combining DB + portions
      portion.py             # PortionEstimator with USDA standard serving sizes
    database/
      usda.py               # USDADatabase with 200+ foods and full micronutrient data
      meals.py              # MealTracker for daily intake logging and goal comparison
    goals/
      daily.py              # DailyGoals with Mifflin-St Jeor TDEE and RDA targets
      advisor.py            # NutritionAdvisor with deficit analysis and food suggestions
  tests/
    test_models.py
    test_usda.py
    test_portion.py
    test_nutrition.py
    test_goals.py
    test_meals.py
```

## Running Tests

```bash
pytest
pytest --cov=nutrisnap
```

## Tech Stack

- **PyTorch** - CNN food classification model
- **Pydantic** - Data validation and serialisation
- **Click** - CLI framework
- **Rich** - Terminal formatting and tables
- **Pillow** - Image loading and preprocessing
- **torchvision** - Image transforms and normalisation

## Author

Mukunda Katta

## License

MIT

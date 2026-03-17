"""Tests for the USDA nutrition database."""

import pytest

from nutrisnap.database.usda import USDADatabase


@pytest.fixture
def db():
    return USDADatabase()


class TestUSDADatabase:
    def test_food_count_over_200(self, db):
        assert db.food_count >= 200

    def test_lookup_known_food(self, db):
        info = db.lookup("chicken_breast")
        assert info is not None
        assert info.calories == 165
        assert info.protein == 31.0
        assert info.fat == 3.6

    def test_lookup_with_spaces(self, db):
        info = db.lookup("chicken breast")
        assert info is not None
        assert info.calories == 165

    def test_lookup_unknown_food(self, db):
        assert db.lookup("unicorn_steak") is None

    def test_search(self, db):
        results = db.search("chicken")
        assert len(results) > 0
        assert all("chicken" in name for name in results)

    def test_search_partial(self, db):
        results = db.search("choc")
        assert "chocolate_dark" in results
        assert "chocolate_milk" in results

    def test_get_category(self, db):
        assert db.get_category("banana") == "fruits"
        assert db.get_category("chicken_breast") == "meat"
        assert db.get_category("salmon") == "seafood"
        assert db.get_category("lentils") == "plant_protein"

    def test_list_categories(self, db):
        categories = db.list_categories()
        assert "fruits" in categories
        assert "vegetables" in categories
        assert "meat" in categories
        assert "dairy" in categories

    def test_foods_in_category(self, db):
        fruits = db.foods_in_category("fruits")
        assert "apple" in fruits
        assert "banana" in fruits
        assert len(fruits) > 10

    def test_all_foods(self, db):
        foods = db.all_foods()
        assert len(foods) >= 200
        assert foods == sorted(foods)  # alphabetical

    def test_nutrition_values_reasonable(self, db):
        """Spot-check several foods for reasonable USDA values."""
        # Banana
        banana = db.lookup("banana")
        assert banana is not None
        assert 85 <= banana.calories <= 95
        assert banana.potassium > 300

        # Salmon
        salmon = db.lookup("salmon")
        assert salmon is not None
        assert salmon.protein > 18
        assert salmon.vitamin_d > 5

        # Spinach
        spinach = db.lookup("spinach")
        assert spinach is not None
        assert spinach.iron > 2
        assert spinach.vitamin_k > 400

    def test_all_nutrition_values_non_negative(self, db):
        """Every value in the database should be >= 0."""
        for food_name in db.all_foods():
            info = db.lookup(food_name)
            assert info is not None
            assert info.calories >= 0
            assert info.protein >= 0
            assert info.carbs >= 0
            assert info.fat >= 0
            assert info.fiber >= 0

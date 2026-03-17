"""Portion size estimation from image context."""

from __future__ import annotations


class PortionEstimator:
    """Estimates serving sizes in grams based on food type and image context.

    Uses a lookup of typical single-serving sizes sourced from USDA standard
    reference portions. In a production system, this would also use spatial
    cues from the image (plate size, utensil references, depth estimation)
    to refine the estimate.
    """

    # Typical single-serving sizes in grams, sourced from USDA standard
    # reference amounts and common dietary guidelines.
    _DEFAULT_PORTIONS: dict[str, float] = {
        # Fruits
        "apple": 182, "banana": 118, "orange": 131, "strawberry": 150,
        "blueberry": 148, "grape": 151, "watermelon": 280, "pineapple": 165,
        "mango": 165, "peach": 150, "pear": 178, "cherry": 140,
        "kiwi": 75, "papaya": 145, "avocado": 150, "cantaloupe": 177,
        "grapefruit": 154, "raspberry": 123, "blackberry": 144,
        "plum": 66, "pomegranate": 174, "lemon": 58,
        "coconut_meat": 80, "fig": 50, "date": 24,

        # Vegetables
        "broccoli": 148, "carrot": 128, "spinach": 85, "tomato": 123,
        "potato": 213, "sweet_potato": 200, "onion": 110, "bell_pepper": 119,
        "cucumber": 301, "lettuce": 72, "corn": 90, "green_beans": 125,
        "peas": 160, "cauliflower": 124, "zucchini": 180, "mushroom": 96,
        "asparagus": 134, "celery": 110, "cabbage": 89, "kale": 67,
        "eggplant": 82, "beet": 136, "artichoke": 120,
        "brussels_sprouts": 88, "radish": 116, "turnip": 122,
        "squash_butternut": 205, "parsnip": 133,

        # Grains
        "white_rice": 186, "brown_rice": 195, "pasta": 140,
        "whole_wheat_bread": 43, "white_bread": 29, "oats": 40,
        "quinoa": 185, "barley": 157, "couscous": 157, "cornbread": 60,
        "tortilla_corn": 26, "tortilla_flour": 45, "granola": 55,
        "bagel": 105,

        # Meat
        "chicken_breast": 172, "chicken_thigh": 116, "turkey_breast": 170,
        "beef_sirloin": 170, "beef_ground_85": 113, "pork_loin": 113,
        "pork_chop": 113, "lamb_loin": 113, "bacon": 28, "ham": 85,
        "sausage_pork": 75, "venison": 113, "bison": 113,
        "steak_ribeye": 227, "pork_belly": 85, "duck_breast": 170,
        "liver_chicken": 113,

        # Seafood
        "salmon": 170, "tuna": 142, "shrimp": 113, "cod": 170,
        "tilapia": 113, "sardine": 92, "trout": 143, "crab": 113,
        "lobster": 145, "scallop": 113, "catfish": 113, "swordfish": 136,

        # Plant protein
        "tofu": 126, "tempeh": 84, "lentils": 198, "chickpeas": 164,
        "black_beans": 172, "kidney_beans": 177, "edamame": 155,
        "peanuts": 28, "almonds": 28, "walnuts": 28, "cashews": 28,
        "sunflower_seeds": 28, "chia_seeds": 28, "flax_seeds": 14,
        "pumpkin_seeds": 28, "pinto_beans": 171, "navy_beans": 182,
        "lima_beans": 170, "soybeans": 180, "pistachio": 28,
        "macadamia": 28, "pecan": 28, "hazelnut": 28,

        # Dairy
        "whole_milk": 244, "skim_milk": 245, "cheddar_cheese": 28,
        "mozzarella": 28, "parmesan": 10, "cottage_cheese": 113,
        "cream_cheese": 28, "greek_yogurt": 170, "yogurt_plain": 170,
        "butter": 14, "sour_cream": 30, "ice_cream_vanilla": 132,
        "swiss_cheese": 28,

        # Eggs
        "egg_whole": 50, "egg_white": 33, "egg_yolk": 17,

        # Oils
        "olive_oil": 14, "coconut_oil": 14, "canola_oil": 14,

        # Beverages
        "orange_juice": 248, "apple_juice": 248, "coffee_black": 237,
        "green_tea": 237, "cola": 355,

        # Prepared foods
        "pizza_cheese": 140, "french_fries": 117, "hamburger": 215,
        "hot_dog": 98, "fried_chicken": 140, "burrito_bean": 217,
        "sushi_roll": 200, "pad_thai": 280, "macaroni_cheese": 200,
        "fried_rice": 200, "mashed_potato": 210, "caesar_salad": 200,
        "taco_beef": 170, "chicken_curry": 250, "beef_stew": 252,
        "chili_con_carne": 253, "lasagna": 250, "spaghetti_meatballs": 248,
        "grilled_cheese": 120, "ramen": 300, "fish_and_chips": 300,
        "chicken_nuggets": 100, "pancake": 77, "waffle": 75,
        "croissant": 57, "donut_glazed": 60, "muffin_blueberry": 113,

        # Sweets & snacks
        "chocolate_dark": 40, "chocolate_milk": 44, "cookie_chocolate_chip": 30,
        "brownie": 56, "cake_chocolate": 80, "apple_pie": 125,
        "cheesecake": 125, "potato_chips": 28, "popcorn_plain": 28,
        "pretzel": 28, "trail_mix": 40, "protein_bar": 60,
        "rice_cake": 9, "energy_bar": 50, "jelly_beans": 40,

        # Condiments
        "ketchup": 17, "mustard": 5, "mayonnaise": 15, "soy_sauce": 16,
        "salsa": 36, "hummus": 30, "guacamole": 30, "peanut_butter": 32,
        "honey": 21, "maple_syrup": 20, "jam": 20, "ranch_dressing": 30,
        "bbq_sauce": 34, "hot_sauce": 6, "teriyaki_sauce": 18,

        # Soups
        "chicken_soup": 245, "tomato_soup": 248, "minestrone": 245,
        "clam_chowder": 248,

        # Breakfast
        "cream_of_wheat": 251, "oatmeal_cooked": 234, "french_toast": 65,
        "cereal_corn_flakes": 30, "cereal_granola": 55,

        # International
        "falafel": 51, "naan": 90, "biryani": 250, "samosa": 100,
        "spring_roll": 64, "dim_sum": 80, "pho": 400, "gyoza": 110,
        "kimchi": 75, "miso_soup": 245, "tzatziki": 30,
        "couscous_moroccan": 200, "risotto": 200, "paella": 250,
        "pierogi": 130, "tikka_masala": 250,

        # Misc
        "granola_bar": 42, "protein_shake": 300, "smoothie_berry": 300,
        "acai_bowl": 300, "overnight_oats": 250, "wrap_chicken": 200,
        "sandwich_turkey": 180,
    }

    _DEFAULT_PORTION: float = 100.0

    def estimate(
        self,
        food_name: str,
        image_scale_factor: float = 1.0,
    ) -> float:
        """Estimate the portion size for a given food.

        Args:
            food_name: Normalised food name matching the USDA database.
            image_scale_factor: Multiplier derived from image context
                (e.g. plate-size heuristic). 1.0 = standard serving.

        Returns:
            Estimated portion in grams.
        """
        key = food_name.lower().replace(" ", "_")
        base = self._DEFAULT_PORTIONS.get(key, self._DEFAULT_PORTION)
        return round(base * image_scale_factor, 1)

    def get_standard_portion(self, food_name: str) -> float:
        """Get the standard reference portion for a food.

        Args:
            food_name: Food name.

        Returns:
            Standard portion in grams.
        """
        key = food_name.lower().replace(" ", "_")
        return self._DEFAULT_PORTIONS.get(key, self._DEFAULT_PORTION)

    @property
    def supported_foods(self) -> list[str]:
        """List all foods with known portion sizes."""
        return sorted(self._DEFAULT_PORTIONS.keys())

"""CNN-based food detection from images."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms


@dataclass
class DetectionResult:
    """A single food detection result."""

    food_name: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None  # x, y, w, h


# The 200+ food classes that the model can identify, matching the USDA database keys.
FOOD_CLASSES: list[str] = [
    "apple", "banana", "orange", "strawberry", "blueberry", "grape",
    "watermelon", "pineapple", "mango", "peach", "pear", "cherry",
    "kiwi", "papaya", "avocado", "cantaloupe", "grapefruit",
    "raspberry", "blackberry", "plum", "pomegranate", "lemon",
    "coconut_meat", "fig", "date",
    "broccoli", "carrot", "spinach", "tomato", "potato", "sweet_potato",
    "onion", "bell_pepper", "cucumber", "lettuce", "corn", "green_beans",
    "peas", "cauliflower", "zucchini", "mushroom", "asparagus", "celery",
    "cabbage", "kale", "eggplant", "beet", "artichoke", "brussels_sprouts",
    "radish", "turnip", "squash_butternut", "parsnip",
    "white_rice", "brown_rice", "pasta", "whole_wheat_bread",
    "white_bread", "oats", "quinoa", "barley", "couscous", "cornbread",
    "tortilla_corn", "tortilla_flour", "granola", "bagel",
    "chicken_breast", "chicken_thigh", "turkey_breast", "beef_sirloin",
    "beef_ground_85", "pork_loin", "pork_chop", "lamb_loin", "bacon",
    "ham", "sausage_pork", "venison", "bison", "steak_ribeye",
    "pork_belly", "duck_breast", "liver_chicken",
    "salmon", "tuna", "shrimp", "cod", "tilapia", "sardine", "trout",
    "crab", "lobster", "scallop", "catfish", "swordfish",
    "tofu", "tempeh", "lentils", "chickpeas", "black_beans",
    "kidney_beans", "edamame", "peanuts", "almonds", "walnuts",
    "cashews", "sunflower_seeds", "chia_seeds", "flax_seeds",
    "pumpkin_seeds", "pinto_beans", "navy_beans", "lima_beans",
    "soybeans", "pistachio", "macadamia", "pecan", "hazelnut",
    "whole_milk", "skim_milk", "cheddar_cheese", "mozzarella",
    "parmesan", "cottage_cheese", "cream_cheese", "greek_yogurt",
    "yogurt_plain", "butter", "sour_cream", "ice_cream_vanilla",
    "swiss_cheese",
    "egg_whole", "egg_white", "egg_yolk",
    "olive_oil", "coconut_oil", "canola_oil",
    "orange_juice", "apple_juice", "coffee_black", "green_tea", "cola",
    "pizza_cheese", "french_fries", "hamburger", "hot_dog",
    "fried_chicken", "burrito_bean", "sushi_roll", "pad_thai",
    "macaroni_cheese", "fried_rice", "mashed_potato", "caesar_salad",
    "taco_beef", "chicken_curry", "beef_stew", "chili_con_carne",
    "lasagna", "spaghetti_meatballs", "grilled_cheese", "ramen",
    "fish_and_chips", "chicken_nuggets", "pancake", "waffle",
    "croissant", "donut_glazed", "muffin_blueberry",
    "chocolate_dark", "chocolate_milk", "cookie_chocolate_chip",
    "brownie", "cake_chocolate", "apple_pie", "cheesecake",
    "potato_chips", "popcorn_plain", "pretzel", "trail_mix",
    "protein_bar", "rice_cake", "energy_bar", "jelly_beans",
    "ketchup", "mustard", "mayonnaise", "soy_sauce", "salsa",
    "hummus", "guacamole", "peanut_butter", "honey", "maple_syrup",
    "jam", "ranch_dressing", "bbq_sauce", "hot_sauce", "teriyaki_sauce",
    "chicken_soup", "tomato_soup", "minestrone", "clam_chowder",
    "cream_of_wheat", "oatmeal_cooked", "french_toast",
    "cereal_corn_flakes", "cereal_granola",
    "falafel", "naan", "biryani", "samosa", "spring_roll", "dim_sum",
    "pho", "gyoza", "kimchi", "miso_soup", "tzatziki",
    "couscous_moroccan", "risotto", "paella", "pierogi", "tikka_masala",
    "granola_bar", "protein_shake", "smoothie_berry", "acai_bowl",
    "overnight_oats", "wrap_chicken", "sandwich_turkey",
]


class FoodCNN(nn.Module):
    """Convolutional Neural Network for food classification.

    Architecture: 4-layer CNN with batch normalisation, dropout, and
    global average pooling, designed for 224x224 RGB food images.
    """

    def __init__(self, num_classes: int = len(FOOD_CLASSES)) -> None:
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 224x224 -> 112x112
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),
            # Block 2: 112x112 -> 56x56
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),
            # Block 3: 56x56 -> 28x28
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),
            # Block 4: 28x28 -> 14x14
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25),
        )
        # Global average pooling + classifier
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.classifier(x)
        return x


class FoodDetector:
    """Detects and classifies food items in images using a CNN.

    Provides methods to load a trained model, preprocess images, and
    return top-K food predictions with confidence scores.
    """

    # Standard ImageNet-style normalisation
    _transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    def __init__(self, model_path: str | None = None, device: str | None = None) -> None:
        """Initialise the food detector.

        Args:
            model_path: Path to a saved model checkpoint (.pth).
                        If None, a freshly initialised model is used.
            device: Torch device string (e.g. "cpu", "cuda").
                    Auto-detected if not specified.
        """
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model = FoodCNN(num_classes=len(FOOD_CLASSES)).to(self.device)

        if model_path and Path(model_path).exists():
            state = torch.load(model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)

        self.model.eval()

    def detect(
        self,
        image_path: str,
        top_k: int = 5,
        confidence_threshold: float = 0.1,
    ) -> list[DetectionResult]:
        """Detect food items in an image.

        Args:
            image_path: Path to the image file.
            top_k: Maximum number of predictions to return.
            confidence_threshold: Minimum confidence to include a result.

        Returns:
            List of DetectionResult sorted by confidence descending.
        """
        image = Image.open(image_path).convert("RGB")
        tensor = self._transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = F.softmax(logits, dim=1).squeeze(0)

        top_probs, top_indices = probabilities.topk(top_k)

        results: list[DetectionResult] = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            if prob >= confidence_threshold:
                results.append(
                    DetectionResult(
                        food_name=FOOD_CLASSES[idx],
                        confidence=round(prob, 4),
                    )
                )
        return results

    def detect_from_pil(
        self,
        image: Image.Image,
        top_k: int = 5,
        confidence_threshold: float = 0.1,
    ) -> list[DetectionResult]:
        """Detect food items from a PIL Image object.

        Args:
            image: PIL Image (RGB).
            top_k: Maximum number of predictions.
            confidence_threshold: Minimum confidence.

        Returns:
            List of DetectionResult.
        """
        tensor = self._transform(image.convert("RGB")).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probabilities = F.softmax(logits, dim=1).squeeze(0)

        top_probs, top_indices = probabilities.topk(top_k)

        results: list[DetectionResult] = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            if prob >= confidence_threshold:
                results.append(
                    DetectionResult(
                        food_name=FOOD_CLASSES[idx],
                        confidence=round(prob, 4),
                    )
                )
        return results

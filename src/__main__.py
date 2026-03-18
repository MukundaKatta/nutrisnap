"""CLI for nutrisnap."""
import sys, json, argparse
from .core import Nutrisnap

def main():
    parser = argparse.ArgumentParser(description="NutriSnap — Food Photo Nutrition Analyzer. Snap a photo of your meal, get instant nutritional breakdown.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Nutrisnap()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.analyze(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"nutrisnap v0.1.0 — NutriSnap — Food Photo Nutrition Analyzer. Snap a photo of your meal, get instant nutritional breakdown.")

if __name__ == "__main__":
    main()

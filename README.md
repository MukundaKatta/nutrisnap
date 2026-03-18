# nutrisnap

**NutriSnap — Food Photo Nutrition Analyzer. Snap a photo of your meal, get instant nutritional breakdown.**

![Build](https://img.shields.io/badge/build-passing-brightgreen) ![License](https://img.shields.io/badge/license-proprietary-red)

## Install
```bash
pip install -e ".[dev]"
```

## Quick Start
```python
from src.core import Nutrisnap
 instance = Nutrisnap()
r = instance.analyze(input="test")
```

## CLI
```bash
python -m src status
python -m src run --input "data"
```

## API
| Method | Description |
|--------|-------------|
| `analyze()` | Analyze |
| `evaluate()` | Evaluate |
| `score()` | Score |
| `compare()` | Compare |
| `get_insights()` | Get insights |
| `generate_report()` | Generate report |
| `get_stats()` | Get stats |
| `reset()` | Reset |

## Test
```bash
pytest tests/ -v
```

## License
(c) 2026 Officethree Technologies. All Rights Reserved.

from pathlib import Path


# Active time range path.
CONFIG_PATH = Path("config/active_time_range.json")

DEFAULT_ACTIVE_TIME_RANGE = 3

VALID_ACTIVE_RANGE_MONTHS_VALUES = (1, 2, 3, 4, 5, 6, 9, 12, 24, 36, 48, 60)

WEEKS_PER_MONTH = 4

MINIMAL_LENGTH_USERNAME = 1
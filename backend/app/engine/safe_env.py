from math import (
    ceil, floor, trunc, sqrt,
    log, log10, log2, pow, exp,
    sin, cos, tan, asin, acos, atan,
    radians, degrees,
    fabs, fmod, isclose, isfinite, isinf, isnan
)
from itertools import (
    product, permutations, combinations, combinations_with_replacement,
    accumulate, groupby, chain, count, cycle, repeat
)
from datetime import datetime, timedelta
from uuid import uuid4
import random
import json
import re
import statistics

# Константы
available_constants = {
    "pi": 3.141592653589793,
    "e": 2.718281828459045,
}

available_functions = (
    # Примитивы
    int, str, float, bool, bytes, list, tuple, dict,
    len, range, enumerate, zip, isinstance, type,
    max, min, abs, round, sum, sorted, reversed,

    # Random (всё кроме seed/sample/shuffle/uniform)
    random.randint, random.randrange, random.getrandbits,
    random.choice, random.choices, random.betavariate,
    random.expovariate, random.gammavariate, random.gauss,
    random.triangular, random.weibullvariate,
    random.lognormvariate, random.normalvariate,

    # Time
    datetime, timedelta,

    # Math
    ceil, floor, trunc, sqrt,
    log, log10, log2, pow, exp,
    sin, cos, tan, asin, acos, atan,
    radians, degrees,
    fabs, fmod, isclose, isfinite, isinf, isnan,

    # Itertools
    product, permutations, combinations, combinations_with_replacement,
    accumulate, groupby, chain, count, cycle, repeat,

    # Statistics
    statistics.mean, statistics.median, statistics.stdev,
    statistics.variance, statistics.mode, statistics.fmean,
    statistics.harmonic_mean, statistics.median_grouped,

    # UUID
    uuid4,

    # JSON
    json.loads, json.dumps,

    # Regex
    re.fullmatch, re.match, re.search, re.findall, re.sub, re.split, re.finditer
)

safe_globals = {f.__name__: f for f in available_functions}
safe_globals.update(available_constants)
safe_globals.update(
    {
        "Exception": Exception,
        "BaseException": BaseException,
    }
)

__all__ = ["available_functions", "available_constants", "safe_globals"]

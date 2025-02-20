import math


def to_engineering_notation(value: float, precision: int = 3):
    if value == 0:
        return "0.0"

    exponent = math.floor(math.log10(abs(value)) / 3) * 3
    mantissa = value / (10 ** exponent)

    return f"{mantissa:.{precision}f}E{exponent:+d}"

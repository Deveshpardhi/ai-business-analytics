import math


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _date_label(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        return value.isoformat()

    return str(value)


def calculate_time_series_metrics(
    data,
    measure,
    date_column,
):
    """
    Calculate deterministic trend metrics from an already
    chronologically sorted time series.

    The LLM is never involved in these calculations.
    """
    points = []

    for row in data:
        date_value = row.get(
            date_column
        )

        measure_value = (
            _finite_number(
                row.get(measure)
            )
        )

        if (
            date_value is None
            or measure_value is None
        ):
            continue

        points.append(
            {
                "date": (
                    _date_label(
                        date_value
                    )
                ),
                "value": (
                    measure_value
                ),
            }
        )

    sample_size = len(points)

    if sample_size < 3:
        return {
            "status": (
                "insufficient_data"
            ),
            "sample_size": sample_size,
            "reason": (
                "Time-series trend analysis "
                "requires at least three "
                "valid observations."
            ),
        }

    values = [
        point["value"]
        for point in points
    ]

    first = points[0]
    last = points[-1]

    first_value = first["value"]
    last_value = last["value"]

    absolute_change = (
        last_value - first_value
    )

    if first_value == 0:
        percentage_change = None
    else:
        percentage_change = (
            absolute_change
            / abs(first_value)
            * 100
        )

    previous_value = values[-2]

    latest_period_change = (
        last_value - previous_value
    )

    if previous_value == 0:
        latest_period_percentage_change = (
            None
        )
    else:
        latest_period_percentage_change = (
            latest_period_change
            / abs(previous_value)
            * 100
        )

    x_values = list(
        range(sample_size)
    )

    x_mean = sum(
        x_values
    ) / sample_size

    y_mean = sum(
        values
    ) / sample_size

    denominator = sum(
        (x - x_mean) ** 2
        for x in x_values
    )

    if denominator == 0:
        slope = 0.0
    else:
        slope = (
            sum(
                (x - x_mean)
                * (y - y_mean)
                for x, y in zip(
                    x_values,
                    values,
                )
            )
            / denominator
        )

    intercept = (
        y_mean -
        slope * x_mean
    )

    predictions = [
        intercept + slope * x
        for x in x_values
    ]

    total_variation = sum(
        (value - y_mean) ** 2
        for value in values
    )

    residual_variation = sum(
        (
            value - predicted
        ) ** 2
        for value, predicted
        in zip(
            values,
            predictions,
        )
    )

    if total_variation == 0:
        r_squared = 1.0
    else:
        r_squared = (
            1.0
            - residual_variation
            / total_variation
        )

        r_squared = max(
            0.0,
            min(
                1.0,
                r_squared,
            ),
        )

    scale = max(
        max(
            abs(value)
            for value in values
        ),
        1.0,
    )

    flat_threshold = (
        scale * 0.01
    )

    if (
        abs(absolute_change)
        <= flat_threshold
    ):
        trend_direction = "flat"
        trend_strength = "stable"
    elif slope > 0:
        trend_direction = "rising"
    else:
        trend_direction = "falling"

    if trend_direction != "flat":
        if r_squared >= 0.80:
            trend_strength = "strong"
        elif r_squared >= 0.50:
            trend_strength = (
                "moderate"
            )
        else:
            trend_strength = "weak"

    peak_index = max(
        range(sample_size),
        key=lambda index:
            values[index],
    )

    trough_index = min(
        range(sample_size),
        key=lambda index:
            values[index],
    )

    moving_average_window = 3

    latest_moving_average = (
        sum(
            values[
                -moving_average_window:
            ]
        )
        / moving_average_window
    )

    return {
        "status": "completed",
        "sample_size": sample_size,
        "first_date": (
            first["date"]
        ),
        "first_value": first_value,
        "last_date": (
            last["date"]
        ),
        "last_value": last_value,
        "absolute_change": (
            absolute_change
        ),
        "percentage_change": (
            percentage_change
        ),
        "latest_period_change": (
            latest_period_change
        ),
        "latest_period_percentage_change": (
            latest_period_percentage_change
        ),
        "trend_direction": (
            trend_direction
        ),
        "trend_strength": (
            trend_strength
        ),
        "slope_per_observation": (
            slope
        ),
        "r_squared": r_squared,
        "peak_date": (
            points[
                peak_index
            ]["date"]
        ),
        "peak_value": (
            values[
                peak_index
            ]
        ),
        "trough_date": (
            points[
                trough_index
            ]["date"]
        ),
        "trough_value": (
            values[
                trough_index
            ]
        ),
        "moving_average_window": (
            moving_average_window
        ),
        "latest_moving_average": (
            latest_moving_average
        ),
    }

import datetime


def is_success(status: int):
    return 200 <= status <= 299


def round_to_closest_hour(exact_time: datetime.datetime) -> datetime.datetime:
    current_hour = exact_time.replace(minute=0, second=0, microsecond=0)
    next_hour = (exact_time + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    if next_hour - exact_time < exact_time - current_hour:
        return next_hour
    else:
        return current_hour

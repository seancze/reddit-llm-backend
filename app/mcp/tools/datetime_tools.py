from datetime import datetime, timezone, timedelta


def get_human_readable_datetime(utc_timestamp: int):
    # convert the UTC timestamp to a datetime object
    dt_utc = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)

    # create a timezone object for GMT+8
    gmt8 = timezone(timedelta(hours=8))

    # convert UTC to GMT+8
    dt_gmt8 = dt_utc.astimezone(gmt8)

    # the formatted date should look like "Aug 31 2024, 08:15PM"
    formatted_date = dt_gmt8.strftime("%b %d %Y, %I:%M%p")

    return formatted_date

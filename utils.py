import datetime
from sqlite import get_top_per_month
from pathlib import Path

async def top_month():
    now = datetime.datetime.now()
    now_first_day = now.replace(day=1)
    last_month_day = now_first_day - datetime.timedelta(days=1)
    last_month_name = last_month_day.strftime('%B')
    year = last_month_day.strftime('%Y')
    month = last_month_day.strftime('%m')
    day = last_month_day.strftime('%d')
    top_month = await get_top_per_month(year, month, day)
    Path(f'{year}').mkdir(parents=True, exist_ok=True)
    with open(f'{year}/top_for_{last_month_name}.txt', 'w', encoding='utf8') as file:
        file.write(f'TOP for {last_month_name} {year}\n\n')
        for num, item in enumerate(top_month):
            num += 1
            name, count = item
            file.write(f'#{num:2} - {name:10} - {count:<3}\n')

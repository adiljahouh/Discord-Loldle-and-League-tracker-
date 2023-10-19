from datetime import datetime
import pytz

amsterdam_tz = pytz.timezone('Europe/Amsterdam')
amsterdam_time = datetime.now(amsterdam_tz).date()

print("Current time in Amsterdam:", amsterdam_time)

print("Current time in Amsterdam:", str(amsterdam_time.strftime('%Y-%m-%d')))
today = datetime.now().date()
print(str(today.strftime('%Y-%m-%d')))
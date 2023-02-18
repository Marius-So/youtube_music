from Einslive_to_YTMusic_Bot import *
from keep_alive import keep_alive
from datetime import datetime
from time import sleep

if __name__ == "__main__":

  keep_alive()
  do_daily_bot_update()

  while True:
    sleep(60)
    t = datetime.now()
    print(t.hour, t.minute, t.second)

    if t.hour == 12 and t.minute < 5:
      try:
        do_daily_bot_update()
      except Exception as e:
        print(e)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from finble.daily_update import test_print, update_kr_data_to_db_daily, update_us_data_to_db_daily, update_kospi_data_to_db_daily, update_exchangerate_data_to_db_daily


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(test_print, CronTrigger.from_crontab('* * * * *'))
    scheduler.add_job(update_kr_data_to_db_daily, CronTrigger.from_crontab('40 15 * * MON-FRI'))
    scheduler.add_job(update_us_data_to_db_daily, CronTrigger.from_crontab('30 6 * * TUE-SAT'))
    scheduler.add_job(update_kospi_data_to_db_daily, CronTrigger.from_crontab('40 15 * * MON-FRI'))
    scheduler.add_job(update_exchangerate_data_to_db_daily, CronTrigger.from_crontab('40 15 * * MON-FRI'))
    scheduler.start()
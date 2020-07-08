# https://github.com/eternnoir/pyTelegramBotAPI
# https://github.com/python-telegram-bot/python-telegram-bot
# pip install psutil pyyaml timeloop pyTelegramBotAPI python-telegram-bot
import os.path
import datetime
import logging
import psutil
import time

# pip install urllib3
import urllib3, json
import yaml

# pip install timeloop
from timeloop import Timeloop
from datetime import timedelta
# from threading import Timer

from telegram import ReplyKeyboardMarkup, ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

if os.path.isfile('_tel_creds'):
    global updater
    token = open('_tel_creds', "r").read().strip()
    updater = Updater(token, use_context=True)
else:
    print("Missing credentials.. place it in '_tel_creds' file.")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

repeater = Timeloop()

listen_uid_list = set([])
history_file = './history.yaml'
uid_list_file = './uid_list.json'

@repeater.job(interval=timedelta(seconds=60))
def write_rate():
    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=11"
    currentDT = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    obj = None

    try:
        resp = urllib3.PoolManager().request('GET', url, retries=30, timeout=10.0).data.decode('utf-8')
        obj = json.loads(resp)
    except:
        print(f"[ERR] Get rate from {url} failed.")

    if (obj is not None):
      usd = next((x for x in obj if x['ccy']=='USD'))
      buy_p = round( float(usd['buy']), 2 )
      sale_p = round( float(usd['sale']), 2 )

      list = []

      changed = True
      if (os.path.exists(history_file)):
          list = yaml.load(open(history_file), Loader=yaml.FullLoader)
          if ( (list is not None) and (len(list) > 0) ):
              cur_rate = next( iter(list[-1].values()) )['USD']
              if ([cur_rate['buy'], cur_rate['sale']] != [buy_p, sale_p]):
                  list.append({currentDT: {'USD': {'buy': buy_p,'sale': sale_p}}})
                  send_upd({'USD': {'buy': buy_p,'sale': sale_p}})
              else:
                  changed = False
          else:
              list.append({currentDT: {'USD': {'buy': buy_p,'sale': sale_p}}})
      if changed:
          yaml.dump(list, open(history_file, 'w'), allow_unicode=True)
      del list

def read_rate():
    read_f = yaml.load(open(history_file), Loader=yaml.FullLoader)
    if ( (read_f is not None) and (len(read_f) > 0) ):
        cur_rate = next( iter(read_f[-1].values()) )['USD']
        return {'buy': cur_rate['buy'], 'sale': cur_rate['sale']}


def write_uid_list(uid_list):
    with open(uid_list_file, 'w+') as filehandle:
        json.dump(list(uid_list), filehandle)

def read_uid_list():
    if not os.path.exists(uid_list_file):
        write_uid_list([])
    with open(uid_list_file, 'r') as filehandle:
        return set(json.load(filehandle))

def send_current(context):
    cur_rate = read_rate()
    if cur_rate is not None:
        context.bot.send_message(
            chat_id=context.job.context,
            text=f"*USD*:\n  {cur_rate['buy']} - {cur_rate['sale']}",
            parse_mode=ParseMode.MARKDOWN
        )
    del cur_rate

def send_upd(rate):
    listen_uid_list = read_uid_list()
    for uid in listen_uid_list:
        ccy = rate['USD']
        updater.bot.send_message(uid,
            text=f"*USD*:\n  {ccy['buy']} - {ccy['sale']}",
            parse_mode=ParseMode.MARKDOWN
        )

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def help(update, context):
    help_map = ReplyKeyboardMarkup([['/id', '/start', '/stop', 'ping']], one_time_keyboard=True)
    update.message.reply_text('Hi!', reply_markup=help_map)

def id(update, context):
    update.message.reply_text(f'FirstName:{update.effective_user.first_name}\nID: {update.effective_user.id}')
    print('[INFO] UserID: %s' % update.effective_user.id)

def start(update, context):
    listen_uid_list = read_uid_list()
    listen_uid_list.add(update.effective_user.id)
    write_uid_list(listen_uid_list)

    strstop = ReplyKeyboardMarkup([['/start', '/stop']], one_time_keyboard=True)
    update.message.reply_text('Буду держать тебя в курсе ! Чтоб остановить /stop', reply_markup=strstop)
    context.job_queue.run_once(send_current, 1, context=update.message.chat_id)

def stop(update, context):
    listen_uid_list = read_uid_list()
    if update.effective_user.id in listen_uid_list:
        listen_uid_list.remove(update.effective_user.id)
        write_uid_list(listen_uid_list)

    if 'sub_upd' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return
    context.chat_data['sub_upd'].schedule_removal()
    del context.chat_data['sub_upd']
    update.message.reply_text('Timer successfully unset!')

def ping(update, context):
    update.message.reply_text("Pong\nRAM usage {}%\nCPU load {}%"
        .format(
            str(psutil.virtual_memory()[2]),
            str(psutil.cpu_percent(interval=None))
        )
    )

def rate(update, context):
    context.job_queue.run_once(send_current, 1, context=update.message.chat_id)

def main():
    write_rate()
    print('Started...')

    dp = updater.dispatcher

    dp.add_error_handler(error)
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("id", id))
    dp.add_handler(CommandHandler("start", start, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("rate", rate))
    dp.add_handler(MessageHandler(Filters.regex('ping'), ping))

    dp.bot.send_animation(
        chat_id=371439949,
        caption='Bot started..',
        duration=5,
        animation='https://i.pinimg.com/originals/eb/24/ac/eb24ac9ceb8b614128ed5945a385206a.gif'
    )

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    repeater.start(block=False)
    main()
    while True:
        try:
            time.sleep(1000)
        except KeyboardInterrupt:
            repeater.stop()
            updater.stop()
            break

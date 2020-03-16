# https://github.com/eternnoir/pyTelegramBotAPI
# https://github.com/python-telegram-bot/python-telegram-bot
# pip install pyyaml
import os.path
import datetime
import logging
import psutil
import time

import urllib.request, json
import yaml

from threading import Timer
from telegram import ReplyKeyboardMarkup, ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


if os.path.isfile('./_tel_creds'):
    updater = Updater(open('./_tel_creds', "r").read(), use_context=True)
else:
    print(f"Missing credentials.. place it in '_tel_creds' file.")


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

start_uid_list = set([])




class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def help(update, context):
    help_map = ReplyKeyboardMarkup([['/id', '/start', '/stop']], one_time_keyboard=True)
    update.message.reply_text('Hi!', reply_markup=help_map)

def id(update, context):
    start_uid_list.add(update.effective_user.id)
    update.message.reply_text(f'FirstName:{update.effective_user.first_name}\nID: {update.effective_user.id}')
    print('[INFO] UserID: %s' % update.effective_user.id)
    # update.message.reply_text('Let\'s play %s :)' % update.effective_user.full_name)
    # timer.start()
    # context.chat_data['upd'] = context.job_queue.run_repeating(upd_status, 60, context=cid)

def start(update, context):
    chat_id = update.message.chat_id
    strstop = ReplyKeyboardMarkup([['/start', '/stop']], one_time_keyboard=True)

    update.message.reply_text('Буду держать тебя в курсе ! Чтоб остановить /stop', reply_markup=strstop)
    context.chat_data['upd'] = context.job_queue.run_repeating(upd_status, 30, context=chat_id)
    context.job_queue.run_once(upd_status, 1, context=chat_id)

    read_curs = yaml.load(open('./curs.yaml'), Loader=yaml.FullLoader)
    cur_rate = next(iter(read_curs[-1].values()))['USD']
    context.bot.send_message(
        chat_id,
        text="*Current*\n{}:\n  {} - {}".format('USD', cur_rate['buy'], cur_rate['sell']),
        parse_mode=ParseMode.MARKDOWN
    )
    del read_curs
    #context.bot.send_message(chat_id, text=chat_id)

def stop(update, context):
    # timer.cancel()
    if 'upd' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return
    context.chat_data['upd'].schedule_removal()
    del context.chat_data['upd']
    update.message.reply_text('Timer successfully unset!')

def ping(update, context):
    update.message.reply_text("Pong\nRAM usage {}%\nCPU load {}%"
        .format(
            str(psutil.virtual_memory()[2]),
            str(psutil.cpu_percent(interval=None))
        )
    )

def curs_upd():
    print('Still alive..')

    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=11"
    obj = json.loads(urllib.request.urlopen(url).read().decode())
    currentDT = datetime.datetime.now()

    usd = next((x for x in obj if x['ccy']=='USD'))

    curs_list = []
    if path.exists('./curs.yaml'):
        curs_list = yaml.load(open('./curs.yaml'), Loader=yaml.FullLoader)

    curs_list.append({
        currentDT.strftime("%Y-%m-%d %H:%M"): {
            'USD': {
                'buy': round(float(usd['buy']),2),
                'sell': round(float(usd['sale']),2),
            },
        }
    })

    data = yaml.dump(curs_list, open('./curs.yaml', 'w'), allow_unicode=True)
    del curs_list


def upd_status(context):
    prev_rate = []
    cur_rate  = []
    ### WRITE ONLY DIFF NO INSERT EVERYTIME

    read_curs = yaml.load(open('./curs.yaml'), Loader=yaml.FullLoader)
    if len(read_curs) > 2:
        prev_rate = next( iter(read_curs[-2].values()) )['USD']
    cur_rate = next( iter(read_curs[-1].values()) )['USD']
    if cur_rate != prev_rate:
        context.bot.send_message(
            context.job.context,
            text="*NEW*\n{}:\n  {} - {}".format('USD', cur_rate['buy'], cur_rate['sell']),
            parse_mode=ParseMode.MARKDOWN
        )
    del read_curs

def main():
    curs_upd()
    timer.start()
    print('Started...')

    dp = updater.dispatcher

    dp.add_error_handler(error)
    dp.bot.send_animation(
        chat_id=371439949,
        caption='Bot started..',
        duration=5,
        animation='https://i.pinimg.com/originals/eb/24/ac/eb24ac9ceb8b614128ed5945a385206a.gif'
    )

    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("id", id))
    dp.add_handler(CommandHandler("start", start, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("stop", stop))

    dp.add_handler(MessageHandler(Filters.regex('ping'), ping))
    # dp.add_handler(MessageHandler(Filters.regex(re.compile(r'ping', re.IGNORECASE)), ping))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    timer = RepeatTimer(60, curs_upd)
    main()

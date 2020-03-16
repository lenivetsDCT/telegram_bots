# https://github.com/eternnoir/pyTelegramBotAPI
# https://github.com/python-telegram-bot/python-telegram-bot
import logging
import psutil
import time

from threading import Timer
from telegram import ReplyKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

if os.path.isfile('./_tel_creds'):
    updater = Updater(open('./_tel_creds', "r").read(), use_context=True)
else:
    print(f"Missing credentials.. place it in '_tel_creds' file.")

dp = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

start_uid_list = set([])

strstop = ReplyKeyboardMarkup([['/start', '/stop']], one_time_keyboard=True)
help_map = ReplyKeyboardMarkup([['/start', '/stop', '/my_id']], one_time_keyboard=True)

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def help(update, context):
    update.message.reply_text('Hi!', reply_markup=help_map)

def ford():
    for cid in start_uid_list:
        print('Spam sent to: %s' % cid)
        dp.bot.send_message(chat_id=cid, text="I'm sorry..")
        dp.bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
        time.sleep(3)
        dp.bot.send_message(chat_id=cid, text="but..")
        dp.bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
        time.sleep(3)
        dp.bot.send_message(chat_id=cid, text="Ford")
        dp.bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
        time.sleep(5)
        dp.bot.send_message(chat_id=cid, text="in not a race car")
        dp.bot.send_photo(chat_id=cid, photo='http://webidsite.com/wp/wp-content/uploads/2013/03/troll-meme.jpg')

def my_id(update, context):
    start_uid_list.add(update.effective_user.id)
    print('[INFO] ChatID: %s' % update.effective_user.id)
    update.message.reply_text('Let\'s play %s :)' % update.effective_user.full_name)
    timer.start()
    # context.chat_data['upd'] = context.job_queue.run_repeating(upd_status, 60, context=cid)

def start(update, context):
    chat_id = update.message.chat_id
    update.message.reply_text('Буду держать тебя в курсе ! Чтоб остановить /stop', reply_markup=strstop)
    context.chat_data['upd'] = context.job_queue.run_repeating(upd_status, 120, context=chat_id)
    #context.bot.send_message(chat_id, text=chat_id)

def stop(update, context):
    timer.cancel()
    if 'upd' not in context.chat_data:
        update.message.reply_text('You have no active timer')
        return
    context.chat_data['upd'].schedule_removal()
    del context.chat_data['upd']
    update.message.reply_text('Timer successfully unset!')

def status(update, context):
    update.message.reply_text("RAM usage {}%\nCPU load {}%"
        .format(
            str(psutil.virtual_memory()[2]),
            str(psutil.cpu_percent(interval=None))
        )
    )

def upd_status(context):
    job = context.job
    context.bot.send_message(job.context, text="RAM usage {}%\nCPU load {}%".format(
            str(psutil.virtual_memory()[2]),
            str(psutil.cpu_percent(interval=None))
        )
    )

def main():
    dp.add_error_handler(error)
    dp.bot.send_message(chat_id=371439949, text='Bot started :)')

    dp.add_handler(CommandHandler("help", help))
    #dp.add_handler(CommandHandler("start", start, pass_args=True, pass_job_queue=True, pass_chat_data=True))
    #dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_handler(CommandHandler("my_id", my_id))
    dp.add_handler(CommandHandler("start", start, pass_job_queue=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("stop", stop))

    dp.add_handler(CommandHandler("status", status))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    timer = RepeatTimer(30, ford)
    main()

import sys
import telegram
from telegram import ParseMode
from telegram.ext import CommandHandler, Defaults, Updater
import logging
import Binance_PF_Module as bn
import time
import json
import dataframe_image as dfi


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

global TOKEN, ID

TOKEN = 'TOKEN ID'
ID = 'CHAT ID (GROUP or personal chat)'


def direct_message(msg):
    bot = telegram.Bot(token=TOKEN)
    bot.sendMessage(chat_id=ID, text=msg)

def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('available commands are: \n/on (threshold)\n/off\n/pf\n/setting_check'
                              '\n/setting_w(SYMBOL WEIGHTS)\n/setting_b(SYMBOL PRECISION)\n/setting_a(ASSET)')

def startCommand(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm ready to roll!")


def pf(update, context):
    try:
        direct_message("wait a minute")
        df = bn.view_portfolio()
        df = df.sort_values(by='target_weight', ascending=False)
        df = df.reset_index(drop=True)

        dfi.export(df, 'msg.png', table_conversion='matplotlib')
        time.sleep(10)
        update.message.reply_text('Your current Portfolio status is:')

        bot = telegram.Bot(token=TOKEN)
        bot.send_photo(chat_id=ID, photo=open('msg.png', 'rb'))

    except:
        response = '⚠️ Please try again later'
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def set_weights(update, context):
    try:
        input = context.args
        symbols = []
        weights = []
        for idx, element in enumerate(input):
            if idx % 2 == 0:
                symbols.append(str(element))
            else:
                weights.append(int(element))
        if sum(weights) != 100:
            raise Exception()
        else:
            weight_dict = dict(zip(symbols, weights))
            with open('weights.json', 'w') as fp:
                json.dump(weight_dict, fp)
            context.bot.send_message(chat_id=update.effective_chat.id, text='Setting Done')
    except:
        response = '⚠️ Please check your input format - SYMBOL WEIGHT (MUST HAVE SPACES IN BETWEEN)' \
                   '\neg) BTC 20 ETH 20 USDT 60 \nor \nyour weights do not add up to 100'
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def set_precision(update, context):
    try:
        input = context.args
        symbols = []
        weights = []
        for idx, element in enumerate(input):
            if idx % 2 == 0:
                symbols.append(str(element)+'USDT')
            else:
                weights.append(int(element))

        base_dict = dict(zip(symbols, weights))
        with open('base.json', 'w') as fp:
            json.dump(base_dict, fp)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Setting Done')
    except:
        response = '⚠️ Please check your input format - PAIR Base_Preicision (MUST HAVE SPACES IN BETWEEN)' \
                   '\neg)BTC 6 ETH 5 SOL 3 RUNE 3}'
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def set_assets(update, context):
    try:
        input = context.args
        arr = [i for i in input]
        asset_dict = {"assets": arr}

        with open('asset.json', 'w') as fp:
            json.dump(asset_dict, fp)
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'your asset setting:\n{asset_dict}')
    except:
        response = '⚠️ Error occured! Please check log'
        context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def check_settings(update, context):
    with open('base.json', 'r') as fp:
        base_dict = json.load(fp)
    base_response = f'your setting for precision is:\n{base_dict}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=base_response)

    with open('weights.json', 'r') as fp:
        weights_dict = json.load(fp)
    weights_response = f'your setting for weights is:\n{weights_dict}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=weights_response)

    with open('asset.json', 'r') as fp:
        asset_dict = json.load(fp)
    asset_response = f'your set assets are:\n{asset_dict}'
    context.bot.send_message(chat_id=update.effective_chat.id, text=asset_response)


def PF_rebalancer(update, context, updater=Updater(token=TOKEN)):
    if len(context.args) > 0:
        threshold = context.args[0]

        context.job_queue.run_repeating(monitorCallback, interval=900, first=15,
                                        context=[threshold, update.message.chat_id], name='my_job')
        response = f"⏳ Portfolio Rebalancer ON\nCondition: weight difference > {threshold})!"

    else:
        response = '⚠️ Error occured'

    context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def stop_job(update, context):
    job = context.job_queue.get_jobs_by_name("my_job")
    job[0].schedule_removal()

def monitorCallback(context):
    threshold = context.job.context[0]
    chat_id = context.job.context[1]

    result = bn.view_portfolio()
    for x in result.index:
        if abs(result.at[x, 'weight_diff']) > float(threshold):
            bn.rebal_sell_savings()
            bn.rebalance(result)
            bn.rebal_purchase_savings()
            response = 'Rebalanced!! Check you Portfolio again!'
            # context.job.schedule_removal() # if commented, eternal loop
            context.bot.send_message(chat_id=chat_id, text=response)
            break
        else:
            print('nothing')

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token=TOKEN, defaults=Defaults(parse_mode=ParseMode.HTML))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler('start', startCommand))
    dispatcher.add_handler(CommandHandler('on', PF_rebalancer))
    dispatcher.add_handler(CommandHandler('off', stop_job))
    dispatcher.add_handler(CommandHandler("pf", pf))
    dispatcher.add_handler(CommandHandler("setting_check", check_settings))
    dispatcher.add_handler(CommandHandler("setting_w", set_weights))
    dispatcher.add_handler(CommandHandler("setting_b", set_precision))
    dispatcher.add_handler(CommandHandler("setting_a", set_assets))

    updater.start_polling()  # Start the bot
    updater.idle()  # Wait for the script to be stopped, this will stop the bot as well

if __name__ == '__main__':
    main()
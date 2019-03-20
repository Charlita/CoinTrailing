from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from tinydb import TinyDB, where
import json
import threading
import os
import urllib.request
import logging
import signal
import sys
from colorama import init, Fore, Style
init()
firstrun = True
timer = True

dir_path = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(filename=dir_path + '/app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

db = TinyDB(dir_path + '/db/db.json')
with open(dir_path + '/settings.conf') as json_data_file:
    data = json.load(json_data_file)
binance = Client(data['api']['key'], data['api']['secret'], {"timeout": 20})


def main():
    global firstrun
    if firstrun is True:
        print("CoinTrailing v" + data['settings']['version'])

    checkupdates(data['settings']['version'])
    firstrun = False
    if not installed():
        install()
        update()
    else:
        run = input("CoinTrailing is ready. Run last setup (ENTER) | Re-Install(R) | Edit Coins(E): ") or "Y"
        if run.upper() == "Y":
            update()
        elif run.upper() == "E":
            editcoins()
        else:
            install()
            update()


# @todo this is throwing unhandled exceptions. Will fix later.
def signal_handler(sig, frame):
    # print("Stopping Script...")
    # global timer
    # timer.cancel()
    # main()
    sys.exit()


signal.signal(signal.SIGINT, signal_handler)


def checkupdates(current):
    """
    Checks if there are any new versions of CoinTrailing available.
    :param current: Current version from settings
    :return: Update if available.
    """
    try:
        response = urllib.request.urlopen("http://cointrailing.com/updates/python.txt")
        urldata = response.read()
        version = urldata.decode('utf-8')
        if current < version:
            print("There is an update available: v" + version + " | Check GitHub for the latest version.")
    except Exception as e:
        print("Error Checking For Updates. Ignoring.", e)


def installed():
    """
    Checks if the script has been installed.
    :return:
    """
    if data['settings']['install'] == 0:
        return 0
    else:
        return 1


def stop_loss_price(current, loss_percent):
    """
    :param current: Current price of the coin
    :param loss_percent: The percentage to decrease on the current price for the stop loss
    :return: Stop Loss Price
    """
    current = float(current)
    loss_percent = float(loss_percent)
    price_diff = (current/100)*loss_percent
    stoploss_price = current - price_diff
    return stoploss_price


def rise_price(current, gain_percent):
    """
    :param current: Current price of the coin
    :param gain_percent: The percentage to increase on the current price for the rise price
    :return: Rise Price
    """
    current = float(current)
    gain_percent = float(gain_percent)
    gain_percent = gain_percent / 100
    price_diff = current * gain_percent
    riseprice = current + price_diff
    return riseprice


def addcoin(symbol, coin, pair, original_price, lastprice, gain_percent, loss_percent, stoploss, riseprice, quantity, precision, orderid):
    """
    Adds a coin to our db.json
    :param symbol: Symbol Pair Example: LTCBTC
    :param coin: The coin you are trading. From Above Example: LTC
    :param pair: The coin you are pairing with. From Above Example: BTC
    :param original_price: Starting price
    :param lastprice: The last price of the coin
    :param gain_percent: Percentage above the starting price for the rise price
    :param loss_percent: Percentage below the price for the stoploss
    :param stoploss: The current stoploss price
    :param riseprice: The current rise price
    :param quantity: The quantity of the coin you are selling
    :param precision: The number of digits after the decimal the exchange allows
    :param orderid: The order ID from Binance
    :return: None
    """
    db.insert({'symbol': symbol, 'coin': coin, 'pair': pair, 'original_price': original_price, 'lastprice': lastprice, 'gain_percent': gain_percent, 'loss_percent': loss_percent, 'stoploss': stoploss, 'riseprice': riseprice,
               'quantity': quantity, 'precision': precision, 'active': "1", 'orderid': orderid})


def checkcoin(symbol, riseprice, stoploss, original_price, lastprice, orderid, quantity, loss_percent, gain_percent, precision, doc_id):
    """
    Checks the current price against the rise price and stoploss price
    :param symbol: Symbol Pair Example: LTCBTC
    :param riseprice: Price that once hit we remove old stop loss and create a new one
    :param stoploss: Current stop loss price. Stop checking coin if we fall below this.
    :param original_price: Starting price
    :param lastprice: The last price of the coin
    :param orderid: The order ID from Binance
    :param quantity: The quantity of the coin you are selling
    :param loss_percent: Percentage below the price for the stoploss
    :param gain_percent: Percentage above the starting price for the rise price
    :param precision: The number of digits after the decimal the exchange allows
    :param doc_id: The ID of the coin from our db.json
    :return: None
    """
    try:
        info = binance.get_symbol_ticker(symbol=symbol)
    except (BinanceAPIException, BinanceRequestException) as e:
        logging.exception(e)
        print("Error Getting Symbol Info:", e)
        return

    if float(stoploss) >= float(original_price):
        gainstatus = " | " + Fore.GREEN + "StopLoss is Above Starting Price" + Style.RESET_ALL
    else:
        gainstatus = " | " + Fore.RED + "StopLoss is Below Starting Price" + Style.RESET_ALL

    if info['price'] >= lastprice:
        print("Current " + info['symbol'] + "(" + str(doc_id) + ") " + "Price: " + Fore.GREEN + info['price'] + Style.RESET_ALL + " | Waiting For: " + Fore.YELLOW + str(riseprice)
              + Style.RESET_ALL + " | StopLoss: " + Fore.CYAN + str(stoploss) + Style.RESET_ALL + gainstatus)
    else:
        print("Current " + info['symbol'] + "(" + str(doc_id) + ") " + "Price: " + Fore.RED + info['price'] + Style.RESET_ALL + " | Waiting For: " + Fore.YELLOW + str(riseprice)
              + Style.RESET_ALL + " | StopLoss: " + Fore.CYAN + str(stoploss) + Style.RESET_ALL + gainstatus)

    # The price has risen above our rise price. Cancel old stop loss and create a new one.
    if float(info['price']) > float(riseprice):
        print(info['symbol'] + " Is Above Rise Price - Canceling Old Order (" + str(orderid) + ")")
        binance.cancel_order(symbol=symbol, orderId=orderid)
        logging.info("Canceled Old Order For: " + symbol + "(" + str(doc_id) + ") | Order ID: " + str(orderid))
        new_stop_loss = stop_loss_price(info['price'], loss_percent)
        precision = "{0:." + str(precision) + "f}"
        # We have to add this precision format because Binance only allows so many decimal places per coin.
        new_stop_loss = precision.format(new_stop_loss)
        new_rise_price = rise_price(info['price'], gain_percent)
        new_rise_price = precision.format(new_rise_price)
        print("New Stop Loss:", new_stop_loss)
        print("New Rise Price:", new_rise_price)

        try:
            order = binance.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=new_stop_loss,
                stopPrice=new_stop_loss
            )
        except BinanceAPIException as e:
            logging.exception(e)
            print("Error Creating New Order:", e)
        else:
            print("Created New Order (" + str(order['orderId']) + ")")
            logging.info("Created New Order for: " + symbol + "(" + str(doc_id) + ") | New Order ID: " + str(order['orderId']))
            # print(order)

            db.update({'orderid': order['orderId'], 'lastprice': info['price'], 'riseprice': new_rise_price, 'stoploss': new_stop_loss}, doc_ids=[doc_id])

    # The price has fallen below the stop loss price. Stop checking the coin.
    if float(info['price']) < float(stoploss):
        print(info['symbol'] + " Is BELOW the stop loss price. Check the exchange to check the status of your order.")
        db.update({'active': "0"}, doc_ids=[doc_id])
        print("No Longer Checking " + info['symbol'] + "(" + str(doc_id) + ")")
        logging.info(info['symbol'] + " Is BELOW the stop loss price. No longer checking.")

    db.update({'lastprice': info['price']}, doc_ids=[doc_id])


def update():
    """
    Function that runs every X seconds as defined in the settings.conf
    :return: None
    """
    refresh = data['settings']['refresh']
    global timer
    timer = threading.Timer(refresh, update)
    timer.start()
    i = 1

    # Let's check if there are NO active coins, if so, we will go back to main()
    search = db.search(where('active') == '1')
    if not search:
        print("No Active Coins Available. Please Edit Your Coins or Re-Install")
        timer.cancel()
        main()

    while not i <= len(db):
        print("No Active Coins Created. Please Re-Install")
        timer.cancel()
        main()

    result = db.all()
    for result in result:
        if result['active'] == "1":
            checkcoin(result['symbol'], result['riseprice'], result['stoploss'], result['original_price'], result['lastprice'], result['orderid'], result['quantity'], result['loss_percent'],
                      result['gain_percent'], result['precision'], result.doc_id)


def checkbalance(quantity, balance):
    """
    Check to see if the quantity the user is trying to sell is higher than the available balance.
    :param quantity: The quantity the user is trying to sell
    :param balance: The balance the user has
    :return: 0 if the quantity trying to be sold is higher than the balance.
    """
    if float(quantity) > float(balance):
        return 0
    else:
        return 1


def getprecision(pair):
    """
    We check the precision because Binance only allows a certain number of decimal places per coin.
    Binance Trading Rules: https://support.binance.com/hc/en-us/articles/115000594711-Trading-Rule

    :param pair: The coin pair we are checking. Ex LTCBTC
    :return: The precision allowed by the exchange
    """
    try:
        details = binance.get_symbol_info(pair)
    except BinanceAPIException as e:
        print("Error Getting Symbol Info (Precision): ", e)
        logging.exception(e)
        sys.exit()
    precision = details['filters'][0]['tickSize']
    precision = precision.replace("0.", ".", 1)
    precision = precision.rindex("1")
    return precision


def validcoin(doc_id):
    """
    Used to check user input on the editcoins function.
    :param doc_id: Coin ID in database
    :return: 1 if valid.
    """
    editcoin = db.contains(doc_ids=[int(doc_id)])
    if editcoin:
        return 1
    else:
        return 0


def editcoins():
    """
    Function for editing/deleting existing coins.
    :return: None
    """
    print("Here is a list of your current coins:")
    i = 1
    while not i <= len(db):
        print("No Active Coins Available.")
        main()

    result = db.all()
    for result in result:
        if result['active'] == "1":
            print("Active: Symbol: " + result['symbol'] + " | Gain %: " + str(result['gain_percent']) + " | Loss %: " + str(result['loss_percent']) + " | ID: " + str(result.doc_id))
        else:
            print("NOT Active: Symbol: " + result['symbol'] + " | Gain %: " + str(result['gain_percent']) + " | Loss %: " + str(result['loss_percent']) + " | ID: " + str(result.doc_id))

    coinid = input("What coin would you like to edit? (Enter Coin ID): ") or 0

    while not validcoin(coinid):
        print("The coin ID you entered is incorrect. Let's try again")
        coinid = input("What coin would you like to edit? (Enter Coin ID): ")

    editcoin = db.get(doc_id=int(coinid))
    print("During this process press ENTER to leave the current value.")
    print("Editing " + editcoin['symbol'] + "(" + str(coinid) + ")")
    delete = input("Would you like to delete this coin? Type Y to delete: ") or "N"
    if delete.upper() == "Y":
        try:
            oldorder = binance.get_order(symbol=editcoin['symbol'], orderId=editcoin['orderid'])
        except BinanceAPIException as e:
            print("Error Getting Order Info: ", e)
            logging.exception(e)
            sys.exit()
        if oldorder['status'] == "NEW":
            print("Order is still open. We will cancel it before deleting.")
            try:
                binance.cancel_order(symbol=editcoin['coin'], orderId=oldorder['orderId'])
            except BinanceAPIException as e:
                print("Error Canceling Old Order: ", e)
                logging.exception(e)
                sys.exit()
            else:
                logging.info("Canceled Old Order For: " + editcoin['coin'] + "(" + str(coinid) + ") | Order ID: " + str(oldorder['orderId']))
        db.remove(doc_ids=[int(coinid)])
        print("Coin Deleted.")
        main()
    else:
        rise = int(input("What percentage above the price should the rise price be set at? Current " + str(editcoin['gain_percent']) + "%: ") or int(editcoin['gain_percent']))
        stop = int(input("What percentage below the price should the stop loss be set at? Current " + str(editcoin['loss_percent']) + "%: ") or int(editcoin['loss_percent']))

        oldorder = binance.get_order(symbol=editcoin['symbol'], orderId=editcoin['orderid'])
        balance = binance.get_asset_balance(editcoin['coin'])
        if oldorder['status'] == "NEW":
            print("Order is still open. We will cancel it and create a new one upon editing.")
            print("Your current balance for " + editcoin['coin'] + " is: Free(" + str(balance['free']) + ") | Locked: (" + str(balance['locked']) + ") - 'Locked' includes this order")
            quantity = input("What quantity would you like to sell? Keep in mind the current quantity(" + str(editcoin['quantity']) + ") is in 'Locked' because it's in an order: ") \
                or editcoin['quantity']

            totalbalance = float(balance['free']) + float(balance['locked'])
            while not checkbalance(quantity, totalbalance):
                print("The quantity you entered is greater than your available balance. Let's try again")
                quantity = input("What quantity would you like to sell? Keep in mind the current quantity(" + str(editcoin['quantity']) + ") is in 'Locked' because it's in an order: ")

            print("Canceling old order(" + str(oldorder['orderId']) + ")")
            try:
                binance.cancel_order(symbol=editcoin['symbol'], orderId=oldorder['orderId'])
            except BinanceAPIException as e:
                print("Error Canceling Old Order: ", e)
                logging.exception(e)
                sys.exit()
            else:
                logging.info("Canceled Old Order For: " + editcoin['coin'] + "(" + str(coinid) + ") | Order ID: " + str(oldorder['orderId']))
        else:
            print("Order is closed. We will create a new order upon editing")
            print("Your current balance for " + editcoin['coin'] + " is: Free(" + str(balance['free']) + ") | Locked: (" + str(balance['locked']) + ")")
            quantity = input("What quantity would you like to sell? Current " + str(editcoin['quantity']) + ": ") or editcoin['quantity']
            while not checkbalance(quantity, balance['free']):
                print("The quantity you entered is greater than your available balance. Let's try again")
                quantity = input("What quantity would you like to sell?: ")

        print("Quantity: " + quantity)
        print("Rise %: " + str(rise))
        print("Stop %: " + str(stop))
        info = binance.get_symbol_ticker(symbol=editcoin['symbol'])
        new_stop_loss = stop_loss_price(info['price'], stop)
        precision = "{0:." + str(editcoin['precision']) + "f}"
        # We have to add this precision format because Binance only allows so many decimal places per coin.
        new_stop_loss = precision.format(new_stop_loss)
        new_rise_price = rise_price(info['price'], rise)
        new_rise_price = precision.format(new_rise_price)
        try:
            order = binance.create_order(
                symbol=editcoin['symbol'],
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=new_stop_loss,
                stopPrice=new_stop_loss
            )
        except BinanceAPIException as e:
            print("Error Creating New Order: ", e)
            logging.exception(e)
            sys.exit()
        print("New Stop Loss:", new_stop_loss)
        print("New Rise Price:", new_rise_price)
        print("Created New Order (" + str(order['orderId']) + ")")
        logging.info("Created New Order for: " + editcoin['symbol'] + "(" + str(coinid) + ") | New Order ID: " + str(order['orderId']))
        db.update({'orderid': order['orderId'], 'original_price': info['price'], 'lastprice': info['price'], 'active': '1', 'quantity': quantity, 'gain_percent': rise, 'loss_percent': stop,
                   'riseprice': new_rise_price, 'stoploss': new_stop_loss}, doc_ids=[int(coinid)])
        print("Coin Updated.")
        main()


def install():
    """
    Install Script. Sets API Information, Refresh Rate, Creates Stop Loss Order
    :return: None
    """

    print("Let's set up a few settings before we start.")
    if len(data['api']['key']) == 0:
        print("Your API data has not been set")
        api_key = input("Enter your Binance API Key: ")
        secret_key = input("Enter your Binance API Secret Key: ")
        data['api']['key'] = api_key
        data['api']['secret'] = secret_key

    refresh = int(input("How often (in seconds) would you like to check the coin's price? Default 5: ") or 5)
    data['settings']['refresh'] = refresh
    coin = input("What coin would you like to trail? Ex. LTC: ")
    while not coin:
        print("You did not enter a coin. Let's try again")
        coin = input("What coin would you like to trail? Ex. LTC: ")

    global binance
    try:
        binance = Client(data['api']['key'], data['api']['secret'])
    except BinanceAPIException as e:
        print("Error Getting Binance Client: ", e)
        logging.exception(e)
        sys.exit()
    try:
        balance = binance.get_asset_balance(coin.upper())
    except BinanceAPIException as e:
        print("Error Getting Asset Balance: ", e)
        logging.exception(e)
        sys.exit()

    pair = input("What coin would you like to pair " + coin.upper() + " with? Ex. BTC: ")
    while not pair:
        print("You did not enter a pair. Let's try again")
        pair = input("What coin would you like to pair " + coin.upper() + " with? Ex. BTC: ")

    symbol = coin.upper() + pair.upper()
    print("You will be trading " + symbol)
    print("Your available balance is: " + balance['free'])
    print("What quantity would you like to sell?")
    quantity = input("If the quantity is below 1 start with '0.' Ex. 0.113 : ")

    while not checkbalance(quantity, balance['free']):
        print("The quantity you entered is greater than your available balance. Let's try again")
        quantity = input("What quantity would you like to sell?: ")

    rise = int(input("What percentage above the price should the rise price be set at? Default 1: ") or 1)
    stop = int(input("What percentage below the price should the stop loss be set at? Default 5: ") or 5)
    print("==============================================================")
    print("Ok let's get started...")
    try:
        current = binance.get_symbol_ticker(symbol=symbol)
    except BinanceAPIException as e:
        print("Error Getting Symbol Ticker: ", e)
        logging.exception(e)
        sys.exit()
    print("Current " + symbol + " Price: " + current['price'])
    precision = getprecision(symbol)
    print("Tick Size (Precision): " + str(precision))

    # We format the stop loss and rise price because Binance has Trading Rules that only allow X amount of decimal places. This is called "Min Tick Size" on their website.
    # Binance Trading Rules: https://support.binance.com/hc/en-us/articles/115000594711-Trading-Rule
    precision_format = "{0:." + str(precision) + "f}"
    stop_loss_local = precision_format.format(stop_loss_price(current['price'], stop))
    rise_price_local = precision_format.format(rise_price(current['price'], rise))
    print("Stop Loss: ", stop_loss_local)
    print("Rise Price: ", rise_price_local)
    try:
        order = binance.create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=stop_loss_local,
            stopPrice=stop_loss_local
        )
    except BinanceAPIException as e:
        print("Error Creating New Order: ", e)
        logging.exception(e)
        sys.exit()
    print("Created New Order (" + str(order['orderId']) + ")")
    logging.info("Created New Order for: " + symbol + " | New Order ID: " + str(order['orderId']))

    addcoin(symbol, coin.upper(), pair.upper(), current['price'], current['price'], rise, stop, stop_loss_local, rise_price_local, quantity, precision, order['orderId'])

    data['settings']['install'] = 1
    # Save settings to settings.conf
    with open('settings.conf', 'w') as json_save_file:
        json.dump(data, json_save_file, indent=4)
    return


if __name__ == "__main__":
    main()

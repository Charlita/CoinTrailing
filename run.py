from binance.client import Client
from tinydb import TinyDB
import json
import threading
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
db = TinyDB(dir_path + '/db/db.json')
with open(dir_path + '/settings.conf') as json_data_file:
    data = json.load(json_data_file)


# @todo Get CMD colors working :(
class bcolors:
    HEADER = ''  # '\033[95m'
    OKBLUE = ''  # '\033[94m'
    OKGREEN = ''  # '\033[92m'
    CYAN = ''  # '\033[0;36;48m'
    WARNING = ''  # '\033[93m'
    FAIL = ''  # '\033[91m'
    ENDC = ''  # '\033[0m'


binance = Client(data['api']['key'], data['api']['secret'])


def main():
    print("CoinTrailing v" + data['settings']['version'])
    if not installed():
        install()
        update()
    else:
        run = input("CoinTrailing is ready. Run last setup (ENTER) or Re-Install(N): ") or "Y"
        if run == "Y":
            update()
        else:
            install()
            update()


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


def addcoin(symbol, original_price, gain_percent, loss_percent, stoploss, riseprice, quantity, precision, orderid):
    db.insert({'symbol': symbol, 'original_price': original_price, 'gain_percent': gain_percent, 'loss_percent': loss_percent, 'stoploss': stoploss, 'riseprice': riseprice,
               'quantity': quantity, 'precision': precision, 'active': "1", 'orderid': orderid})


def checkcoin(symbol, riseprice, stoploss, original_price, orderid, quantity, loss_percent, gain_percent, precision, doc_id):
    info = binance.get_symbol_ticker(symbol=symbol)

    if info['price'] >= original_price:
        print(bcolors.CYAN, "Current " + info['symbol'] + "(" + str(doc_id) + ") " + "Price: " + info['price'] + bcolors.ENDC + "| Waiting For:" + str(riseprice) +
              " | StopLoss: " + str(stoploss))
    else:
        print(bcolors.FAIL, "Current " + info['symbol'] + "(" + str(doc_id) + ") " + "Price: " + info['price'] + bcolors.ENDC + "| Waiting For:" + str(riseprice) +
              " | StopLoss: " + str(stoploss))

    if float(info['price']) > float(riseprice):
        binance.cancel_order(symbol=symbol, orderId=orderid)

        print(info['symbol'] + " Is Above Rise Price - Canceling Old Order (" + str(orderid) + ")")
        new_stop_loss = stop_loss_price(info['price'], loss_percent)
        precision = "{0:." + precision + "f}"
        # We have to add this precision format because Binance only allows so many decimal places per coin.
        new_stop_loss = float(precision.format(new_stop_loss))
        new_rise_price = rise_price(info['price'], gain_percent)
        new_rise_price = float(precision.format(new_rise_price))
        print("New Stop Loss:", new_stop_loss)
        print("New Rise Price:", new_rise_price)

        order = binance.create_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=new_stop_loss,
            stopPrice=new_stop_loss
        )
        print("Created New Order (" + str(order['orderId']) + ")")
        # print(order)

        db.update({'orderid': order['orderId'], 'riseprice': new_rise_price, 'stoploss': new_stop_loss}, doc_ids=[doc_id])


def update():
    refresh = data['settings']['refresh']
    threading.Timer(refresh, update).start()
    i = 1

    while not i <= len(db):
        print("No Active Coins Available.")

    while i <= len(db):
        result = db.get(doc_id=i)
        if result['active'] == "1":
            checkcoin(result['symbol'], result['riseprice'], result['stoploss'], result['original_price'], result['orderid'], result['quantity'], result['loss_percent'],
                      result['gain_percent'], result['precision'], i)
        i += 1



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
    details = binance.get_symbol_info(pair)
    # print(details)
    # print(details['filters'][0]['tickSize'])
    precision = details['filters'][0]['tickSize']
    precision = precision.replace("0.", ".", 1)
    precision = precision.rindex("1")
    return precision


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
        print(bcolors.FAIL + "You did not enter a coin. Let's try again" + bcolors.ENDC)
        coin = input("What coin would you like to trail? Ex. LTC: ")
    coin.upper()

    global binance
    binance = Client(data['api']['key'], data['api']['secret'])
    balance = binance.get_asset_balance(coin)

    pair = input("What coin would you like to pair " + coin + " with? Ex. BTC: ")
    while not pair:
        print(bcolors.FAIL + "You did not enter a pair. Let's try again" + bcolors.ENDC)
        pair = input("What coin would you like to pair " + coin + " with? Ex. BTC: ")
    pair.upper()

    symbol = coin + pair
    print("You will be trading " + symbol)
    print("Your available balance is: " + balance['free'])
    print("What quantity would you like to sell?")
    quantity = input("If the quantity is below 1 start with '0.' Ex. 0.113 : ")

    while not checkbalance(quantity, balance['free']):
        print(bcolors.FAIL + "The quantity you entered is greater than your available balance. Let's try again" + bcolors.ENDC)
        quantity = input("What quantity would you like to sell?: ")

    rise = int(input("What percentage above the price should the rise price be set at? Default 1: ") or 1)
    stop = int(input("What percentage below the price should the stop loss be set at? Default 5: ") or 5)
    print("==============================================================")
    print("Ok let's get started...")
    current = binance.get_symbol_ticker(symbol=symbol)
    print("Current " + symbol + " Price: " + current['price'])
    precision = getprecision(symbol)
    print("Tick Size (Precision): " + str(precision))

    # We format the stop loss and rise price because Binance has Trading Rules that only allow X amount of decimal places. This is called "Min Tick Size" on their website.
    # Binance Trading Rules: https://support.binance.com/hc/en-us/articles/115000594711-Trading-Rule
    precision_format = "{0:." + str(precision) + "f}"
    stop_loss_local = float(precision_format.format(stop_loss_price(current['price'], stop)))
    rise_price_local = float(precision_format.format(rise_price(current['price'], rise)))
    print("Stop Loss: " + str(stop_loss_local))
    print("Rise Price: " + str(rise_price_local))

    order = binance.create_order(
        symbol=symbol,
        side=Client.SIDE_SELL,
        type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
        timeInForce=Client.TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=stop_loss_local,
        stopPrice=stop_loss_local
    )
    print("Created New Order (" + str(order['orderId']) + ")")

    addcoin(symbol, current['price'], rise, stop, stop_loss_local, rise_price_local, quantity, precision, order['orderId'])

    data['settings']['install'] = 1
    # Save settings to settings.conf
    with open('settings.conf', 'w') as json_save_file:
        json.dump(data, json_save_file, indent=4)
    return


if __name__ == "__main__":
    main()

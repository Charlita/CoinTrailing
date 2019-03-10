# CoinTrailing
Allows for the creation of a trailing stop loss on Binance. Great for securing profits, or for coins that have a history of pumping.

*This is my first Python script, I decided to write it to help me learn Python. If there are any issues please let me know via Discord or issues/pull requests*

## Support
**Discord for live support and general chat https://discord.gg/hxWGneV**

## Disclaimer
**Use at your own risk.**

## Future Updates
* Multiple Exchanges (Unfortunately some exchanges do not allow stop-loss orders via API)
* Fix the interrupt script to immediately stop the program.
* Add Colorama for colored output

## Getting Started

### Prerequisites

Python 3+

```
### Python Requirements: ###
autobahn
certifi
chardet
cryptography
dateparser
pyOpenSSL
requests
service-identity
Twisted
tinydb
```

When I set this up on a vanilla machine these were the dependencies I had to install via pip:
```
pip install requests
pip install dateparser
pip install tinydb
```

### Installing

**When creating an API key, I suggest NOT allowing withdrawals.**

Run run.py in CMD and follow the installation instructions:
```
Enter your Binance API Key:
Enter your Binance API Secret Key:
How often (in seconds) would you like to check the coin's price? Default 5: 5
What coin would you like to trail? Ex. LTC: BNB
What coin would you like to pair X with? Ex. BTC: BTC
What quantity would you like to sell? 0.95
What percentage above the price should the rise price be set at? Default 1: 1
What percentage below the price should the stop loss be set at? Default 5: 3
```

### Install Multiple Coins
After the initial install press CTRL+C (This will take a few seconds to register). Choose the re-install option and input another coin.
The script will automagically check both coins.

When checking multiple coins the output will look like:
```
Current LTCBTC(1) Price: 0.01240500...
Current BNBBTC(2) Price: 0.00289980...
```


## Reading The Output
```
Current BNBBTC(1) Price: 0.00360890 | Waiting For: 0.0036458 | StopLoss: 0.003357 | Below Start Price of 0.0036097
```
* Current Price: The Current Price of the Coin
* Waiting For: The Rise Price. When it hits this price it will increase the stop loss
* StopLoss: The StopLoss price. When it hits this price it will no longer check the coin.
* Above/Below Start: Currently Above/Below the starting price of when you started this script.


## Editing Coins
Editing Options:
* Delete Coin
* Change Rise Percentage
* Change Stop Loss Percentage
* Change Quantity

## Changelog

> **v1.0.1**
> * Added Coin Editing
> * Added Version Check
> * Added Logging
> * Fixed a crash that happened when deleting old orders
>
> **v1.0.0**
> * Initial Release

## Built With

* [python-binance](https://github.com/sammchardy/python-binance) - Python Binance API
* [TinyDB](https://tinydb.readthedocs.io/en/latest/) - Database for Coins

## Authors

* **Charlita** - *Developer*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Examples
Bought beginning of breakout. As the coin went up (1%) the trail was set at 2% below.
![example1](https://github.com/Charlita/CoinTrailing/blob/master/examples/example1.png)

## Donate
If this script helped you out feel free to donate.
* BTC: bc1qpszmsad8rcy50ze9wg7ntcxuktqmnuywfy3ucq
* ETH: 0x0De6fDb75A34D148Bcd5a853b89a5aCBBD88db13
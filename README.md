# CoinTrailing
Allows for the creation of a trailing stop loss on Binance. Great for securing profits, or for coins that have a history of pumping.

## Support
**Discord Chat for live support and general chat https://discord.gg/hxWGneV**

## Disclaimer
**Use at your own risk.**

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
After the initial install close the script and re-open. Choose the re-install option and input another coin.
The script will automagically check both coins.

When checking multiple coins the output will look like:
```
Current LTCBTC(1) Price: 0.01240500...
Current BNBBTC(2) Price: 0.00289980...
```

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

## Donate
If this script helped you out feel free to donate.
* BTC: bc1qpszmsad8rcy50ze9wg7ntcxuktqmnuywfy3ucq
* ETH: 0x0De6fDb75A34D148Bcd5a853b89a5aCBBD88db13
from setuptools import setup

setup(
    name='CoinTrailing',
    version='1.0.0',
    packages=['binance'],
    url='http://cointrailing.com',
    license='MIT',
    author='Charlita',
    author_email='charlita@cointrailing.com',
    install_requires=['requests', 'six', 'Twisted', 'pyOpenSSL', 'autobahn', 'service-identity', 'dateparser', 'urllib3', 'chardet', 'certifi', 'cryptography', 'tinydb'],
    description='Creates a trailing stop loss on Binance.',
    uses='https://github.com/sammchardy/python-binance'
)

# crypto_rebal

**Automated cryptocurrency investment portfolio rebalancing tool**

Medium Link: https://medium.com/@rukawa917

The weight of each assets are decided based on personal research and intuition.

The is not an official product or service, so use with caution.

Required packages:
- pandas
- python-binance
- python-telegram-bot
- dataframe-image
- lxml

# Logs
2021-11-23:
- Spotted a bug that doesn't combine the assets in the flexible savings and spot wallet.
- Will be fixed asap.

2021-11-11:
- changes in view_portfolio() func
  - deleted parameters
  - originally, only preset assets were visible. Now you can see all the assets.
- Change applied to telegram bot module

2021-10-13: 
- added automatic subscription and redemption of fleixble savings
during rebalancing.
- Deleted ignore_lst variable by retreiving only active pairs in get_spotWallet() in Binance_API_Module

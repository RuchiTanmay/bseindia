# bseindia 0.1

Python Library to get publicly available data on new BSE india website.

Release Notes
* Compatible and Tested with Python 3.9 and above
* Future release will be done on requirement basic

## Libraries Required
- requests
- beautifulsoup
- numpy 
- scipy
- pandas
- lxml

For Windows systems you can install Anaconda, this will cover many dependencies (You'll have to install requests and beautifulsoup additionally though)

## Installation
Fresh installation 

```$pip install bseindia```

Upgrade

```$pip install bseindia --upgrade```

## Function list

### bseindia
* trading_holiday_calendar
* historical_stock_data
* equity_bhav_copy
* derivative_bhav_copy
* stock_info

Example :

import bseindia

data = bseindia.trading_holiday_calendar()


Example :

data = bseindia.get_historical_stock_data(symbol='SBIN', from_date='01-06-2023', to_date='10-06-2023')
                                            
OR

data = bseindia.get_historical_stock_data(symbol='SBIN', period='1M')

Example :

data = bseindia.equity_bhav_copy(trade_date='01-07-2024')

More functions will be available in future releases...

## How can I contribute?
There are multiple ways in which you can contribute-

### Write about your project

There are working on to add many function to this library. BSElib at the moment is short of good documentation. There are lot of features in BSElib yet to come :( , so till we complete the documentation, I'll need support from the community.

Please write about your projects in blogs, quora answers and other forums, so that people find working examples to get started.

### Raising issues, bugs, enhancement requests

For quick resolution please raise issues both [here on issue page](https://github.com/RuchiTanmay/bselib/issues). I'll try my best to address the issues quickly on github as and when I get notified, but raising it on stackoverflow will provide you access to a larger group and someone else might solve your problem before I do.

### Submit patches

If you have fixed an issue or added a new feature, please fork this repository, make your changes and submit a pull request. [Here's good article on how to do this.](https://code.tutsplus.com/tutorials/how-to-collaborate-on-github--net-34267) 

Looking forward for healthy participation from community.

The script is to download document from https://max.book118.com, for web scraping study only

# Prerequisite
* selenium, to scraping books from url

`pip install selenium`

* chrome & chromedriver

Download chromedriver from https://sites.google.com/a/chromium.org/chromedriver/downloads ,unzip and put the executable under the same directory of maxbook118_downloader.py 

* reportlab, to generate pdf

`pip install reportlab`

* python3.x

# Example 
`python maxbook118_downloader.py --url https://max.book118.com/html/2017/0712/121971213.shtm`

When --url is given, the script will start browser, scraping document from url and store document into cache directory. After all document is downloaded, one pdf will be generated under the same directory

When network connection is not stable, it is possible that only parts of document is downloaded. In this case, try to increase --wait_interval (default 2.5 seconds) and download again.

If downloading to frequent, captcha might appear. The downloading will continue after the captcha is typed manually.

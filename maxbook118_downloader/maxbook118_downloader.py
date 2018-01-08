#!/usr/bin/python3
# Chao Xu
import os
import logging
import argparse
import re
import time
import urllib

from selenium import webdriver
from reportlab.pdfgen import canvas

# logger
LOGGER='dumpbook118'

DEFAULT_WAIT_INTERVAL=2.5

def init_logging(verbose):    
    log = logging.getLogger(LOGGER)
    
    ch  = logging.StreamHandler()
    log.addHandler(ch)
    if verbose:       
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
        
def clear_cache_dir(dir):
    log = logging.getLogger(LOGGER)
    if not os.path.exists(dir):
       log.info("cache dir %s not found, creating" % dir)
       os.mkdir(dir)
       
    if os.path.isdir(dir):
        cachefiles = os.listdir(dir)
        for cachefile in cachefiles:
            fullfilename = os.path.join(dir, cachefile)
            if os.path.isfile(fullfilename):
                try:
                    os.remove(fullfilename)
                except os.error:
                    log.error("remove %s error. please remove manually" % fullfilename)
                    exit(-1)
    
    log.info("cache dir %s is cleared" % dir)
    
def check_url(url):
    log = logging.getLogger(LOGGER)
    pattern = re.compile(r'^((https|http)?:\/\/)max.book118.com[^\s]+')
    if pattern.match(url) is None:
        log.error("input url is not correct, should be like https://max.book118.com/xxx")
        exit(-1)
   
def get_images_src(url, wait_interval):
    log = logging.getLogger(LOGGER)
    # open url
    driver = webdriver.Chrome(executable_path="chromedriver.exe")    
    log.debug("chrome driver created")    
    driver.get(url)
    time.sleep(1)
    
    # start preview and move to preview iframe
    driver.find_element_by_class_name("view-dialog-btn").click()
    while(True):
        time.sleep(0.5)
        content_div = driver.find_element_by_class_name("layui-layer")
        tmp_type = content_div.get_attribute("type")
        log.debug(tmp_type)
        if tmp_type == "iframe":
            break
       
    iframeid = "layui-layer" + "-" + content_div.get_attribute("type") + content_div.get_attribute("times")    
    driver.switch_to.frame(iframeid)
    
    # try load all pages, continue scroll to the end of page 
    page_id = 0
    log.info("loading document, please be patient")
    while(True):
        page_id += 1
        oldScrollHeight = driver.find_element_by_id("pdf").get_property("scrollHeight")
        log.debug("start to scroll down page {0}.".format(page_id))
        driver.execute_script('document.getElementById("pdf").scrollTo(0,document.getElementById("pdf").scrollHeight)')
        time.sleep(wait_interval)
        newScrollHeight = driver.find_element_by_id("pdf").get_property("scrollHeight")
        
        if newScrollHeight <= oldScrollHeight:
            break
    
    # get url of images
    images_src = []
    for image in driver.find_element_by_id("pdf").find_elements_by_tag_name("img"):
        log.debug("image src %s" % image)
        images_src.append(image.get_attribute("src"))
        
    driver.close()
    
    return images_src

def fetch_images(images_src, dir):
    log = logging.getLogger(LOGGER)
    id = 0
    for image_src in images_src:
        id += 1
        log.info("fetching image {0}.png".format(image_src))
        urllib.request.urlretrieve(image_src, "{0}/{1}.png".format(dir, id))
    log.info("fetch image completed")
    
def generate_pdf(cache_dir):
    log = logging.getLogger(LOGGER)
    nop = 0
    c = canvas.Canvas('download.pdf')
    images = [image for image in os.listdir(cache_dir) if os.path.isfile(cache_dir + '/' + image) and image[-4:] == ".png"]
    totalnum = len(images)
    
    from reportlab.lib.pagesizes import A4,portrait,landscape
    (w,h) = portrait(A4)
    while nop < totalnum:
        nop += 1
        c.drawImage('{0}/{1}.png'.format(cache_dir,nop),0,0,w,h)
        c.showPage()
    c.save()
    log.info("pdf file generated!")
    
def download(url, wait_interval, cache_dir):
    log = logging.getLogger(LOGGER)
    images_src = get_images_src(url, wait_interval)
    fetch_images(images_src, cache_dir)
    generate_pdf(cache_dir)
    
def main():
    """This script is used to download books from https://max.book118.com"""
    log = logging.getLogger(LOGGER)

    # script usage text
    usage = "%prog --url Url [--wait_interval Interval] [--debug Debug]"
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument(
        "--url",
        dest="url",
        type=str,
        help="document url"
    )
    parser.add_argument(
        "--wait_interval",
        dest="wait_interval",
        type=int,
        default=DEFAULT_WAIT_INTERVAL,
        help="wait seconds(default 2s) when caching each document page, the value depends on network connection"
    )   
    parser.add_argument(
        "--debug",
        action="store_true",
        dest="verbose",
        default=False,
        help="print more info"
    )
    args = parser.parse_args()
    
    # consistency check and initialization
    check_url(args.url)
    init_logging(args.verbose)    
    clear_cache_dir("cache")
    
    # download
    download(args.url, args.wait_interval, "cache")
   
if __name__ == '__main__':
    main()

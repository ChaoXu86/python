#!/usr/bin/python
# auther: Chao Xu

import os
import logging

from optparse import OptionParser

# logger
LOGGER='get_imei_info'

def parse_tac_database(tacDataBase, delimma):
    log = logging.getLogger(LOGGER)
    
    with open(tacDataBase, encoding="utf8") as fr:
        lines = fr.readlines()
        
    columnHeader = lines[0].strip().split(delimma)
    imeidict = {}
    for line in lines[1:]:
        tacData  = line.strip().split(delimma)
        imeiCode = tacData[0]
        imeiInfo = tacData[1:]
        imeidict[imeiCode] = imeiInfo
    
    log.debug('[DEBUG] parse_tac_database column header %r, number of data %d' % (columnHeader, len(imeidict.keys())))
    return columnHeader, imeidict
    
def lookup_imei_info(imei, imeiDict):
    log = logging.getLogger(LOGGER)
    imeiCode = imei[0:8]
    imeiInfo = imeiDict.get(imeiCode, 'not_found')
    log.debug('[DEBUG] lookup_imei_info imei %s, imei info %r' % (imei, imeiInfo))
    return imeiInfo
        
def get_imei_info(tacDataBase, delimma, imei):
    log = logging.getLogger(LOGGER)
    log.debug('[DEBUG] get_imei_info database %s, delimma %s, imei %s' % (tacDataBase, delimma, imei))
    columnHeader, imeiDict = parse_tac_database(tacDataBase, delimma)
    imeiInfo = lookup_imei_info(imei, imeiDict)
    show_imei_info(columnHeader, imei, imeiInfo)
    
def show_imei_info(columnHeader, imei, imeiInfo):
    log = logging.getLogger(LOGGER)
    if type(imeiInfo) != list:
        print("%s not found in db" % (imei))
    else:
        fullImeiInfo = [imei] + imeiInfo
        for i in range(len(columnHeader)):
            print("%30s: %s" %(columnHeader[i],fullImeiInfo[i]))

def main():
    """This script is get imei info from database(csv file)"""
    log = logging.getLogger(LOGGER)

    # script usage text
    usage = "%prog -d database  -i imei(sv) --delimma delimmastr"

    parser = OptionParser(usage=usage)

    parser.add_option(
        "-d","--db",
        dest="database",
        type=str,
        help="tac database file")

    parser.add_option(
        "-i","--imei",
        dest="imei",        
        help="imei or imeisv")

    parser.add_option(
        "--delimma",
        dest="delimma",
        type=str,
        default="|",
        help="delimma of database csv file"
    )
    
    parser.add_option(
        "--debug",
        action="store_true",
        dest="verbose",
        default=False,
        help="print more info")

    options, args = parser.parse_args()
    for arga in args:
        print(arga)

    # setup logging
    ch = logging.StreamHandler()
    log.addHandler(ch)
    if options.verbose:
        # set logging to debug
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # consistency check
    if not options.database:
        parser.error("Missing mandatory argument: '-d'")
    if not options.imei:
        parser.error("Missing mandatory argument: '-i'")    
    if len(options.imei) < 15:
        parser.error("Invalid imei length")
    
    # main function starts here
    tacDataBase = options.database
    delimma = options.delimma
    imei = options.imei
    
    get_imei_info(tacDataBase, delimma, imei)

if __name__ == '__main__':
    main()


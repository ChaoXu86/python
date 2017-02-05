#!/usr/bin/python
# exxucao

import os
import logging

from optparse import OptionParser
from Crypto.Cipher import AES

# cipher passwd
CIPHER_KEY = "who's your daddy"
CIPHER_BS  = AES.block_size
CIPHER_PAD = lambda s: s+(CIPHER_BS - len(s) % CIPHER_BS) * chr(CIPHER_BS - len(s) % CIPHER_BS)
CIPHER_UNPAD = lambda s: s[0:-ord(s[-1])]

# logger
LOGGER='authcfg'

# trick
LEN_BLOCK = 4

# info format
INFO_HEADER = ['Id','Name','Password','Tenant','Url']
# INFO_WIDTH  = [   4,    20,        20,      20,   60]

def print_header():
    print_params(INFO_HEADER)

def print_params(paramList):
    print  "%4s |" % paramList[0],
    print "%20s |" % paramList[1],
    print "%20s |" % paramList[2],
    print "%20s |" % paramList[3],
    print "%60s |" % paramList[4]

def cipher_str(string):
    log = logging.getLogger(LOGGER)
    cryptor = AES.new(CIPHER_KEY)
    ciphered_str = cryptor.encrypt(CIPHER_PAD(string)).encode('hex')
    log.debug("[DEBUG] cipher %s -> %s" % (string, ciphered_str) )
    return ciphered_str

def decipher_str(string):
    log = logging.getLogger(LOGGER)
    cryptor = AES.new(CIPHER_KEY)
    deciphered_str = CIPHER_UNPAD(cryptor.decrypt(string.decode('hex')))
    log.debug("[DEBUG] decipher %s -> %s" % (string, deciphered_str) )
    return deciphered_str

def set_parameter(cfgFile, uid, name, password, tenant, auth_url):
    log = logging.getLogger(LOGGER)
    message = encode([name, password, tenant, auth_url])
    replaceline = uid + ' ' + message + '\n'

    # read cfg
    allLines = ''
    if os.path.isfile(cfgFile):
        with open(cfgFile,'r') as fr:
            allLines = fr.readlines()

    log.debug('[DEBUG] new parameter info %s' % replaceline)
    # update cfg
    with open(cfgFile,'w') as fw:
        # always make the updated entry to top
        fw.write(replaceline)
        for line in allLines:
            if not line.startswith(uid):
                fw.write(line)

def delete_parameter(cfgFile,uid):
    if os.path.isfile(cfgFile):
        with open(cfgFile,'r') as fr:
            allLines = fr.readlines()

    with open(cfgFile,'w') as fw:
        for line in allLines:
            if not line.startswith(uid):
                fw.write(line)
def list_parameter(cfgFile):
    print_header()
    if os.path.isfile(cfgFile):
        with open(cfgFile,'r') as fr:
            allLines = fr.readlines()

    for line in allLines:
        [uid, encoded_info] = line.split()
        result = decode(encoded_info)
        result.insert(0,uid)
        print_params(result)

def get_parameter(cfgFile, uid):
    log = logging.getLogger(LOGGER)
    if os.path.isfile(cfgFile):
        with open(cfgFile,'r') as fr:
            allLines = fr.readlines()

    for line in allLines:
        if line.startswith(uid):
            # get rid of uid
            encoded_info = line.split()[-1]
            result = decode(encoded_info)

    result.insert(0,uid)
    log.debug('[DEBUG] get_parameter %r %r -> %r' % (cfgFile, uid, result))
    return result

def encode_len(string):
    ## 'helloworld' -> 000ahelloworld
    log = logging.getLogger(LOGGER)
    lenstr = hex(len(string))[2:]
    length = len(lenstr)
    pad = '0' * (LEN_BLOCK - length)
    encoded_len = pad + lenstr
    log.debug('[DEBUG] encode_len of %s : %s' % (string, encoded_len))
    return encoded_len

def decode_len(string):
    log = logging.getLogger(LOGGER)
    length = int(string, 16)
    log.debug('[DEBUG] decode_len of %s : %d' % (string, length))
    return length

def encode(strList):
    log = logging.getLogger(LOGGER)
    oneLine=''
    for item_str in strList:
        encoded_item = cipher_str(item_str)
        oneLine=oneLine + encode_len(encoded_item) + encoded_item
    log.debug('[DEBUG] encode %r -> %s' % (strList, oneLine))
    return oneLine

def decode(string):
    log = logging.getLogger(LOGGER)
    decoded_strList = []
    rest = string
    while rest != '':
        lenstr  = rest[0:LEN_BLOCK]
        itemlen = decode_len(lenstr)
        itemstr = rest[LEN_BLOCK:LEN_BLOCK + itemlen]
        rest    = rest[LEN_BLOCK + itemlen:]
        decoded_strList.append(decipher_str(itemstr))
    log.debug('[DEBUG] decode %s -> %r' % (string, decoded_strList))
    return decoded_strList

def main():
    """This script is used to get/put the authentication related configuration of openstack."""
    log = logging.getLogger(LOGGER)

    # script usage text
    usage = "%prog -i Id  [-l] [--get] [--delete] [--put --name Name --passwd Password --tenant Tenant --url AuthUrl] [-c CfgFile] [--debug]\n\
example: %prog -i 1 --put --name Admin --passwd Admin --tenant ECM --url https://10.147.32.171:5000/v2.0\n\
         %prog -i 1 [--get] \n\
         %prog -i 1 --delete \n\
         %prog -l"

    parser = OptionParser(usage=usage)

    parser.add_option(
        "-i","--uid",
        dest="uid",
        type=str,
        help="unique id of user ")

    parser.add_option(
        "-l","--list",
        dest="is_list",
        action="store_true",
        help="list all parameters from file ")

    parser.add_option(
        "--get",
        dest="is_save",
        action="store_false",
        help="get parameter information ")

    parser.add_option(
         "--delete",
        dest="is_delete",
        action="store_true",
        help="delete parameter information "
    )

    parser.add_option(
        "--put",
        dest="is_save",
        action="store_true",
        help="put parameter information ")

    parser.add_option(
        "--name",
        dest="name",
        type=str,
        help="openstack username"
    )
    parser.add_option(
        "--passwd",
        dest="password",
        type=str,
        help="openstack password"
    )
    parser.add_option(
        "--tenant",
        dest="tenant",
        type=str,
        help="openstack tenant id"
    )
    parser.add_option(
        "--url",
        dest="auth_url",
        type=str,
        help="openstack authentication url"
    )
    parser.add_option(
        "-c","--conf",
        dest="conf",
        type=str,
        default="auth.cfg",
        help="configuration file name"
    )

    parser.add_option(
        "--debug",
        action="store_true",
        dest="verbose",
        default=False,
        help="print more info")

    options, args = parser.parse_args()
    for arga in args:
        print arga

    # setup logging
    ch = logging.StreamHandler()
    log.addHandler(ch)
    if options.verbose:
        # set logging to debug
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # consistency check
    if not options.uid and not options.is_list:
        parser.error("Missing mandatory argument: '-i/-l'")
    if options.is_save :
        if not options.name:
            parser.error("Missing mandatory argument: '--name' ")
        if not options.password:
            parser.error("Missing mandatory argument: '--passwd' ")
        if not options.tenant:
            parser.error("Missing mandatory argument: '--tenant' ")
        if not options.auth_url:
            parser.error("Missing mandatory argument: '--url' ")
    if options.is_delete :
        if not options.uid:
            parser.error("Missing mandatory arugment: '-i' ")

    # main function begins
    if options.is_save:
        set_parameter(options.conf, options.uid, options.name, options.password,\
                      options.tenant,options.auth_url)
    elif options.is_delete:
        delete_parameter(options.conf, options.uid)
    elif options.is_list:
        list_parameter(options.conf)
    else:
        allParams = get_parameter(options.conf, options.uid)
        print_params(allParams)

if __name__ == '__main__':
    main()



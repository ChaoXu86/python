# updateConf
updateConf works as simple database which holds the configuration from user input. 
Basic put/get/delete/list operations are supported. All information are encoded in AES.
Python2.x is required

updateConf.py -i Id  [-l] [--get] [--delete] [--put --name Name --passwd Password --tenant Tenant --url AuthUrl] [-c CfgFile] [--debug]\n\

example: 

$ updateConf.py -i 1 --put --name Admin --passwd Admin --tenant ECM --url https://10.147.32.171:5000/v2.0

$ updateConf.py -i 1 [--get] 

$ updateConf.py -i 1 --delete

$ updateConf.py -l

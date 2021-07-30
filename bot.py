#!/usr/bin/env python3

import bs4
import time
import requests
import configparser
# import argparse

config = configparser.ConfigParser()
config.read('config.ini')

# Send msg to Telegram


def sendMessage(token, text, chat_id, parse_mode=None):
    while True:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
        url = f'https://tg.nano.ac/bot{token}/sendMessage'
        params = {'text': text, 'chat_id': chat_id,
                  'disable_web_page_preview': True}
        if parse_mode != None:
            params['parse_mode'] = parse_mode
        try:
            response = requests.get(
                url=url, params=params, headers=headers, timeout=(5, 10))
            assert response.status_code == 200
            print(response.json())
            return response.json()['result']['message_id']
        except Exception as e:
            print(e)
            time.sleep(1)
            continue

# parser = argparse.ArgumentParser()
# parser.add_argument('--name', type=str, required=True)
# parser.add_argument('--password', type=str, required=True)
# args = parser.parse_args()


session = requests.session()

res = session.get('http://myhome.tsinghua.edu.cn')
res.encoding = 'gbk'
soup = bs4.BeautifulSoup(res.text, features='html.parser')
inputs = soup.find_all('input', recursive=True)

keys = [
    'net_Default_LoginCtrl1$lbtnLogin.x',
    '__VIEWSTATEGENERATOR',
    '__VIEWSTATE',
    'Home_Img_ActivityCtrl1$hfScript',
    'Home_Vote_InfoCtrl1$Repeater1$ctl01$hfID',
    'net_Default_LoginCtrl1$lbtnLogin.y',
    'net_Default_LoginCtrl1$txtUserName',
    'Home_Vote_InfoCtrl1$Repeater1$ctl01$rdolstSelect',
    'Home_Img_NewsCtrl1$hfJsImg',
    'net_Default_LoginCtrl1$txtSearch1',
    'net_Default_LoginCtrl1$txtUserPwd'
]

data = dict()

for key in keys:
    data[key] = None

for x in inputs:
    if x['name'] in set(keys):
        try:
            if data[x['name']] is None:
                data[x['name']] = x['value']
        except KeyError:
            pass

data['net_Default_LoginCtrl1$lbtnLogin.x'] = '22'
data['net_Default_LoginCtrl1$lbtnLogin.y'] = '12'
data['net_Default_LoginCtrl1$txtSearch1'] = ''
data['net_Default_LoginCtrl1$txtUserName'] = config['BOT']['name']
data['net_Default_LoginCtrl1$txtUserPwd'] = config['BOT']['password']

for k in data.keys():
    if data[k] == None:
        data[k] = 'dummyContent'
    data[k] = data[k].encode('gbk')

res = session.post('http://myhome.tsinghua.edu.cn/default.aspx', data=data)
res = session.get('http://myhome.tsinghua.edu.cn/Netweb_List/Netweb_Home_electricity_Detail.aspx')
res.encoding = 'gbk'
soup = bs4.BeautifulSoup(res.text, features='html.parser')
balance = soup.find('span', {'id': 'Netweb_Home_electricity_DetailCtrl1_lblele'}).text
balance = float(balance)

if balance < 20:
    text = f'Need to recharge the electricity bill. The electricity bill now is {balance} kilowatt.'
    sendMessage(config['BOT']['token'], text, config['BOT']['owner'])

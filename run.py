import http.cookiejar as HC
import logging
import re
import sys
import time

import requests
import schedule

from basic import (add_file_handler, archive, config, db, eprint, heartbeat,
                   logger, set_testmode)

# ============================

add_file_handler('./log/dorm.log')

HEARTBEAT_SERVER = 'https://alert.nano.ac/api/push/hKvmAorWb1?msg=OK&ping='

# session
session = requests.session()
session.cookies = HC.LWPCookieJar(filename='secret/myhome_cookies')
try:
    session.cookies.load(ignore_discard=True)
except:
    pass

# ============================


def login():
    logger.info('login...')
    resp = session.get('http://myhome.tsinghua.edu.cn/web_netweb_user/noLogin.aspx', timeout=(5, 10))

    data = {}
    data['__VIEWSTATE'] = re.findall(r'id="__VIEWSTATE" value="(.*?)"', resp.text)[0]
    data['__VIEWSTATEGENERATOR'] = re.findall(r'id="__VIEWSTATEGENERATOR" value="(.*?)"', resp.text)[0]
    data['net_Default_LoginCtrl1$txtUserName'] = config['MYHOME']['name']
    data['net_Default_LoginCtrl1$txtPassword'] = config['MYHOME']['password']
    data['net_Default_LoginCtrl1$btnLogin'] = ''

    resp = session.post('http://myhome.tsinghua.edu.cn/web_netweb_user/noLogin.aspx', data=data, timeout=(5, 10))
    session.cookies.save(ignore_discard=True, ignore_expires=True)


def run():
    try:
        resp = session.get('http://myhome.tsinghua.edu.cn/web_Netweb_List/Netweb_Home_electricity_Detail.aspx', timeout=(5, 10))
        balance = re.findall(r'<span id="Netweb_Home_electricity_DetailCtrl1_lblele"><font color="Red">(.*?)</font></span>', resp.text)
        if len(balance) == 0 or len(balance[0]) == 0:
            login()
            resp = session.get('http://myhome.tsinghua.edu.cn/web_Netweb_List/Netweb_Home_electricity_Detail.aspx', timeout=(5, 10))
            balance = re.findall(r'<span id="Netweb_Home_electricity_DetailCtrl1_lblele"><font color="Red">(.*?)</font></span>', resp.text)
        balance = float(balance[0])

        points = [
            {"measurement": "dorm", "tags": {"type": "electricity"}, "fields": {
                "balance": balance
            }},
        ]
        if not db.write_points(points, database='personal'):
            raise Exception('db.write_points failed')

        heartbeat(HEARTBEAT_SERVER)

    except requests.exceptions.RequestException:
        logger.debug('Network timeout')
    except Exception as e:
        eprint(e, logging.ERROR)


def test():
    set_testmode()
    run()
    exit()


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == '--test':
        test()
    try:
        run()
        schedule.every(8).hours.do(run)
        while True:
            schedule.run_pending()
            time.sleep(300)
    except Exception as e:
        eprint(e, logging.ERROR)
    except KeyboardInterrupt:
        pass

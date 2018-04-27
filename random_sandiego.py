import config
from scrapex import *
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
from datetime import datetime
from datetime import timedelta
from mysql_manage import *
from captcha2upload import CaptchaUpload
from models import DashboardLasd, DashboardNoResultOther, DashboardOtherHistory
# import captcha
from time import sleep
from lastname_list import last_name_list
from proxy_list import random_proxy
import json
import sys
import pytz
import csv
import os
import re
import random
import argparse
import string
import sys
import smtplib
from email.mime.text import MIMEText
from urllib import urlencode
import requests


reload(sys)
sys.setdefaultencoding('utf8')

lock = threading.Lock()

total_cnt = 0
first_name_list = []
no_result = []

DRIVER_SHORT_WAITING_SECONDS = 8
proxy_file_name = 'proxy_rotating.txt'

tz = pytz.timezone('America/Los_Angeles')
start_url = "http://apps.sdsheriff.net/wij/"


def show_exception_detail(e):
    print (e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("{}, {}, {}".format(exc_type, fname, str(exc_tb.tb_lineno)))


def prefix_letter(thread_index):
    return str(thread_index + 1)


def wait():
    sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))


def check_proxy_status(doc):
    if doc.status.code == 0 or doc.status.code == 403:
        return False

    return True


def get_proxy():
    proxy_ip, proxy_port, proxy_user, proxy_pass = random_proxy()
    proxies = {
      'http': 'http://{}:{}@{}:{}'.format(proxy_user, proxy_pass, proxy_ip, proxy_port),
      'https': 'http://{}:{}@{}:{}'.format(proxy_user, proxy_pass, proxy_ip, proxy_port),
    }
    return proxies


def delete_database():
    delete_date = (datetime.now(tz) + timedelta(days=-1)).strftime('%Y-%m-%d')
    print "Delete date = ", delete_date
    try:
        db.session.query(DashboardLasd).filter(
            DashboardLasd.ArrestDate < delete_date).delete()
        db.session.commit()
    except Exception as e:
        print e


def parse_website(thread_index):
    global first_name_list, no_result

    # Delete Old database history
    delete_database()

    for item in db.session.query(DashboardNoResultOther).filter(
                DashboardNoResultOther.Website == config.PREFIX_SANDIEGO):
        no_result.append(item.serialize())

    # get all name lists
    name_list = []
    for first_name in first_name_list:
        name_list.append(first_name_list[thread_index] + first_name)

    captcha_error_count = 0
    print "Captcha Error Count: ", config.ERROR_MAX_CAPTCHA_COUNT
    print captcha_error_count, config.ERROR_MAX_CAPTCHA_COUNT

    s = Scraper(
        use_cache=False,
        retries=3,
        timeout=30,
        proxy_file=proxy_file_name,
        one_proxy=True,
        log_file='logs/log{}.txt'.format(thread_index)
    )

    try:
        for ind, last_name in enumerate(name_list):
            for first_name in first_name_list:
                no_error = config.ERROR_NO_NONE
                try:
                    no_error = parse_root(thread_index, ind, last_name,
                                          first_name)
                except Exception as e:
                    show_exception_detail(e)
                    s.save(
                        ["error", str(e)],
                        "logs/san_error_{}.csv".format(thread_index)
                    )

                if no_error == config.ERROR_NO_CAPTCHA:
                    captcha_error_count += 1

                if captcha_error_count > config.ERROR_MAX_CAPTCHA_COUNT:
                    raise Exception("Captcha Service Error")

    except Exception as e:
        s1 = Scraper(
            use_cache=False,
            retries=3, timeout=30,
            proxy_file=proxy_file_name,
            one_proxy=True,
            log_file='logs/san_error_log{}.txt'.format(thread_index)
        )
        s1.logger.info(e)


def solve_captcha(s, image_url, session, thread_index):
    logger = s.logger
    imagefilepath = s.join_path(
        'images/san_captcha_{}.jpg'.format(thread_index))

    if os.path.exists(imagefilepath):
        os.remove(imagefilepath)

    r = session.get(image_url)
    # print "+++++++++++++Cookie++++++++++"
    # for c in r.cookies:
    #     print(c.name, c.value)

    if r.status_code == 200:
        with open(imagefilepath, 'wb') as f:
            for chunk in r:
                f.write(chunk)

    captcha = CaptchaUpload(config.CPATHA_API_KEY)
    first_captcha_code = captcha.solve(imagefilepath)
    if str(first_captcha_code) == "1":
        logger.info("Captcha Service Error")
        return config.ERROR_NO_CAPTCHA

    logger.info('{} 1st_captcha2 -> {}'.format(
        prefix_letter(thread_index), first_captcha_code))

    wait()
    return first_captcha_code


def is_error(value):
    return value == config.ERROR_NO_CAPTCHA or \
           value == config.ERROR_NO_PROXY or \
           value == config.ERROR_NO_NOT_RESULT_FOUND


def parse_root_url(s, thread_index, ind, lastname, firstname):
    logger = s.logger

    url = start_url + "WijAList.aspx?LastName={}&FirstName={}".format(
        lastname, firstname)
    logger.info("{} Loading First URL -> {}".format(
        prefix_letter(thread_index), url))

    session = requests.session()
    res = session.get(url, proxies=get_proxy())
    # print "+++++++++++++Cookie++++++++++"
    # for c in res.cookies:
    #     print(c.name, c.value)

    if res.status_code != 200:
        logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
        return config.ERROR_NO_PROXY

    doc = Doc(html=res.text)
    img_url = start_url + doc.x('//img[@id="ctl00_Main_Image1"]/@src')
    # print "++++++++++++++"
    # print img_url
    if img_url != "":
        first_captcha_code = solve_captcha(s, img_url, session, thread_index)
        if is_error(first_captcha_code) is True:
            logger.info("{} Captcha Error".format(prefix_letter(thread_index)))
            return config.ERROR_NO_CAPTCHA, session

        __LASTFOCUS = doc.x("//input[@id='__LASTFOCUS']/@value")
        __VIEWSTATE = doc.x("//input[@id='__VIEWSTATE']/@value")
        __VIEWSTATEGENERATOR = doc.x("//input[@id='__VIEWSTATEGENERATOR']/@value")
        __EVENTTARGET = doc.x("//input[@id='__EVENTTARGET']/@value")
        __EVENTARGUMENT = doc.x("//input[@id='__EVENTARGUMENT']/@value")
        __EVENTVALIDATION = doc.x("//input[@id='__EVENTVALIDATION']/@value")
        ctl00_Main_btnCaptcha = doc.x("//input[@id='ctl00_Main_btnCaptcha']/@value")

        payload = {
            "__LASTFOCUS":              __LASTFOCUS,
            "__VIEWSTATE":              __VIEWSTATE,
            "__VIEWSTATEGENERATOR":     __VIEWSTATEGENERATOR,
            "__EVENTTARGET":            __EVENTTARGET,
            "__EVENTARGUMENT":          __EVENTARGUMENT,
            "__EVENTVALIDATION":        __EVENTVALIDATION,
            "ctl00$Main$txtimgcode":    first_captcha_code,
            "ctl00$Main$btnCaptcha":    ctl00_Main_btnCaptcha
        }

        urlcodeStr = urlencode(payload)
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        res = None
        try:
            res = session.post(
                url, data=urlcodeStr, proxies=get_proxy(), headers=headers)
        except Exception as e:
            logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
            return config.ERROR_NO_PROXY, session

        doc = Doc(html=res.text)
        if res.status_code != 200:
            logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
            return config.ERROR_NO_PROXY, session

        return doc, session


def parse_root(thread_index, ind, lastname, firstname):
    print "+++++++++++++++++START++++++++++++++++++++"

    for no_item in no_result:
        if no_item["lastname"] == lastname and \
           no_item["firstname"] == firstname and \
           no_item["nocount"] > config.NO_MAX_COUNT:
                print("No found Name: ", lastname, firstname)

    s = Scraper(
        use_cache=False,
        retries=3,
        timeout=30,
        proxy_file=proxy_file_name,
        one_proxy=True,
        log_file='logs/log_los{}.txt'.format(thread_index)
    )

    logger = s.logger

    currentdate = datetime.now(tz).strftime('%Y-%m-%d')
    currenttime = datetime.now(tz).strftime('%H:%M')
    logger.info("{} Current Date & Time: {} , {}".format(
        prefix_letter(thread_index), currentdate, currenttime))

    logger.info("{} Search Name: {} , {}".format(
        prefix_letter(thread_index), lastname, firstname))

    doc, session = parse_root_url(s, thread_index, ind, lastname, firstname)
    if is_error(doc) is not True:
        info_list = doc.q("//table[@id='ctl00_Main_grdPeople']//tr")
        print "Found = ", len(info_list)

        if len(info_list) == 0:
            no_history = db.session.query(DashboardNoResultOther).filter(
                DashboardNoResultOther.Website == config.PREFIX_SANDIEGO,
                DashboardNoResultOther.LastName == lastname,
                DashboardNoResultOther.FirstLetter == firstname
                ).first()

            if no_history is not None:
                no_history.NoCount = no_history.NoCount + 1
                try:
                    db.session.commit()
                except Exception as e:
                    logger.info(e)
            else:
                no_other = DashboardNoResultOther(
                    s_lastname=lastname,
                    s_firstletter=firstname,
                    s_website=config.PREFIX_SANDIEGO,
                    s_nocount=1
                )

                try:
                    db.session.add(no_other)
                    db.session.commit()
                except Exception as e:
                    logger.info(e)

            return

        for info_item in info_list:
            href = start_url + info_item.x("td[not(@title)]/a/@href")
            l_name = info_item.x("td[not(@title)]/a/text()")

            if l_name != "":
                f_name = info_item.x("td[2]/text()")
                m_name = info_item.x("td[3]/text()")
                birthday = info_item.x("td[6]/text()")

                booking = db.session.query(DashboardLasd).filter(
                    DashboardLasd.BookingNo.contains(config.PREFIX_SANDIEGO),
                    DashboardLasd.LastName == l_name,
                    DashboardLasd.FirstName == f_name,
                    DashboardLasd.MiddleName == m_name,
                    DashboardLasd.Birthday == birthday).first()

                history = db.session.query(DashboardOtherHistory).filter(
                    DashboardOtherHistory.LastName == l_name,
                    DashboardOtherHistory.FirstName == f_name,
                    DashboardOtherHistory.MiddleName == m_name,
                    DashboardOtherHistory.Birthday == birthday,
                    DashboardOtherHistory.Website == config.PREFIX_SANDIEGO).first()

                if (history is None) and (booking is None):
                    print "+++++++++++++++Not Saved+++++++++++++", l_name, f_name, m_name
                    ret = parse_booking(s, thread_index, ind, currentdate,
                                  currenttime, lastname, firstname, href)

                    if is_error(ret) is True:
                        return ret
                else:
                    if history is not None:
                        logger.info('{} Increase Duplication -> {}, {}, {}'.format(
                            prefix_letter(thread_index), l_name, f_name, m_name))
                        history.Duplication = history.Duplication + 1
                        history.CapturedDate = currentdate
                        history.CapturedTime = currenttime

                        try:
                            db.session.commit()
                        except Exception as e:
                            logger.info(e)

                    if history is None:
                        logger.info('{} Saved Booking Information with existing Booking -> {}, {}, {}'.format(
                            prefix_letter(thread_index), l_name, f_name, m_name))

                        booking_history = DashboardOtherHistory(
                            s_middlename=m_name,
                            s_lastname=l_name,
                            s_firstname=f_name,
                            s_captureddate=currentdate,
                            s_capturedtime=currenttime,
                            s_duplication=0,
                            s_birthday=birthday,
                            s_website=config.PREFIX_SANDIEGO,
                            s_booking_no=""
                        )

                        try:
                            db.session.add(booking_history)
                            db.session.commit()
                        except Exception as e:
                            logger.info(e)

        return config.ERROR_NO_NONE
    else:
        return doc


def parse_detail(s, doc, thread_index, ind, currentdate, currenttime,
                 s_lastname, s_firstname):
    logger = s.logger

    BookingNo = doc.x("//span[@id='ctl00_Main_lblBookingNbr']/text()")

    logger.info("{} Booking No in detail: {}".format(
        prefix_letter(thread_index), BookingNo))

    if BookingNo == "":
        return

    LastName = doc.x("//span[@id='ctl00_Main_lblLast']/text()")
    FirstName = doc.x("//span[@id='ctl00_Main_lblFirst']/text()")
    MiddleName = doc.x("//span[@id='ctl00_Main_lblMiddle']/text()")
    Birthday = doc.x("//span[@id='ctl00_Main_lblDOB']/text()")
    Age = doc.x("//span[@id='ctl00_Main_lblAge']/text()")
    Sex = doc.x("//span[@id='ctl00_Main_lblSex']/text()")
    Race = doc.x("//span[@id='ctl00_Main_lblRace']/text()")
    Hair = doc.x("//span[@id='ctl00_Main_lblHair']/text()")
    Eyes = doc.x("//span[@id='ctl00_Main_lblEyes']/text()")
    Height = doc.x("//span[@id='ctl00_Main_lblHeight']/text()")
    Weight = doc.x("//span[@id='ctl00_Main_lblWeight']/text()")
    CapturedDate = currentdate
    CapturedTime = currenttime
    ArrestAgency = doc.x("//span[@id='ctl00_Main_lblArrestAgency']/text()")
    AgencyDescription = ""
    DateBooked = doc.x("//span[@id='ctl00_Main_lblDateBooked']/text()")
    TimeBooked = doc.x("//span[@id='ctl00_Main_lblTimeBooked']/text()")
    ArrestDateStr = DateBooked.split('/')
    y = ArrestDateStr.pop()
    d = ArrestDateStr.pop()
    m = ArrestDateStr.pop()
    ArrestDate = y+"-"+m+"-"+d
    ArrestTime = TimeBooked[:5]

    BookingLocation = ""
    LocationDescription = ""
    TotalBailAmount = ""
    TotalHoldBailAmount = ""
    GrandTotal = ""
    HousingLocation = doc.x("//span[@id='ctl00_Main_lblArea']/text()")
    PermanentHousingAssignedDate = ""
    AssignedTime = ""

    VisitorStatus = ""
    Facility = doc.x("//span[@id='ctl00_Main_lblFacility']/text()")
    Address = doc.x("//span[@id='ctl00_Main_lblFacAddr']/text()")
    City = doc.x("//span[@id='ctl00_Main_lblCity']/text()")

    today = datetime.now(tz).strftime('%Y-%m-%d')
    yest = (datetime.now(tz) + timedelta(days=-1)).strftime('%Y-%m-%d')

    print "************************************************************"
    print today, yest
    print "Arrest = ", ArrestDate
    print "************************************************************"
    if (today == ArrestDate) or (yest == ArrestDate):
        booking_no = BookingNo + config.PREFIX_SANDIEGO

        booking = DashboardLasd(
            s_bookingno=booking_no,
            s_lastname=LastName,
            s_firstname=FirstName,
            s_middlename=MiddleName,
            s_birthday=Birthday,
            s_age=Age,
            s_sex=Sex,
            s_race=Race,
            s_hair=Hair,
            s_eyes=Eyes,
            s_height=Height,
            s_weight=Weight,
            s_arrestdate=ArrestDate,
            s_arresttime=ArrestTime,
            s_captureddate=CapturedDate,
            s_capturedtime=CapturedTime,
            s_arrestagency=ArrestAgency,
            s_agencydescription=AgencyDescription,
            s_datebooked=DateBooked,
            s_timebooked=TimeBooked,
            s_bookinglocation=BookingLocation,
            s_locationdescription=LocationDescription,
            s_totalbailamount=TotalBailAmount,
            s_totalholdbailamount=TotalHoldBailAmount,
            s_grandtotal=GrandTotal,
            s_housinglocation=HousingLocation,
            s_permanenthousingassigneddate=PermanentHousingAssignedDate,
            s_assignedtime=AssignedTime,
            s_visitorstatus=VisitorStatus,
            s_facility=Facility,
            s_address=Address,
            s_city=City,
            s_jail=0
        )

        try:
            db.session.add(booking)
            db.session.commit()
        except Exception as e:
            logger.info(e)

        logger.info('+++++++{} Data was saved {}, {}, {}, {}'.format(
            prefix_letter(thread_index), BookingNo, ArrestDate, LastName, FirstName))
    else:
        logger.info('{} Arrest Date is {}'.format(prefix_letter(thread_index), ArrestDate))

    booking_history = DashboardOtherHistory(
        s_middlename=MiddleName,
        s_lastname=LastName,
        s_firstname=FirstName,
        s_captureddate=currentdate,
        s_capturedtime=currenttime,
        s_duplication=0,
        s_birthday=Birthday,
        s_website=config.PREFIX_SANDIEGO,
        s_booking_no=BookingNo
    )

    try:
        db.session.add(booking_history)
        db.session.commit()
    except Exception as e:
        logger.info(e)

    try:
        db.session.query(DashboardNoResultOther).filter(
            DashboardNoResultOther.Website == config.PREFIX_SANDIEGO,
            DashboardNoResultOther.LastName == s_lastname,
            DashboardNoResultOther.FirstLetter == s_firstname
            ).delete()
        db.session.commit()
    except Exception as e:
        print e

    return config.ERROR_NO_NONE


def parse_booking(s, thread_index, ind, currentdate, currenttime,
                  lastname, firstname, url):
    logger = s.logger
    doc, session = parse_root_url(s, thread_index, ind, lastname, firstname)
    if is_error(doc) is not True:
        info_list = doc.q("//table[@id='ctl00_Main_grdPeople']//tr")
        print "Found = ", len(info_list)

        res = session.get(url, proxies=get_proxy())
        if res.status_code != 200:
            logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
            return config.ERROR_NO_PROXY

        doc = Doc(html=res.text)
        parse_detail(s, doc, thread_index, ind, currentdate, currenttime,
                     lastname, firstname)

        return config.ERROR_NO_NONE
    else:
        return doc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-i', '--index', type=int, required=True,
                        help='Index of letter from 10 ~ 36')

    name_str = "abcdefghijklmnopqrstuvwxyz"
    first_name_list = list(name_str)

    args = parser.parse_args()
    index_number = args.index - 10

    if index_number >= 0 and index_number < 36:
        parse_website(index_number)

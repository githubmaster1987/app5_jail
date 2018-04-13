import config
from scrapex import *
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
from datetime import datetime
from mysql_manage import *
from models import DashboardLasd, DashboardJailHistory, DashboardNoResult, DashboardVineName
#from captcha2upload import CaptchaUpload
import captcha
from time import sleep
import sys 
import pytz
import csv
import os
import re
import random
import argparse
import string
import sys
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText


reload(sys)  
sys.setdefaultencoding('utf8')

lock = threading.Lock()

total_cnt = 0
first_url = "http://app5.lasd.org/iic/"
second_url = "http://app5.lasd.org/iic/iverifysearch.cfm"

list_to_be_scraped = {}

DRIVER_SHORT_WAITING_SECONDS = 8
# proxy_file_name = 'proxy_chris.txt'
proxy_file_name = 'proxy_rotating.txt'
success_filename = "name_succss.csv"
miss_filename = "name_miss.csv"
nofound_filename = "name_nofound.csv"
outofdate_filename = "name_outofdate.csv"


global_s = Scraper(use_cache=False, retries=3, timeout=30, proxy_file=proxy_file_name, one_proxy=True,
        log_file='logs/log_global.txt')

VALUE_WEBSITE_JAIL = 0
VALUE_WEBSITE_VINE = 2
VALUE_CHECK_MISSING = 1

def prefix_letter(thread_index):
    return str(thread_index + 1)


def wait():
    sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))


def check_proxy_status(doc):
    if doc.status.code != 200:
        return False
    return True


def parse_first_webpage(thread_index, ind, lastname, firstname, checkmiss):
    print "+++++++++++++++++++++++++++++++++++++++++++++++++++START+++++++++++++++++++++++++++++++++++++++++++++++++"

    # no_result = db.session.query(DashboardNoResult).filter_by(LastName=lastname, FirstLetter=firstname).first()
    # if no_result is not None:
    #     print ("{} No Result in Last Name: {}, First Name: {}".format(prefix_letter(thread_index), lastname, firstname))
    #     save_names(lastname, firstname, nofound_filename)
    #     save_names(lastname, firstname, success_filename, "No Found")
    #     return

    tz = pytz.timezone('America/Los_Angeles')

    s = Scraper(use_cache=False, retries=3, timeout=30, proxy_file=proxy_file_name, one_proxy=True, log_file='logs/log{}.txt'.format(thread_index))

    logger = s.logger
    logger.info("{} Loading First URL -> {}".format(prefix_letter(thread_index), first_url))

    doc = s.load(first_url)
    if check_proxy_status(doc) == False:
        logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
        return config.ERROR_NO_PROXY

    currentdate = datetime.now(tz).strftime('%Y-%m-%d')
    currenttime = datetime.now(tz).strftime('%H:%M')
    logger.info("{} Current Date & Time: {} , {}".format(prefix_letter(thread_index), currentdate, currenttime))

    formdata = {
        'method': 'post',
        'currentdate': currentdate,
        'currenttime': currenttime,
        'startdate': '03/05/2014',
        'starttime': '08 : 00',
        'enddate': '03/05/2014',
        'endtime': '12 : 00',
        'last_name': str(lastname),
        'first_name': str(firstname),
        'middle_name': '',
        'dob': '',
        'search': 'Search'
    }

    logger.info("{} Name Index: {},  Last Name: {}, First Name: {}".format(prefix_letter(thread_index), ind, lastname, firstname))

    doc = s.load(second_url, post=formdata)
    if check_proxy_status(doc) is False:
        logger.info("{} Proxy Error".format(prefix_letter(thread_index)))
        return config.ERROR_NO_PROXY

    img_url = doc.x('//img[@alt="Captcha image"]/@src')

    if img_url != "":
        ckey = doc.x('//input[@name="ckey"]/@value')
        imagefilepath = s.join_path('images/captcha_{}.jpg'.format(thread_index))
        if os.path.exists(imagefilepath):
            os.remove(imagefilepath)

        u = s.client.opener.open(img_url)
        f = open(imagefilepath, 'wb')
        block_sz = 8192
        while True:
            buf = u.read(block_sz)
            if not buf:
                break
            f.write(buf)
        f.close()

        #captcha = CaptchaUpload(config.captcha_api_key)
        first_captcha_code = captcha.solve(imagefilepath)
        if str(first_captcha_code) == "1":
            logger.info("Captcha Service Error")
            # return config.ERROR_NO_CAPTCHA

        captcha_code_old = first_captcha_code
        logger.info('{} 1st_captcha2 -> {}'.format(prefix_letter(thread_index), first_captcha_code))

        wait()
        return parse_second_webpage(s, thread_index, first_captcha_code, currentdate, currenttime, lastname, firstname, checkmiss)

def captcha_retry(doc, s, thread_index, currentdate, currenttime, lastname, firstname, url, merge_headers, old_captcha_code):
    logger = s.logger
    img_url = doc.x('//img[@alt="Captcha image"]/@src')
    #logger.info('{} img_url -> {}'.format(prefix_letter(thread_index), img_url)
    # print "+++++++++++++++++++++++++"
    # print img_url
    # print "+++++++++++++++++++++++++"

    if merge_headers == True:
        old_code = old_captcha_code

    catpcha_try_count = 0
    while img_url != "":
        if catpcha_try_count > config.captcha_max_tries:
            print "--------------------Captcha tries reached as max value---------------"
            return doc, config.ERROR_NO_CAPTCHA

        catpcha_try_count += 1
        print "*****************************************"
        
        if merge_headers == True:
            print "Try to solve captcha in 2nd step:",  img_url
        else:
            print "Try to solve captcha in 1st step:",  img_url

        ckey = doc.x('//input[@name="ckey"]/@value')
        #logger.info('{} ckey -> {}, thread-> {}'.format(prefix_letter(thread_index), ckey, thread_index)
        
        imagefilepath = s.join_path('images/captcha_{}.jpg'.format(thread_index))
        
        if os.path.exists(imagefilepath):
            os.remove(imagefilepath)

        u = s.client.opener.open(img_url)
        f = open(imagefilepath, 'wb')
        block_sz = 8192
        while True:
            buf = u.read(block_sz)
            if not buf:
                break
            f.write(buf)
        f.close()
        
        #captcha = CaptchaUpload(config.captcha_api_key)
        first_captcha_code = captcha.solve(imagefilepath)
        if str(first_captcha_code) == "1":
            logger.info("Captcha Service Error")
            # return config.ERROR_NO_CAPTCHA

        # global_export_filename = "retry/retry_{}_{}_{}.csv".format(currentdate, currenttime, thread_index)

        # global_s.save([
        #     "Current Date", currentdate,
        #     "Current Time", currenttime,
        #     "Captcha", first_captcha_code,
        #     ], global_export_filename)

        captcha_code_old = first_captcha_code

        if merge_headers == True:
            logger.info('{} 2nd_captcha2_code -> {}'.format(prefix_letter(thread_index), first_captcha_code))
        else:
            logger.info('{} 1st_captcha2_code -> {}'.format(prefix_letter(thread_index), first_captcha_code))
        
        wait()

        if merge_headers == True:
            
            formdata = {
                "ckey" : old_code,
                "key" : first_captcha_code,
                "submit" : "Submit"
            }
            
            headers = {
                "Host" : "app4.lasd.org",
                "User-Agent" : "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0",
                "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language" : "en-US,en;q=0.5",
                "Accept-Encoding" : "gzip, deflate, br",
                "Referer" : url,
                "Upgrade-Insecure-Requests": "1"
            }
            doc = s.load(url, post=formdata, headers=headers, merge_headers = True)
        else:
            formdata = {
                "key" : first_captcha_code,
                "ckey" : first_captcha_code,
                "submit" : "Submit"
            }
            doc = s.load(second_url, post=formdata)

        img_url = doc.x('//img[@alt="Captcha image"]/@src')

        old_code = first_captcha_code
        # return parse_second_webpage(s, thread_index, first_captcha_code, currentdate, currenttime, lastname, firstname)
    if merge_headers == True:
        print "********2nd Step : Solved Captcha Successfully**********"
    else:
        print "********1st Step : Solved Captcha Successfully**********"
    return doc, config.ERROR_NO_NONE

def parse_second_webpage(sc_obj, thread_index, captcha_code, currentdate, currenttime, lastname, first_letter, checkmiss):
    logger = sc_obj.logger
    
    formdata = {
        "key" : captcha_code,
        "ckey" : captcha_code,
        "submit" : "Submit"
    }

    doc = sc_obj.load(second_url, post=formdata)
    
    #retry captcha if failed

    doc, captcha_error = captcha_retry(doc, sc_obj, thread_index, currentdate, currenttime, lastname, first_letter, second_url, False, "")
    if captcha_error == config.ERROR_NO_CAPTCHA:
        print "Captcha Error"
        return config.ERROR_NO_CAPTCHA
        
    if check_proxy_status(doc) == False:
        logger.info("{} Proxy Error of function parse_second_webpage".format(prefix_letter(thread_index)))
        return config.ERROR_NO_PROXY

    error_div = doc.x("//form[@name='inm_lst']/center/strong/font//text()").strip()
    print "Error Div=", error_div
    if "No records match your search criteria." in error_div:
        no_result_history = db.session.query(DashboardNoResult).filter_by(FirstLetter=first_letter, LastName=lastname).first()

        if no_result_history is None:
            booking_no_result =  DashboardNoResult(
                    s_lastname = lastname,
                    s_firstletter = first_letter,
                )

            try:
                db.session.add(booking_no_result)
                db.session.commit()
            except Exception as e:
                logger.info(e)

        save_names(lastname, first_letter, nofound_filename)
        # save_names(lastname, first_letter, success_filename, "No Found")

        return config.ERROR_NO_NONE

    res = doc.q("//table[@class='Grid']//tr/td/a")
    print "Listing Len = ", len(res)
    if len(res) == 0:
        logger.info("{} Result does not exist".format(prefix_letter(thread_index)))
        return config.ERROR_NO_NOT_RESULT_FOUND

    obj_key = lastname + "," + first_letter
    obj_booking_no = list_to_be_scraped[obj_key]

    print "List Len=", len(res), " Key =", obj_key, "Booking No=", obj_booking_no

    booking_no = ""
    booking_url = ""
    if checkmiss == VALUE_WEBSITE_VINE:
        try:
            booking_no = doc.q("//table[@class='Grid']//tr/td/a[contains(text(), '" + obj_booking_no +"')]")[0].x('text()')
            booking_url = doc.q("//table[@class='Grid']//tr/td/a[contains(text(), '" + obj_booking_no +"')]")[0].x('@href')
        except:
            
            for t in doc.q("//table[@class='Grid']//tr"):
                td_list = []

                for qt in t.q(".//td"):
                    td_list.append(qt.x("text()").strip().lower())

                if len(td_list) > 3:
                    if (lastname.lower() == td_list[1]) and (first_letter.lower() == td_list[2]):
                        booking_no = t.x("td/a/text()").strip()
                        booking_url = t.x("td/a/@href").strip()

                if booking_no != "":
                    break
    else:
        booking_no = doc.q("//table[@class='Grid']//tr/td/a")[-1].x('text()')
        booking_url = doc.q("//table[@class='Grid']//tr/td/a")[-1].x('@href')

    if (obj_booking_no != "") and (booking_no == ""):
        print "+++++++++++++++++++++++++++++++"
        print "----------------> VINE NAME = ", obj_key, " BOOKING NO = ", obj_booking_no, " NOT FOUND"
        print "+++++++++++++++++++++++++++++++"
        return

    form_action_url = doc.x("//form/@action")
    captchaText = doc.x("//form[@name='inm_lst']/input[@name='captchaText']/@value")
    comment1 = doc.x("//form[@name='inm_lst']/input[@name='comment1']/@value")

    logger.info('{} booking_no -> {}'.format(prefix_letter(thread_index), booking_no))

    tmp = booking_url.split("javascript:getsupport('", 1)
    
    rtmp = tmp[1].split("')", 1)
    
    bookinguid = rtmp[0]
    
    history = db.session.query(DashboardJailHistory).filter(DashboardJailHistory.BookingNo.contains(booking_no)).first()
    booking = db.session.query(DashboardLasd).filter(DashboardLasd.BookingNo.contains(booking_no)).first()

    if (history is None) and (booking is None):

        formdata = {
            "captchaText" : captchaText,
            "comment1" : comment1,
            "supporttype" : bookinguid,
            "bkgno" : bookinguid,
        }
        
        wait()
        return parse_detail_page(sc_obj, thread_index, form_action_url, formdata, captcha_code, currentdate, currenttime, lastname, first_letter)
    else:
        if history is not None:
            logger.info('{} Increase Duplication -> {}'.format(prefix_letter(thread_index), booking_no))
            history.Duplication = history.Duplication + 1
            history.CapturedDate = currentdate
            history.CapturedTime = currenttime

            try:
                db.session.commit()
            except Exception as e:
                logger.info(e)

            # Delete VINE Info if exist in History Table
            obj_key = lastname + "," + first_letter
            obj_booking_no = list_to_be_scraped[obj_key]

            if (obj_booking_no != ""):
                print "+++++++++++++++++++++++++++"
                print "-----------------> Delete VINE NAME = ", obj_key, " BOOKING NO = ", obj_booking_no
                print "+++++++++++++++++++++++++++"

                try:
                    db.session.query(DashboardVineName).filter(DashboardVineName.BookingNo == obj_booking_no).delete()
                    db.session.commit()
                except Exception as e:
                    print e
        
        if history is None:
            logger.info('{} Saved Booking Information with existing Booking -> {}'.format(prefix_letter(thread_index), booking_no))
            booking_history =  DashboardJailHistory(
                s_bookingno = booking.BookingNo,
                s_lastname = booking.LastName,
                s_firstname = booking.FirstName,
                s_captureddate = currentdate,
                s_capturedtime = currenttime,
                s_duplication = 0,
                s_arrestdate = booking.ArrestDate
            )

            try:
                db.session.add(booking_history)
                db.session.commit()
            except Exception as e:
                logger.info(e)

        save_names(lastname, first_letter, success_filename, "Exist", booking_no)
        logger.info('{} booking_no exist -> {}'.format(prefix_letter(thread_index), booking_no))

def parse_detail_page(sc_obj, thread_index, form_action_url, formdata, old_captcha_code, currentdate, currenttime, lastname, first_letter) :
    logger = sc_obj.logger
    
    doc = sc_obj.load(form_action_url, post=formdata)
    if check_proxy_status(doc) == False:
        logger.info("{} Proxy Error of function parse_detail_page".format(prefix_letter(thread_index)))
        return config.ERROR_NO_PROXY

    img_url = doc.x('//img[@alt="Captcha image"]/@src')

    if img_url != "":
        imagefilepath = sc_obj.join_path('images/captcha_{}.jpg'.format(thread_index))

        if os.path.exists(imagefilepath):
            os.remove(imagefilepath)

        u = sc_obj.client.opener.open(img_url)
        f = open(imagefilepath, 'wb')
        block_sz = 8192
        while True:
            buf = u.read(block_sz)
            if not buf:
                break
            f.write(buf)
        f.close()

        #captcha = CaptchaUpload(config.captcha_api_key)
        second_captcha_code = captcha.solve(imagefilepath)
        if str(second_captcha_code) == "1":
            logger.info("Captcha Service Error")
            return config.ERROR_NO_CAPTCHA

        logger.info('{} 2nd_captcha2_code -> {}'.format(prefix_letter(thread_index), second_captcha_code))

        formdata = {
            "ckey" : old_captcha_code,
            "key" : second_captcha_code,
            "submit" : "Submit"
        }
        
        headers = {
            "Host" : "app4.lasd.org",
            "User-Agent" : "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language" : "en-US,en;q=0.5",
            "Accept-Encoding" : "gzip, deflate, br",
            "Referer" : form_action_url,
            "Upgrade-Insecure-Requests": "1"
        }
        
        doc = sc_obj.load(form_action_url, post=formdata, headers=headers, merge_headers = True)

        doc, captcha_error = captcha_retry(doc, sc_obj, thread_index, currentdate, currenttime, lastname, first_letter, form_action_url, True, old_captcha_code)
        if captcha_error == config.ERROR_NO_CAPTCHA:
            print "Captcha Error"
            return config.ERROR_NO_CAPTCHA

        
        if check_proxy_status(doc) == False:
            logger.info("{} Proxy Error of function parse_detail_page".format(prefix_letter(thread_index)))
            return config.ERROR_NO_PROXY

        logger.info('{} Captcha Code: Old -> {}, New -> {}'.format(prefix_letter(thread_index), old_captcha_code, second_captcha_code))
        logger.info('{} form_action_url -> {}'.format(prefix_letter(thread_index), form_action_url))

        try:
            booking_no_cointainer = doc.q("//tr[@class='Row2']/td")
            booking_no_cointainer = ''.join([item.html() for item in booking_no_cointainer])

            BookingNo = re.search('Booking No.: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            LastName = re.search('Last Name: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            FirstName = re.search('First Name: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            MiddleName = re.search('Middle Name: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Birthday = re.search('Date Of Birth: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            
            Age = re.search('Age: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Sex = re.search('Sex: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Race = re.search('Race: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Hair = re.search('Hair: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Eyes = re.search('Eyes: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Height = re.search('Height: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()
            Weight = re.search('Weight: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(booking_no_cointainer), re.M|re.I|re.S).group(2).strip()

            contents = doc.q("//tr[@class='Caption2']/td[@align='center']")
            contents = ''.join([item.html() for item in contents])
            
            try:
                ArrestDateStr=re.search('Arrest Date: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', contents, re.M|re.I|re.S).group(2).strip()
            except Exception as e:
                print '*******************************'
                print e
                print contents
                print BookingNo
                print "LEN =", len(doc.q("//tr[@class='Caption2']"))
                print '*******************************'

            ArrestDateStr=re.search('Arrest Date: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', contents, re.M|re.I|re.S).group(2).strip()
            ArrestDateStr = ArrestDateStr.split('/')
            y = ArrestDateStr.pop()
            d = ArrestDateStr.pop()
            m = ArrestDateStr.pop()
            ArrestDate = y+"-"+m+"-"+d
            ArrestTimeStr=re.search('Arrest Time: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            ArrestTime = ArrestTimeStr[:2]+":"+ArrestTimeStr[2:]
            CapturedDate=currentdate
            CapturedTime=currenttime
            ArrestAgency=re.search('Arrest Agency: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            AgencyDescription=re.search('Agency Description: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            DateBooked=re.search('Date Booked: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            TimeBooked=re.search('Time Booked: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            # DateBooked=currentdate
            # TimeBooked=currenttime
            BookingLocation=re.search('Booking Location: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            LocationDescription=re.search('Location Description: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            TotalBailAmount=re.search('Total Bail Amount: (\<strong\>)?([.\,\w\s]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            TotalHoldBailAmount=re.search('Total Hold Bail Amount: (\<strong\>)?([.\,\w\s]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            GrandTotal=re.search('Grand Total: (\<strong\>)?([.\,\w\s]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            HousingLocation=re.search('Housing Location: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            PermanentHousingAssignedDate=re.search('Permanent Housing Assigned Date: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            AssignedTime=re.search('Assigned Time: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            # PermanentHousingAssignedDate=currentdate
            # AssignedTime=currenttime
            
            VisitorStatus=re.search('Visitor Status: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            Facility=re.search('Facility: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            Address=re.search('Address: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()
            City=re.search('City: (\<strong\>)?([^\<.*]*)\<[\/]?strong[\/]?\>', str(contents), re.M|re.I|re.S).group(2).strip()

            la_tz = pytz.timezone('America/Los_Angeles')

            today = datetime.now(la_tz).strftime('%Y-%m-%d')
            yesterday = (datetime.now(la_tz) + timedelta(days=-1)).strftime('%Y-%m-%d')

            print "************************************************************"
            print today, yesterday
            print "Arrest = ", ArrestDate
            print "************************************************************"
            
            obj_key = lastname + "," + first_letter
            obj_booking_no = list_to_be_scraped[obj_key]

            booking_no = BookingNo
            if (obj_booking_no != ""):
                booking_no += config.PREFIX_VINE

            if (today == ArrestDate) or (yesterday == ArrestDate):
            # if True:
                booking = DashboardLasd(
                    s_bookingno= booking_no,
                    s_lastname= LastName,
                    s_firstname= FirstName,
                    s_middlename= MiddleName,
                    s_birthday= Birthday,
                    s_age= Age,
                    s_sex= Sex,
                    s_race= Race,
                    s_hair= Hair,
                    s_eyes= Eyes,
                    s_height= Height,
                    s_weight= Weight,
                    s_arrestdate= ArrestDate,
                    s_arresttime= ArrestTime,
                    s_captureddate= CapturedDate,
                    s_capturedtime= CapturedTime,
                    s_arrestagency= ArrestAgency,
                    s_agencydescription= AgencyDescription,
                    s_datebooked= DateBooked,
                    s_timebooked= TimeBooked,
                    s_bookinglocation= BookingLocation,
                    s_locationdescription= LocationDescription,
                    s_totalbailamount= TotalBailAmount,
                    s_totalholdbailamount= TotalHoldBailAmount,
                    s_grandtotal= GrandTotal,
                    s_housinglocation= HousingLocation,
                    s_permanenthousingassigneddate= PermanentHousingAssignedDate,
                    s_assignedtime= AssignedTime,
                    s_visitorstatus= VisitorStatus,
                    s_facility= Facility,
                    s_address= Address,
                    s_city=City,
                    s_jail=1
                )

                try:
                    db.session.add(booking)
                    db.session.commit()

                    if float(GrandTotal.replace(",", "")) >= 20000:
                        send_notify_email(booking)

                except Exception as e:
                    logger.info(e)


                logger.info('+++++++{} Data was saved {}, {}, {}, {}'.format(prefix_letter(thread_index), BookingNo, ArrestDate, LastName, FirstName))
                save_names(lastname, first_letter, success_filename, "", booking_no, ArrestDate)
            else:
                logger.info('{} Arrest Date is {}, {}'.format(prefix_letter(thread_index), ArrestDate, booking_no))
                save_names(lastname, first_letter, outofdate_filename, "", booking_no, ArrestDate)
                save_names(lastname, first_letter, success_filename, "Out Of Date", booking_no, ArrestDate)

            booking_history =  DashboardJailHistory(
                s_bookingno = BookingNo,
                s_lastname = LastName,
                s_firstname = FirstName,
                s_captureddate = CapturedDate,
                s_capturedtime = CapturedTime,
                s_duplication = 0,
                s_arrestdate = ArrestDate
            )

            try:
                db.session.add(booking_history)
                db.session.commit()
            except Exception as e:
                logger.info(e)

            try:
                obj_key = lastname + "," + first_letter
                obj_booking_no = list_to_be_scraped[obj_key]

                print "Delete VINE Booking No for ", obj_booking_no
                db.session.query(DashboardVineName).filter(DashboardVineName.BookingNo == obj_booking_no).delete()
                db.session.commit()
            except Exception as e:
                print e
                
        except Exception as e:
            logger.info(e)
            show_exception_detail(e)
            pass   

    return config.ERROR_NO_NONE

def show_exception_detail(e):
    print (e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("{}, {}, {}".format(exc_type, fname, str(exc_tb.tb_lineno)))

def parse_website(thread_index, checkmiss):
    threads_number = config.thread_numbers

    captcha_error_count = 0

    print "Captcha Error Count: ", config.ERROR_MAX_CAPTCHA_COUNT
    print captcha_error_count, config.ERROR_MAX_CAPTCHA_COUNT
    print len(list_to_be_scraped)
    
    s = Scraper(use_cache=False, retries=3, timeout=30, proxy_file=proxy_file_name, one_proxy=True, 
            log_file='logs/log{}.txt'.format(thread_index))

    # print list_to_be_scraped
    
    # no_error = parse_first_webpage(thread_index, 0, "SMITH", "ANTHONY", VALUE_WEBSITE_JAIL)
    # return

    try:
        for ind, item in enumerate(list_to_be_scraped.keys()):
            personal_name = item
            lastname = personal_name.split(",")[0].strip()
            firstname = personal_name.split(",")[1].strip()
            
            no_error = config.ERROR_NO_NONE
            try:
                no_error = parse_first_webpage(thread_index, ind, lastname, firstname, checkmiss)
            except Exception as e:
                s.logger.info(e)
                show_exception_detail(e)
                s.save(["error", str(e)], "logs/error_{}.csv".format(thread_index))

            if no_error == config.ERROR_NO_CAPTCHA:
                captcha_error_count += 1

            if captcha_error_count > config.ERROR_MAX_CAPTCHA_COUNT:
                raise Exception("Captcha Service Error")
            
    except Exception as e:
        s1 = Scraper(use_cache=False, retries=3, timeout=30, proxy_file=proxy_file_name, one_proxy=True,
            log_file='logs/error_log{}.txt'.format(thread_index))
        s1.logger.info(e)

def get_depart_list(checkmiss=0):
    timestamp = int(datetime.now().strftime("%s")) * 1000 
    sub_url_list = []

    thread_index = 100
    person_list = []
    success_list = []

    tz = pytz.timezone('America/New_York')


    delete_date = (datetime.now(tz) + timedelta(days=-1)).strftime('%Y-%m-%d')
    print "Delete date =", delete_date
    try:
        db.session.query(DashboardLasd).filter(DashboardLasd.ArrestDate < delete_date).delete()
        db.session.commit()
    except Exception as e:
        print e

    delete_vine_date = (datetime.now(tz) + timedelta(days=-10)).strftime('%Y-%m-%d')
    print "Delete VINE date =", delete_vine_date
    try:
        db.session.query(DashboardVineName).filter(DashboardVineName.CapturedDate <= delete_vine_date).delete()
        db.session.commit()
    except Exception as e:
        print e

    currentdate = datetime.now(tz).strftime('%Y-%m-%d')
    tomorrowdate = (datetime.now(tz) + timedelta(days=1)).strftime('%Y-%m-%d')
    yestdate = (datetime.now(tz) + timedelta(days=-3)).strftime('%Y-%m-%d')

    url_list = [
        "http://www.jailbase.com/en/arrested/ca-lcso/{}/".format(tomorrowdate),
        "http://www.jailbase.com/en/arrested/ca-lcso/{}/".format(currentdate),
        "http://www.jailbase.com/en/arrested/ca-lcso/{}/".format(yestdate),
    ]

    print url_list

    need_delete = False
    try:
        with open("csv/" + success_filename) as csvfile:
            reader = csv.reader(csvfile)

            for i, item in enumerate(reader):
                if i > 0:
                    lastname = item[0]
                    firstname = item[1]
                    note = item[2]
                    booking_no = item[3]
                    date_time = item[4]
                    arrest = item[6]

                    if date_time != currentdate:
                        need_delete = True
                        break

                    success_list.append(lastname + "," + firstname)
                    save_names(lastname, firstname, success_filename, note, booking_no, arrest)

    except Exception as e:
        print e

    if need_delete is True:
        print "Delete Success File"
        s_filename = "csv/" + success_filename
        if os.path.exists(s_filename):
            os.remove(s_filename)


    for url in url_list:
        s = Scraper(use_cache=False, retries=3, timeout=30, proxy_file=proxy_file_name, one_proxy=True, 
            log_file='logs/log{}.txt'.format(thread_index))

        logger = s.logger

        html = s.load(url)
        print url

        persons = html.q("//div[@id='jbArrestContent']//div[@class='thumb-text2']/span")
        for person in persons:
            person_str = person.x("text()").strip()
            try:
                lastname=person_str.split(",")[0].replace(" ","")
                firstname=person_str.split(",")[1].strip().replace(" ","")

                person_list.append(lastname + "," + firstname)
            except Exception as e:
                continue

    missed_name_list = []

    for personal_name in person_list:
        p_lastname = personal_name.split(",")[0].strip()
        p_firstname = personal_name.split(",")[1].strip()

        exists = False
        for s_name in success_list:
            s_lastname = s_name.split(",")[0].strip()
            s_firstname = s_name.split(",")[1].strip()            

            if s_lastname == p_lastname and s_firstname == p_firstname:
                exists = True
                break

        if exists == False:
            missed_name_list.append(p_lastname + "," + p_firstname)

    print "****************************************"
    print "Success Len = ", len(success_list)
    print "Web Site Len = ", len(person_list)
    print "Missed Len = ", len(missed_name_list)
    print "****************************************"

    for s_name in missed_name_list:
        s_lastname = s_name.split(",")[0].strip()
        s_firstname = s_name.split(",")[1].strip()
        save_names(s_lastname, s_firstname, miss_filename)

    if len(missed_name_list) == 0:
        print "Delete Success File"
        s_filename = "csv/" + miss_filename

        if os.path.exists(s_filename):
            os.remove(s_filename)
    
    if checkmiss == VALUE_WEBSITE_JAIL:
        for item in missed_name_list:
            list_to_be_scraped[item] = ""

    if checkmiss == VALUE_WEBSITE_VINE:
        vine_name_list = db.session.query(DashboardVineName).all()

        print "****************************************"
        print "Vine Missed Len = ", len(vine_name_list)
        print "****************************************"

        for i, item in enumerate(vine_name_list):
            last_name = item.LastName
            first_name = item.FirstName
            obj_key = last_name + "," + first_name

            list_to_be_scraped[obj_key] = item.BookingNo

    # print json.dumps(list_to_be_scraped, indent=4)
    if checkmiss != VALUE_CHECK_MISSING:
        parse_website(thread_index, checkmiss)


def save_names(lastname, firstname, filename, note="", booking_no="", arrested=""):
    tz = pytz.timezone('America/New_York')

    currentdate = datetime.now(tz).strftime('%Y-%m-%d')
    currenttime = datetime.now(tz).strftime('%H:%M:%S')
    global_s.save([
        "Last", lastname,
        "First", firstname,
        "Note", note,
        "Booking No", booking_no,
        "Current Date", currentdate,
        "Current Time", currenttime,
        "Arrest", arrested
    ], "csv/" + filename)


def send_notify_email(lasd_item=None):

    content = """
        Booking No: {}
        Last Name: {}
        First Name: {}
        Total Bail: {}
        Race: {}
        Arrest Time: {}
        Location Description: {}
        Age: {}
        Sex: {}
    """.format(lasd_item.BookingNo, 
        lasd_item.LastName, 
        lasd_item.FirstName, 
        lasd_item.GrandTotal, 
        lasd_item.Race, 
        lasd_item.ArrestTime,
        lasd_item.LocationDescription,
        lasd_item.Age,
        lasd_item.Sex,
        )

    subject = "Booking No. ({})".format(lasd_item.BookingNo)

    msg = MIMEText(content.encode('utf-8'))
    msg['Subject'] = subject
    msg['From'] = config.from_mail
    #msg['To'] = ", ".join(config.receive_email)
    msg['To'] = config.receive_email

    # print  "Sending Email."
    # try:
        
    #     server = smtplib.SMTP('smtp.sendgrid.net')
    #     server.ehlo()
    #     server.starttls()
        
    #     server.login('apikey', config.send_grid_key)
    #     server.sendmail(config.from_mail, config.receive_email, msg.as_string())
    #     server.quit()
    # except Exception as e:
    #     print e
    #     return False

    print "++++++++Email Sent Successfully++++++++++"
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-c', '--checkmiss', type=int, required=False, default=0, help='Generate Missing File')
    
    args = parser.parse_args()
    checkmiss = args.checkmiss

    get_depart_list(checkmiss)

from scrapex import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from time import sleep
from selenium.webdriver import ActionChains
import sys
import random
import pytz
from models import DashboardLasd, DashboardJailHistory, DashboardNoResult, \
    DashboardVineName
import common_lib
import config
from mysql_manage import db
from datetime import datetime
import re
from remove import purge
from os import path
import argparse
import json
import requests
from requests.cookies import cookiejar_from_dict

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

selectStateXPath = "//select[@id='state']"

findOffenderXPath = '//img[@ng-click="onClickOFFENDER()"]'
continueXPath = '//button[@ng-click="ok()"]'

offenderIdXPath = "//input[@id='oid']"
searchBtnXPath = "//button[@id='labelbuttonsearch']"
iframeXPath = "//iframe[contains(@src , 'anchor?k=')]"

recaptchaSubmitBtnXPath = "//button[@type='submit']"
errorXPath = "//a[contains(@href, 'vinelink-threshold-limit')]"


def wait():
    sleep(random.randrange(config.DRIVER_SHORT_WAITING_SECONDS, config.DRIVER_MEDIUM_WAITING_SECONDS))


def wait_medium():
    sleep(random.randrange(config.DRIVER_MEDIUM_WAITING_SECONDS, config.DRIVER_LONG_WAITING_SECONDS))    


class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """
    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                if fn(driver):
                    return True
            except Exception:
                pass


def solve_recaptcha(t_driver, answer_id, url, sitekey):
    try:
        captcha_answer = ""
        if sitekey != "":
            print("Site Key -> {0}".format(sitekey))
            captcha_answer = common_lib.solve_captcha(sitekey, url)

        if "CAPCHA_NOT_READY" in captcha_answer:
            print("captcha is not solved")
            return config.RECAPTCHA_NOT_SOLVED
        else:
            try:
                # script_str = "document.getElementById('{}').style.display='block';".format(answer_id)
                # t_driver.execute_script(script_str)
                # wait()

                script_str = "document.getElementById('{}').value='{}';".format(answer_id, captcha_answer)
                t_driver.execute_script(script_str)
                wait()
            except Exception as e:
                print "?????????????????????????????? response not found ?????????????????????????????"
                if ("-1" not in answer_id) and ("-2" not in answer_id):
                    answer_id = answer_id + "-1"
                print answer_id
                print e

                try:
                    # script_str = "document.getElementById('{}').style.visibility='visible';".format(answer_id)
                    # t_driver.execute_script(script_str)
                    # wait()

                    script_str = "document.getElementById('{}').value='{}';".format(answer_id, captcha_answer)
                    t_driver.execute_script(script_str)
                    wait()
                except Exception as e:
                    print "?????????????????????????????? response not found ?????????????????????????????"
                    if ("-1" not in answer_id) and ("-2" not in answer_id):
                        answer_id = answer_id + "-2"
                    print answer_id
                    print e

                    # script_str = "document.getElementById('{}').style.visibility='visible';".format(answer_id)
                    # t_driver.execute_script(script_str)
                    # wait()

                    script_str = "document.getElementById('{}').value='{}';".format(answer_id, captcha_answer)
                    t_driver.execute_script(script_str)
                    wait()


            # print "+++++++++++++++++++++++++++++++++"
            # print captcha_answer
            # print "+++++++++++++++++++++++++++++++++"
    except Exception as e:
        print "-----------------------Solve recaptcha function error -------------------------"
        print e
        show_exception_detail(e)
        return config.RECAPTCHA_NOT_SOLVED

    return config.RECAPTCHA_SOLVED


def found_captcha(t_driver):
    doc = Doc(html=t_driver.page_source)

    iframe_url = ""
    for item in doc.q(iframeXPath):
        if item.x("@src") != "":
            iframe_url = item.x("@src").encode("utf-8").strip()

    print "URL -> ", iframe_url

    url = t_driver.current_url
    print "URL -> ", url

    if iframe_url != "":
        print("wait until it show response")
        WebDriverWait(t_driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, "//textarea[contains(@id, 'g-recaptcha-response')]")
                ),
            )
        )

        sitekey = ""
        try:
            sitekey = re.search("k\=(.*?)&", iframe_url).group(1)
        except Exception as e:
            print e
            pass

        print "SiteKey = ", sitekey

        if sitekey == "":
            common_lib.phantom_Quit(t_driver)
            exit()

        ret_value = solve_recaptcha(t_driver, "g-recaptcha-response", url, sitekey)
        print "Recatpcha = ", ret_value

        if (ret_value == config.RECAPTCHA_SOLVED):
            print "Click Checkbox after solve recaptcha"

            t_driver.switch_to_default_content()
            wait()

            recaptchaSubmitBtnObj = t_driver.find_element_by_xpath(recaptchaSubmitBtnXPath)
            actions = ActionChains(t_driver)
            actions.move_to_element(recaptchaSubmitBtnObj)
            actions.click(recaptchaSubmitBtnObj)
            actions.perform()
            wait_medium()

        return ret_value

    return None


def run():
    """Main function to run bot."""
    url = "https://www.vinelink.com/"
    driver = common_lib.create_chrome_driver(True)
    try:

        driver.get("http://lumtest.com/myip.json")
        wait()

        driver.get(url)
        wait()

        print "Wait for Select"
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, selectStateXPath)
                ),
                ec.presence_of_element_located(
                    (By.XPATH, errorXPath)
                ),
            )
        )

        errorObj = None
        try:
            errorObj = driver.find_element_by_xpath(errorXPath)
        except Exception as e:
            print e
            pass

        print errorObj
        if errorObj is not None:
            print "Exit"
            exit()

        print "Input-> {}".format(url)

        selectStateObj = driver.find_element_by_xpath(selectStateXPath)

        print "Change Select option as california ..."
        for option in selectStateObj.find_elements_by_tag_name('option'):
            if "California" == option.text:
                option.click()
                break

        sleep(config.DRIVER_MEDIUM_WAITING_SECONDS)

        print "Wait for Offender Button"
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, findOffenderXPath)
                )
            )
        )

        print "click Offender Button"
        findOffenderObj = driver.find_element_by_xpath(findOffenderXPath)
        actions = ActionChains(driver)
        actions.move_to_element(findOffenderObj)
        actions.click(findOffenderObj)
        actions.perform()
        wait_medium()

        print "wait continue button"
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, continueXPath)
                )
            )
        )
        print "click continue button"
        continueObj = driver.find_element_by_xpath(continueXPath)
        actions = ActionChains(driver)
        actions.move_to_element(continueObj)
        actions.click(continueObj)
        actions.perform()
        wait_medium()

        bookingNo = "5212364"

        print "wait offender Id"
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, offenderIdXPath)
                )
            )
        )

        offenderIdObj = driver.find_element_by_xpath(offenderIdXPath)
        offenderIdObj.click()
        wait()

        offenderIdObj.send_keys(bookingNo)
        wait()

        searchBtnObj = driver.find_element_by_xpath(searchBtnXPath)
        actions = ActionChains(driver)
        actions.move_to_element(searchBtnObj)
        actions.click(searchBtnObj)
        actions.perform()
        wait()

        print "wait for IFRAME RECAPTCHA"
        WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
            AnyEc(
                ec.presence_of_element_located(
                    (By.XPATH, iframeXPath)
                )
            )
        )

        ret_value = found_captcha(driver)

        if (ret_value == config.RECAPTCHA_SOLVED):

            # MILLER,CALVIN  RAY
            # LAST, FIRST, MIDDLE

            # DAVIS, CHANEL
            # with open("response.html", 'w') as f:
            #     f.write(driver.page_source.encode("utf-8"))

            # exit()

            name = ""
            bFirst = True

            for i, missing_id in enumerate(missing_id_list):
                try:
                    doc = Doc(html=driver.page_source)

                    iframe_url = ""
                    for item in doc.q(iframeXPath):
                        if item.x("@src") != "":
                            iframe_url = item.x("@src").encode("utf-8").strip()

                    with open("response_found.html", 'w') as f:
                        f.write(driver.page_source.encode("utf-8"))

                    if iframe_url != "":
                        print "Re-Captcha Found"

                        # print("wait until it show response")
                        # WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
                        #     AnyEc(
                        #         ec.presence_of_element_located(
                        #             (By.XPATH, "//textarea[@id='g-recaptcha-response']")
                        #         ),
                        #     )
                        # )

                        # sitekey = ""
                        # try:
                        #     sitekey = re.search("k\=(.*?)&", iframe_url).group(1)
                        # except Exception as e:
                        #     print e
                        #     pass

                        # print "SiteKey = ", sitekey

                        # if sitekey == "":
                        #     common_lib.phantom_Quit(t_driver)
                        #     exit()

                        # ret_value = solve_recaptcha(driver, "g-recaptcha-response", url, sitekey)
                        # print "Recatpcha = ", ret_value

                        # if (ret_value == config.RECAPTCHA_SOLVED):
                        #     print "Click Checkbox after solve recaptcha"

                        
                        ret_value = found_captcha(driver)
                        if (ret_value != config.RECAPTCHA_SOLVED):
                            common_lib.phantom_Quit(driver)
                            exit()

                    # bPass = True

                    # if iframe_url != "":
                    #     ret_value = found_captcha(driver)

                    #     if ret_value != config.RECAPTCHA_SOLVED:
                    #         bPass = False

                    # if bPass == False:
                    #     print "Captcha Error"
                    #     exit()

                    btnObj = driver.find_element_by_xpath("//span[contains(@label, 'Search again')]")

                    try:
                        name = driver.find_element_by_xpath("//div[@label='Offender Name']").get_attribute("value")
                        # print " Found Name -> ", name, " bFirst =", bFirst
                        missing_id = missing_id_list[i-1]

                        if (name != "") and (bFirst == False):
                            print "-------------------> Name = ", name, " BookingNo =", missing_id

                            LastName = name.split(",")[0]
                            name_str = name.split(",")[-1].strip()
                            FirstName = name_str.split(" ")[0]

                            booking_history = DashboardVineName(
                                s_bookingno=missing_id,
                                s_lastname=LastName,
                                s_firstname=FirstName,
                                s_captureddate=currentdate,
                                s_capturedtime=currenttime,
                                s_duplication=0
                            )

                            try:
                                db.session.add(booking_history)
                                db.session.commit()
                            except Exception as e:
                                print e

                    except Exception as e:
                        print e
                        pass

                    actions = ActionChains(driver)
                    actions.move_to_element(btnObj)
                    actions.click(btnObj)
                    actions.perform()
                    wait_medium()
                except:
                    pass

                bFirst = False
                # print "wait offender Id", i
                messageXpath = "//span[contains(text(), 'No offenders matching your criteria were found')]"

                WebDriverWait(driver, config.DRIVER_WAITING_SECONDS).until(
                    AnyEc(
                        ec.presence_of_element_located(
                            (By.XPATH, messageXpath)
                        ),
                        ec.presence_of_element_located(
                            (By.XPATH, offenderIdXPath)
                        ),
                    )
                )

                print "input offender id -> ", missing_id
                offenderIdObj = driver.find_element_by_xpath(offenderIdXPath)
                offenderIdObj.clear()
                wait()
                offenderIdObj.send_keys(str(missing_id))
                wait()

                searchBtnObj = driver.find_element_by_xpath(searchBtnXPath)
                actions = ActionChains(driver)
                actions.move_to_element(searchBtnObj)
                actions.click(searchBtnObj)
                actions.perform()
                wait_medium()

            print "*********************************"
            print "Completed"
            print "*********************************"

    except Exception as e:
        # common_lib.phantom_Quit(driver)
        print e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-m', '--method', type=int, required=False, default=0,
                        help='0: first, 1: last, other: random')

    args = parser.parse_args()
    method = args.method

    print "Delete Temp Dir"
    try:
        purge("C:\\Users\\Administrator\\AppData\\Local\\Temp", "scoped_dir")

        for folder_i in range(0,10):
            purge("C:\\Users\\Administrator\\AppData\\Local\\Temp\\{}".format(folder_i), "scoped_dir")
            purge("C:\\Users\\Administrator\\AppData\\Local\\Temp\\{}".format(folder_i), "chrome")

            for folder_j in range(0,10):
                purge("C:\\Users\\Administrator\\AppData\\Local\\Temp\\{}".format(folder_i), str(folder_j))
    except Exception:
        pass

    print "Delete Completed"

    sleep(config.DRIVER_SHORT_WAITING_SECONDS * 3)

    missing_id_list = []

    tz = pytz.timezone('America/Los_Angeles')
    currentdate = datetime.now(tz).strftime('%Y-%m-%d')
    currenttime = datetime.now(tz).strftime('%H:%M')
    print "Current Date & Time: {} , {}".format(currentdate, currenttime)

    vine_name_list = db.session.query(DashboardVineName.BookingNo).order_by(DashboardVineName.BookingNo.desc()).all()
    lasd_list = db.session.query(DashboardLasd.BookingNo).filter(
        DashboardLasd.ArrestDate == currentdate,
        ~DashboardLasd.BookingNo.contains(config.PREFIX_SANDIEGO)
    ).order_by(DashboardLasd.BookingNo.desc()).all()
    history_list = db.session.query(DashboardJailHistory.BookingNo).all()

    lasd_no_list = []
    for item in lasd_list:
        booking_no = item.BookingNo.replace(config.PREFIX_VINE, "")
        lasd_no_list.append(int(booking_no))

    vine_no_list = []
    for item in vine_name_list:
        vine_no_list.append(int(item.BookingNo))

    history_list = []
    for item in history_list:
        history_list.append(int(item.BookingNo))

    min_value = 0
    max_value = 0

    if len(lasd_no_list) > 1:
        min_value = int(lasd_no_list[len(lasd_no_list) - 1])
        max_value = int(lasd_no_list[0])
    else:
        if len(vine_no_list) > 0:
            min_value = vine_no_list[0] + 1
            max_value = vine_no_list[0] + 100
    print "Max = ", max_value, " Min = ", min_value

    id_list = []

    print "****************** Running Method ****************"
    print method
    print "****************** Running Method ****************"

    
    if method <= 2:
        min_value = min_value + 20 * method
        for i in range(0, config.ID_MISSING_LIST_COUNT * 2):
            for value in range(min_value, max_value):
                if value not in id_list:
                    id_list.append(value)
    elif method <= 6:
        max_value = max_value - 20 * (method - 1)
        print "Max = ", max_value, " Min = ", min_value

        for i in range(0, config.ID_MISSING_LIST_COUNT * 2):
            for value in range(max_value, min_value, -1):
                if value not in id_list:
                    id_list.append(value)
    else:
        for i in range(0, config.ID_MISSING_LIST_COUNT * 2):
            value = random.choice(range(max_value, min_value, -1))
            if value not in id_list:
                id_list.append(value)

    for i in id_list:
        b_Found = False
        for item in lasd_no_list:
            if item == i:
                b_Found = True
                break

        for item in vine_no_list:
            if item == i:
                b_Found = True
                break

        for item in history_list:
            if item == i:
                b_Found = True
                break

        if b_Found is False:
            missing_id_list.append(i)

        if len(missing_id_list) == config.ID_MISSING_LIST_COUNT:
            break

    print lasd_no_list
    print "+++++++++++++++++++++++++++++"
    print vine_no_list
    print "+++++++++++++++++++++++++++++"
    print missing_id_list

    if len(missing_id_list) > 0:
        run()
    else:
        print "Not found missing id"

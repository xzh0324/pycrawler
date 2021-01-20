# -*- coding:utf-8 -*-
# @author xuezhenhua
import datetime
import re

import requests
from selenium import webdriver
from helium import *
import time
import json

from selenium.webdriver import chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import model
from model import KEY_TOTAL, KEY_NAME, KEY_LINK
from model import KEY_CRASH
from model import KEY_ANR
from model import KEY_ERROR

QQ_USER_NAME = "123"
QQ_PASSWORD = "test"

# 【使用QQ某个方便的登录页，s_url表示登录后跳转的页面】
LOGIN_URL = "https://bugly.qq.com/v2/workbench/apps"
SUCCESS_URL = "https://bugly.qq.com/v2/workbench/apps"

# 【动态内容的根，Bugly所有页面都是动态生成的】
ROOT_ELEMENT = "return document.getElementById('root')"

APP_NAME_CLASS = "_1bPqZ_46W99zJg_a_ceYQf"
APP_ID_CLASS = "fwdCYw4oJ2IzdKsot4EmO"


def GET_SEARCH_URL(appId, date, status='all'):
    # https://bugly.qq.com/v2/crash-reporting/advanced-search/a0df5ed682?pid=1&status=0
    return "https://bugly.qq.com/v2/crash-reporting/advanced-search/"+appId+"&status="+status+"&date="+date


SEARCH_BTN_CLASS = "btn_blue"

SEARCH_CONTENT_CLASS = "main-content"


# // Hard Code End //

g_data = {
    "total":0,
    "crash":0,
    "anr":0,
    "error":0
}

g_appList = {
    "name":"",
    "data":{
        "not_handle":{
            "total":0,
            "crash":0,
            "anr":0,
            "error":0
        }
    }
}


driver = None
g_wait = None

def untilTrue(until):
    while True:
        if until():
            return

# @return object{ total crash anr error }
def search(url):
    global driver
    print("search:"+url)
    yesterday = datetime.datetime.today() + datetime.timedelta(-1)
    yesterday = yesterday.strftime('%Y%m%d')
    driver.get(url)
    time.sleep(1)

    htmlElement = None
    while True:
        htmlElement = driver.execute_script(ROOT_ELEMENT)
        if htmlElement is not None:
            break
        time.sleep(1)


    g_wait.until(EC.presence_of_all_elements_located)

    btnSearch = None
    while True:
        btnSearch = htmlElement.find_element_by_class_name(SEARCH_BTN_CLASS)
        if btnSearch is not None:
            break
        time.sleep(1)


    # wait for document loaded
    g_wait.until(EC.presence_of_all_elements_located)
    # wait for btn clickable
    g_wait.until(EC.element_to_be_clickable((By.CLASS_NAME, SEARCH_BTN_CLASS)))

    while True:
        try:
            btnSearch.click()
            break
        except:
            time.sleep(1)
            continue

    # wait for document loaded
    g_wait.until(EC.presence_of_all_elements_located)

    time.sleep(5)
    # wait for result

    content = driver.find_element_by_class_name(SEARCH_CONTENT_CLASS).text
    print(content)
    allcrash = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/div/div[2]').text
    # print(allcrash)
    index = 0
    with open("crash" + url.split('=')[-1] + str(yesterday) + ".txt", 'w') as fw:
        for line in allcrash.splitlines():
            if line.strip() == "上报时间:-":
                index = index + 1
                try:
                    strlink = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/div/div[2]/div['+str(index)+']/div/ul/li[5]/a').get_attribute("href")
                    fw.write(strlink + "\n")
                except Exception as e:
                    print(e)
            fw.write(line + "\n")
    result = []
    list = content.split(' ')
    pattern = re.compile(r'^\d+(\,\d+)?')
    for item in list:
        match = re.match(pattern, item)
        if item.isdigit() or match:
            result.append(item)
    obj = {}
    obj[KEY_LINK] = url
    obj[KEY_TOTAL] = 0
    obj[KEY_CRASH] = 0
    obj[KEY_ANR] = 0
    obj[KEY_ERROR] = 0
    if len(result) == 4:
        obj[KEY_TOTAL] = result[0]
        obj[KEY_CRASH] = result[1]
        obj[KEY_ANR] = result[2]
        obj[KEY_ERROR] = result[3]
    return obj
    pass


def login():
    global driver
    global g_wait

    g_wait.until(EC.presence_of_all_elements_located)
    driver.switch_to.frame(driver.find_element_by_id("ptlogin_iframe"))
    driver.find_element_by_id('switcher_plogin').click()

    input_str = driver.find_element_by_xpath('//*[@id="u"]')
    input_str.clear()
    input_str.send_keys(QQ_USER_NAME)
    # time.sleep(1)
    password_element = driver.find_element_by_xpath('//*[@id="p"]')
    password_element.clear()
    password_element.send_keys(QQ_PASSWORD)
    # time.sleep(1)
    button = driver.find_element_by_xpath('//*[@id="login_button"]')
    button.click()
    driver.switch_to.default_content()
    time.sleep(5)

    while True:
        if (SUCCESS_URL in driver.current_url):
            print ("Login Successful.")
            break
        time.sleep(2)
        print ("Login Failed. Waiting manual login.")
    pass

# @return appNameList[], appIdList[]
def get_app_list():
    global driver
    global g_wait

    htmlElement = None
    names = None
    
    while True:
        htmlElement = driver.execute_script(ROOT_ELEMENT)
        if htmlElement is not None:
            names = htmlElement.find_elements_by_class_name(APP_NAME_CLASS)
            if len(names) > 0:
                # time.sleep(1)
                break
        time.sleep(1)

    names = htmlElement.find_elements_by_class_name(APP_NAME_CLASS)
    ids = htmlElement.find_elements_by_class_name(APP_ID_CLASS)

    appNameList = []
    appIdList = []
    for name in names:
        name = name.text
        appNameList.append(name)
        print(name)
    for id in ids:
        id = id.get_attribute('href')
        if id is not None:
            id = id[id.rindex('/') + 1: len(id)]
            appIdList.append(id)
            print(id)
    return appNameList, appIdList
    pass

def test():
    global driver
    driver.get("https://www.baidu.com/")
    print("https OK")

def main():
    global driver
    global g_wait
    startTime = time.time()

    option = webdriver.ChromeOptions()
    option.add_argument('--no-sandbox')
    driver = start_chrome(LOGIN_URL, options=option)##获取网页
    driver.maximize_window()##最大化窗口


    g_wait = WebDriverWait(driver, 10) # wait for at most 10s

    print("## step1. login ##")
    login()

    print("## step2. get app list ##")
    appNameList, appIdList = get_app_list()

    print("## step3. get app crash data ##")
    yesterday = datetime.datetime.today() + datetime.timedelta(-1)
    yesterday = yesterday.strftime('%Y%m%d')
    driver.get("https://bugly.qq.com/v2/crash-reporting/dashboard/" + appIdList[0] + "&isRealTime=1&startDate1="+str(yesterday)+"&endDate1="+str(yesterday)+"&date1=custom")
    time.sleep(1)

    htmlElement = None
    result3 = {}
    result3[KEY_CRASH] = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/ul/li[1]/span[2]').text
    while True:
        result3[KEY_CRASH] = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/ul/li[1]/span[2]').text
        if result3[KEY_CRASH] != "-":
            break
        time.sleep(1)
    print(result3[KEY_CRASH])
    result3[KEY_ANR] = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/ul/li[2]/span[2]').text
    result3[KEY_ERROR] = driver.find_element_by_xpath('//*[@id="root"]/div/div/div[2]/div/div[2]/ul/li[3]/span[2]').text
    dataList = []
    for i in range(len(appNameList)):
        print("name:"+appNameList[i])
        appId = appIdList[i]

        result = []
        searchNotHandleUrl = GET_SEARCH_URL(appId, "", "0")
        result1 = search(searchNotHandleUrl)
        result1[KEY_NAME] = appNameList[i]
        result1[KEY_LINK] = GET_SEARCH_URL(appId, "")
        result.append(result1)

        searchLast1DayUrl = GET_SEARCH_URL(appId, "last_1_day")
        result2 = search(searchLast1DayUrl)
        result2[KEY_NAME] = appNameList[i]
        result2[KEY_LINK] = GET_SEARCH_URL(appId, "")
        result.append(result2)
        result.append(result3)
        dataList.append(result)
    print(dataList)

    print("## Time Cost: " + model.getPassTime(startTime))
    model.generateMailHtmlText(dataList)
    print("## finally. quit browser ##")
    driver.quit()




if __name__ == '__main__':
    # Main #
    main()

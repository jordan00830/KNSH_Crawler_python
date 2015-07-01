# -*- coding=utf-8 -*-
import httplib, urllib
from bs4 import BeautifulSoup
import pprint

def main():
    
    KNSHCrawler = crawler()
    KNSHCrawler.getSchoolList('1031b','A')
    # KNSHCrawler.getBook('SCB027,七堵國小','1032a','C','2')

class crawler:
    def __init__(self):
        return

    # Return : [{'schoolID': 'SCB027,七堵國小', 'schoolAddr': '七堵國小 - 基隆市七堵區明德一路184號'} ...]    
    def getSchoolList(self,semesterID, countryID):
        result = [] # [{'schoolID': 'SCB027,七堵國小', 'schoolAddr': '七堵國小 - 基隆市七堵區明德一路184號'} ...]    
        # Get Data
        paramsObj = {'hidsel1': semesterID, 'hidsel2': countryID}
        htmlSoup, response  = self.__getDataByHttpPost(paramsObj)
        schoolListDOM = htmlSoup.find_all(attrs={"name": "sel0"})[0].find_all('option')
        
        # Process content
        for row in schoolListDOM:
            schoolID = row.get('value')
            schoolAddr = row.get_text()
            if schoolID:
                eachSchool = {'schoolID': schoolID, 'schoolAddr': schoolAddr}
                result.append(eachSchool)
        printUnicodeObj(result)
        return result

    # Return : [{'publisherName': '南一', 'courseName': '國語'} ... ]
    def getBook(self,schoolID,semesterID,countryID,grade):
        result = [] # [{'publisherName': '南一', 'courseName': '國語'} ... ]
        # Get data
        paramsObj = {'sel0': schoolID, 'sel1': semesterID, 'sel2': countryID, 'sel4': grade, 'hidsubmited':'Y' }
        htmlSoup, response  = self.__getDataByHttpPost(paramsObj)
        bookDOM = htmlSoup.find_all(id="table_1")[0]

        # Process content
        publisherMap = [] # [index: 'publisherName',...]
        for row in bookDOM.find_all('tr'):
            # Title :  科目\出版社 | 康軒 | 南一 | 翰林 | 部編 |
            if len(row.find_all('th')) > 0:
                publisherMap = map(lambda x: x.get_text(), row.find_all('th')) 
                printUnicodeObj(publisherMap)
            # Row :       國語    |  v  |      |     |　   |
            #             數學    |     |   v  |     |　   |
            #             生活    |     |      |  v  |　   |
            else:
                eachCourseBook = {'publisherName': None , 'courseName': None }
                for idx,courseCol in enumerate(row.find_all('td')):
                    if idx == 0:
                        eachCourseBook["courseName"] = courseCol.get_text()
                    elif (idx != 0) and len(courseCol.contents) > 0:
                        eachCourseBook["publisherName"] = publisherMap[idx]
                result.append(eachCourseBook)           
        printUnicodeObj(result)
        return result        

    # Return : BeautifulSoup object
    def __getDataByHttpPost(self,paramsObj):   
        params =  urllib.urlencode(paramsObj)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn = httplib.HTTPSConnection("www.knsh.com.tw")
        conn.request("POST", "/_KNSH/Version.asp?go_Sub_Topic=06", params, headers)
        response = conn.getresponse()
        # print response.status, response.reason
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')
        return soup, response

def printUnicodeObj(obj, prettify = True):
    if prettify:
        for v in obj:
            print repr(v).decode("unicode-escape")
    else:
        print repr(obj).decode("unicode-escape")

if __name__ == '__main__':
    main()
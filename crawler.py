# -*- coding=utf-8 -*-
import httplib, urllib
from bs4 import BeautifulSoup
import pprint

def main():
    
    KNSHCrawler = crawler()
    # KNSHCrawler.getSchoolList('1031b','A')
    # KNSHCrawler.getBook('SCB027,七堵國小','1032a','C','2')
    # KNSHCrawler.getAllSemesterAndCountry()
    KNSHCrawler.crawlAll()

class crawler:
    def __init__(self):
        return


    def crawlAll(self):
        semesterList, countryList = self.getAllSemesterAndCountry()
        for semester in semesterList:
            for country in countryList:
                schooList = self.getSchoolList(semester["semesterID"].encode('utf-8'),country["countryID"].encode('utf-8'))
                for school in schooList:
                    gradeList = self.__getGradeRange(semester["semesterID"])
                    for grade in gradeList:
                        bookList = self.getBook(school["schoolID"].encode('utf-8'),semester["semesterID"].encode('utf-8'),country["countryID"].encode('utf-8'),grade)
                        self.__printFinalResultText(semester["semesterText"],country["countryName"], school["schoolAddr"], grade, bookList)
                        # print semester["semesterText"], '|', country["countryName"] , '|' , school["schoolAddr"], '|' , grade , '年級'
                        # printUnicodeObj(bookList)

    def __printFinalResultText(self, semesterText, countryName, schoolAddr, grade, bookList):
        print semesterText, '|', countryName, '|', schoolAddr.split(" ")[0], '|', grade, '年級'
        for row in bookList:
            if not row["publisherName"]:
                row["publisherName"] = "未提供"
            print row["courseName"], '|' , row["publisherName"]
        print '----------------------------------------------------'    

    def __writeFinalResultCSV(self):
        return

    def __getGradeRange(self,semesterID):
        # elementary school
        if 'a' in semesterID:
            return ['1','2','3','4','5','6']
        # junior high schoool
        elif 'b' in semesterID:
            return ['1','2','3']      


    # Return : semesterResult, countryResult
    #       semesterResult => [{'semesterID':'1032a', 'semesterText' : '國小103學年度下學期'}]
    #       countryResult  => [{ 'countryID' :'A', 'countryName': '台北市'} ...]
    def getAllSemesterAndCountry(self):
        semesterResult = [] # [{'semesterID':'1032a', 'semesterText' : '國小103學年度下學期'}]
        countryResult = [] # [{ 'countryID' :'A', 'countryName': '台北市'} ...]

        # Get Data
        htmlSoup, response  = self.__getDataByHttpPost()
        semesterDOM = htmlSoup.find_all(attrs={"name": "sel1"})[0].find_all('option')
        countryDOM = htmlSoup.find_all(attrs={"name": "sel2"})[0].find_all('option')

        # Process semester content
        for row in semesterDOM:
            semesterID = row.get('value')
            semesterText = row.get_text()
            if semesterID:
                eachSemester = {'semesterID': semesterID, 'semesterText': semesterText}
                semesterResult.append(eachSemester)
        # Process country content
        for row in countryDOM:
            countryID = row.get('value')
            countryName = row.get_text()
            if countryID:
                eachCountry = {'countryID' : countryID, 'countryName' : countryName}
                countryResult.append(eachCountry)

        # printUnicodeObj(semesterResult)
        # printUnicodeObj(countryResult)
        return semesterResult, countryResult


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
        # printUnicodeObj(result)
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
        # printUnicodeObj(result)
        return result        

    # Return : BeautifulSoup object
    def __getDataByHttpPost(self,paramsObj = {}):   
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
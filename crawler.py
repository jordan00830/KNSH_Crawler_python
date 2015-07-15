# -*- coding: utf-8 -*-  
import httplib, urllib,json
from bs4 import BeautifulSoup
import pprint
import csv
import collections
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')

# Const variable
with open('conf/PUBLISHER_NAME_MAP.json') as fp:
    PUBLISHER_NAME_MAP = json.load(fp)

# Map Enum to courseFilter key name
ENUM_SCHOOL_TYPE_ELE = 'elememtarySchool'
ENUM_SCHOOL_TYPE_SEN = 'seniorHighSchool'

# outputMode = 1 # 1 as chinese mode, 2 as abbreviation mode

def main():
    KNSHCrawler = crawler()
    # KNSHCrawler.getSchoolList('1031b','A')
    # KNSHCrawler.getBook('SCB027,七堵國小','1032a','C','2')
    # KNSHCrawler.getAllSemesterAndCountry()
    # KNSHCrawler.crawlAll()
    # KNSHCrawler.crawlByUserDefine()

    print '\nWhich crawl mode do you want to crawl?\n\n'\
        '1. crawl all courses (only for testing, this choice will not write output file) \n'\
        '2. crawl customized courses\n'\

    crawlMode = raw_input('Enter the choice: ')

    print '\nWhich output mode do you want?\n\n'\
        '1. write chinese directly\n'\
        '2. write abbreviation defined in config\n'
    outputMode = raw_input('Enter the choice: ') # Write chinese or abbr map conf in PUBLISHER_NAME_MAP.json
    KNSHCrawler.setOutputMode(outputMode)

    if int(crawlMode) == 1:
        KNSHCrawler.crawlAll()
    elif int(crawlMode) == 2:
        KNSHCrawler.crawlByUserDefine()    

class crawler:
    def __init__(self):
        self.outputMode = 1; # 1 as chinese mode ( by default), 2 as abbreviation mode
        return

    def setOutputMode(self,outputMode):
        self.outputMode = int(outputMode)

    def crawlAll(self):
        print 'Fetching semester && country information...\n'
        semesterList, countryList = self.getAllSemesterAndCountry()
        semesterList = self.__askSemester(semesterList)
        
        print 'Crawler start...\n'
        for semester in semesterList:
            for country in countryList:
                schooList = self.getSchoolList(semester['semesterID'].encode('utf-8'),country['countryID'].encode('utf-8'))
                for school in schooList:
                    gradeList = self.__getGradeRange(semester['semesterID'])
                    for grade in gradeList:
                        bookList = self.getBook(school['schoolID'].encode('utf-8'),semester['semesterID'].encode('utf-8'),country['countryID'].encode('utf-8'),grade)
                        self.__printFinalResultText(semester['semesterText'],country['countryName'], school['schoolAddr'], grade, bookList)
                        
    def crawlByUserDefine(self):
        with open('conf/COURSE_FILTER.json') as fp:
            courseFilter = json.load(fp, object_pairs_hook=collections.OrderedDict)
        
        print 'Fetching semester && country information...\n'
        semesterList, countryList = self.getAllSemesterAndCountry()
        
        # Ask request semester
        semesterList = self.__askSemester(semesterList)
        
        # Ask request country
        isAllCountry, countryList = self.__askCountry(countryList)

        print 'Crawler start...\n'
        for semester in semesterList:
            countryIdStr = 'ALL' if isAllCountry else ''.join(map(lambda x: x['countryID'], countryList))
            outputFileName = '%s_%s.csv' % (semester['semesterText'],countryIdStr)
            # print outputFileName
            # return
            csvFp = csv.writer(open( outputFileName, 'wb'))

            # Write title info
            self.__writeCSVTitle(courseFilter,semester['semesterID'],csvFp)            
            for country in countryList:
                schooList = self.getSchoolList(semester['semesterID'].encode('utf-8'),country['countryID'].encode('utf-8'))
                for school in schooList:
                    # 縣市名稱 | 學校名稱
                    csvRow = [country['countryName'] ,school['schoolAddr'].split(' ')[0]]
                    gradeList = self.__getGradeRange(semester['semesterID'])
                    for grade in gradeList:
                        bookList = self.getBook(school['schoolID'].encode('utf-8'),semester['semesterID'].encode('utf-8'),country['countryID'].encode('utf-8'),grade)
                        # Filter bookList  
                        schoolType = self.__detectSchoolType(semester['semesterID'])
                        selectedCourse = courseFilter[schoolType][str(grade)]    
                        bookList = filter(lambda x: x['courseName'] in selectedCourse ,bookList)
                        
                        # Append bookList in courseFilter setting order
                        for selCourseName in courseFilter[schoolType][str(grade)]:
                            publisher = filter(lambda bookItem: bookItem['courseName'] == selCourseName ,bookList)[0]['publisherName']
                            if self.outputMode == 1:
                                csvRow.append(publisher)
                            elif self.outputMode == 2:    
                                publisherAbbr = [key for key, value in PUBLISHER_NAME_MAP.items() if value == publisher.encode('utf-8')]
                                csvRow.append(publisherAbbr[0]) if len(publisherAbbr) > 0 else csvRow.append("")
                                
                                # csvRow.append(publisherAbbr)
                        self.__printFinalResultText(semester['semesterText'],country['countryName'], school['schoolAddr'], grade, bookList)
                    csvFp.writerow(csvRow)
        print 'Success!'

    def __writeCSVTitle(self,courseFilter,semesterID,csvFp):
        schoolType = self.__detectSchoolType(semesterID)        
        # First row => |  |  | 一年級 | 二年級 | 三年級 | 四年級 | 五年級 | 六年級
        row = ["",""] # for 縣市名稱 | 學校名稱
        for grade, selectedCourse in courseFilter[schoolType].items():
            row.append(convertNumToChinese(grade) + '年級')
            for x in xrange(1,len(selectedCourse)):
                row.append("")
        csvFp.writerow(row)
        # Second row => 縣市名稱 | 學校名稱 | 科目1 | 科目2 ....
        row = ['縣市名稱','學校名稱']
        for grade, selectedCourse in courseFilter[schoolType].items():
            for courseName in selectedCourse:
                row.append(courseName)
        csvFp.writerow(row)

    # Return : ENUM_SCHOOL_TYPE_ELE | ENUM_SCHOOL_TYPE_SEN
    def __detectSchoolType(self,semesterID):
        if "a" in semesterID:
            return ENUM_SCHOOL_TYPE_ELE
        elif "b" in semesterID:
            return ENUM_SCHOOL_TYPE_SEN    

    def __askSemester(self, semesterList):
        print 'Please choose the semester type you want to crawl\n'
        for idx, semester in enumerate(semesterList):
            print str(idx) + '. ' + semester['semesterText']
        selSemesterIdxStr = raw_input('\nEnter the choice'\
                                    ' (use "," for multiple choice): ')
        selSemesterIdxArr = map(lambda x: int(x) ,selSemesterIdxStr.split(','))
        return [ x for _,x in filter(lambda (i,x): i in selSemesterIdxArr , enumerate(semesterList))]

    def __askCountry(self, countryList):
        print 'Please choose the country\n'
        for idx, country in enumerate(countryList):
            print str(idx) + ". " + country['countryName']
        print '\nUse "-" for a range, "," for multiple choice'\
            '\nExample: 0-3,5,7,10-15'
        
        selCountryIdxStr = raw_input('\nEnter the choice'\
                                  ' (press Enter directly for all country): ')    
        if selCountryIdxStr:
            selCountryIdxArr = []
            selCountryIdxArrTmp = map(lambda x: x, selCountryIdxStr.split(','))
            for selIdx in selCountryIdxArrTmp:
                # range value
                if '-' in selIdx:
                    startIdx,endIdx = selIdx.split('-')
                    for rangeIdx in range(int(startIdx),int(endIdx)+1):
                        selCountryIdxArr.append(rangeIdx)
                # single value
                else:
                    selCountryIdxArr.append(selIdx)      
            # convert into integer
            selCountryIdxArr = [int(x) for x in selCountryIdxArr]
            return False, [ x for _,x in filter(lambda (i,x): i in selCountryIdxArr , enumerate(countryList))]
        else:
            return True, countryList

    def __printFinalResultText(self, semesterText, countryName, schoolAddr, grade, bookList):
        print semesterText, '|', countryName, '|', schoolAddr.split(" ")[0], '|', grade, '年級'
        for row in bookList:
            if not row['publisherName']:
                row['publisherName'] = '未提供'
            print row['courseName'], '|' , row['publisherName']
        print '----------------------------------------------------'    

    def __getGradeRange(self,semesterID):
        # elementary school
        if self.__detectSchoolType(semesterID) == ENUM_SCHOOL_TYPE_ELE:
            return ['1','2','3','4','5','6']
        # junior high schoool
        elif self.__detectSchoolType(semesterID) == ENUM_SCHOOL_TYPE_SEN:
            return ['1','2','3']      


    # Return : semesterResult, countryResult
    #       semesterResult => [{'semesterID':'1032a', 'semesterText' : '國小103學年度下學期'}]
    #       countryResult  => [{ 'countryID' :'A', 'countryName': '台北市'} ...]
    def getAllSemesterAndCountry(self):
        semesterResult = [] # [{'semesterID':'1032a', 'semesterText' : '國小103學年度下學期'}]
        countryResult = [] # [{ 'countryID' :'A', 'countryName': '台北市'} ...]

        # Get Data
        htmlSoup, response  = self.__getDataByHttpPost()
        semesterDOM = htmlSoup.find_all(attrs={'name': 'sel1'})[0].find_all('option')
        countryDOM = htmlSoup.find_all(attrs={'name': 'sel2'})[0].find_all('option')

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
        schoolListDOM = htmlSoup.find_all(attrs={'name': 'sel0'})[0].find_all('option')
        
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
        bookDOM = htmlSoup.find_all(id='table_1')[0]

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
                eachCourseBook = {'publisherName': '' , 'courseName': '' }
                for idx,courseCol in enumerate(row.find_all('td')):
                    if idx == 0:
                        eachCourseBook['courseName'] = courseCol.get_text()
                    elif (idx != 0) and len(courseCol.contents) > 0:
                        eachCourseBook['publisherName'] = publisherMap[idx]
                result.append(eachCourseBook)           
        # printUnicodeObj(result)
        return result        

    # Return : BeautifulSoup object
    def __getDataByHttpPost(self,paramsObj = {}):   
        params =  urllib.urlencode(paramsObj)
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
        conn = httplib.HTTPSConnection("www.knsh.com.tw")
        conn.request('POST', '/_KNSH/Version.asp?go_Sub_Topic=06', params, headers)
        response = conn.getresponse()
        # print response.status, response.reason
        data = response.read()
        soup = BeautifulSoup(data, 'html.parser')
        return soup, response

def convertNumToChinese(str):
    if str == '1' or str == 1:
        return '一'
    elif str == '2' or str == 2:
        return '二'
    elif str == '3' or str == 3:
        return '三'
    elif str == '4' or str == 4:
        return '四'
    elif str == '5' or str == 5:
        return '五'
    elif str == '6' or str == 6:
        return '六'

def printUnicodeObj(obj, prettify = True):
    if prettify:
        for v in obj:
            print repr(v).decode('unicode-escape')
    else:
        print repr(obj).decode('unicode-escape')

if __name__ == '__main__':
    main()
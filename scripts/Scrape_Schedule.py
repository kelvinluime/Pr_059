# Database
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr

# Processing
import numpy as np
import pandas as pd
from pathlib import Path
from functools import reduce
import json
from multiprocessing.dummy import Pool as ThreadPool

# Time
import datetime
import time
import pytz

# Data scrapping 
from bs4 import BeautifulSoup

#Scraping the Scheduling DATA
QUERY_TERMS = ['SP18', 'WI18']
QUERY_DEPTS = ['AIP', 'AWP', 'ANBI', 'ANAR', 'ANTH', 'ANSC', 'BENG', ' BIEB', 'BICD', 'BIPN', 'BIBC', 'BILD', 'BIMM', 'BISP', 'CENG', 'CHEM', 'CHIN', 'COGS', 'COMM', 'CSE', 'ICAM', 'CONT','CGS', 'CAT', 'TDDM', 'TDHD', 'TDMV', 'TDTR', 'DSC', 'DSGN', 'DOC', 'ECON', 'EDS', 'ERC', 'ECE','ENG', 'ENVR', 'ESYS', 'ETHN', 'EXPR', 'FMPH', 'FILM', 'HITO', 'HIEA', 'HIEU', 'HILA', 'HISC', 'HINE', 'HIUS', 'HILD','HDP', 'HUM', 'INTL', 'JAPN', 'JUDA', 'LATI', 'LIAB', 'LIDS', 'LIGN',  'LIHL', 'LIIT', 'LIPO', 'LISP','LISP', 'LTFR', 'LTGM', 'LTIT', 'LIFR', 'LTKO','LTLA', 'LTRU', 'LTSP', 'LTWR', 'LTEN', 'LTWL', 'LTEA', 'MMW', 'MATH',  'MAE','MCWP', 'MUS', 'NANO', 'PHIL', 'PHYS', 'POLI', 'PSYC', 'RELI', 'REV', 'SOCE', 'SOCI', 'SE', 'TDAC','TDDE', 'TDDR', 'TDGE', 'TDHT', 'TDPW', 'TWS', 'TMC', 'USP', 'VIS', 'WARR', 'WCWP']

def get_soup(dept='CSE', term='SP18', page='1'):
    """
    Return a soup object with given dept, term, and page.  
    """
    parameters = 'selectedTerm='+term+'&xsoc_term=&loggedIn=false&tabNum=&selectedSubjects='+dept+'&_selectedSubjects=1&schedOption1=true&_schedOption1=on&_schedOption11=on&_schedOption12=on&schedOption2=true&_schedOption2=on&_schedOption4=on&_schedOption5=on&_schedOption3=on&_schedOption7=on&_schedOption8=on&_schedOption13=on&_schedOption10=on&_schedOption9=on&schDay=M&_schDay=on&schDay=T&_schDay=on&schDay=W&_schDay=on&schDay=R&_schDay=on&schDay=F&_schDay=on&schDay=S&_schDay=on&schStartTime=12%3A00&schStartAmPm=0&schEndTime=12%3A00&schEndAmPm=0&_selectedDepartments=1&schedOption1Dept=true&_schedOption1Dept=on&_schedOption11Dept=on&_schedOption12Dept=on&schedOption2Dept=true&_schedOption2Dept=on&_schedOption4Dept=on&_schedOption5Dept=on&_schedOption3Dept=on&_schedOption7Dept=on&_schedOption8Dept=on&_schedOption13Dept=on&_schedOption10Dept=on&_schedOption9Dept=on&schDayDept=M&_schDayDept=on&schDayDept=T&_schDayDept=on&schDayDept=W&_schDayDept=on&schDayDept=R&_schDayDept=on&schDayDept=F&_schDayDept=on&schDayDept=S&_schDayDept=on&schStartTimeDept=12%3A00&schStartAmPmDept=0&schEndTimeDept=12%3A00&schEndAmPmDept=0&courses=&sections=&instructorType=begin&instructor=&titleType=contain&title=&_hideFullSec=on&_showPopup=on'
    page_source = requests.get('https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudentResult.htm?page='+page+'&'+parameters)
    return BeautifulSoup(page_source.content, 'html.parser')

def get_time(dept='CSE', term='SP18'):
    page = 1
    soup = get_soup(dept,term, str(page))
    time_list = []
    availability = []
    capacity = []

    while 'Error report' not in soup.html.head.title.text:
        for first in soup.find_all(True, {'class': 'sectxt'}):
            stuff = first.find_all(True,{'class': 'brdr'})
            if len(stuff) > 6 and '\n' not in stuff[6] and len(stuff) > 10 and "ertext" not in str(stuff[10]):
                time_list += stuff[6]
                availability += stuff[10]
                capacity += stuff[11]
                
        page += 1
        soup = get_soup(dept, term, str(page))
    people = [0 for i in range(len(availability))]
    
    for i in range(len(capacity)):
        if(str(availability[i]) != "Unlim" and int(availability[i]) <= int(capacity[i])):
            people[i] = int(int(capacity[i]) - int(availability[i]))
        else:
            people[i] = int(capacity[i])

    return people, time_list

def splitTimes(timeOfCourse = ["stuff"]):
    start_time = ["" for _ in range(len(timeOfCourse))]
    end_time = ["" for _ in range(len(timeOfCourse))]
    
    for i in range(len(timeOfCourse)):
        start_time[i] = timeOfCourse[i].split("-")[0]
        end_time[i] = timeOfCourse[i].split("-")[1]
    return start_time, end_time

def updateTime(timeList = [4]):
    for i in range(len(timeList)):
        if timeList[i].endswith("p") and timeList[i][1] == ":": 
            if timeList[i][:2].endswith(":"):
                timeList[i] = str(int(timeList[i][:1]) + 12) + ":" + timeList[i][2:4]
            else:
                timeList[i] = str(int(timeList[i][:2]) + 12) + ":" + timeList[i][3:5]
    return timeList

def takeEndSymbol(timeList = []):
    for i in range(len(timeList)):
        if timeList[i].endswith("a") or timeList[i].endswith("p"):
            timeList[i] = timeList[i][:-1]
    return timeList

def convertToDouble(time = []):
    for i in range(len(time)):
        temp = time[i].split(":")
        data = float(temp[0]) + (float(temp[1])/100)*(5.0/3.0)
        time[i] = data
    return time


def getAll(quarter, name):
    people_total = []
    beg_total = []
    end_total = []
    for i in QUERY_DEPTS:
        people, time_list = get_time(i, quarter)
        beg = []
        end = []
        beg, end = splitTimes(time_list)
        #if p, then adds 12 
        newBeg = updateTime(beg)
        newEnd = updateTime(end)
        #take away the a and p at end
        newBeg = takeEndSymbol(newBeg)
        newEnd = takeEndSymbol(newEnd)
        #convert to double
        newBeg = convertToDouble(newBeg)
        newEnd = convertToDouble(newEnd)
        people_total += people
        beg_total += newBeg
        end_total += newEnd
    d = {'size': people_total, 'start_time':beg_total, 'end_time':end_total}
    df = pd.DataFrame(d)
    df = df[['start_time', 'end_time', 'size']]
    df.to_csv(name, sep='\t')
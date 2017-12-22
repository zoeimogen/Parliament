#!/usr/bin/python
# pylint: disable=invalid-name
import collections
import datetime
import argparse
import csv
import tabulate
import requests
from lxml import etree

today = datetime.date.today()

# A list of parties with more than 4 members.
partynames = {'Bishops': 'Bishop',
              'Crossbench': 'XBench',
              'Conservative': 'Cons',
              'Labour': 'Labour',
              'Liberal Democrat': 'LibDem'}

def calculate_age(born):
    '''CAolculate someone's Age'''
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def summarise(year, lords, factor):
    '''Calcuate membership of the house for a given year'''
    total = len([l for l in lords if l[factor] >= year or l['type'] != 'Life peer'])
    line = [year, total]
    other = total
    for party in partynames:
        count = len([l for l in lords if l['party'] == party and
                     (l[factor] >= year or l['type'] != 'Life peer')])
        other = other - count
        line.append(count)
    line.append(other)
    return line

parser = argparse.ArgumentParser(description='Predict Lords  membership under various rules')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--life', action='store_true', help='Current life membership rules')
group.add_argument('--age75', action='store_true', help='Mandatory retirement at 75')
group.add_argument('--age80', action='store_true', help='Mandatory returement at 80')
parser.add_argument('--csv', action='store_true', help='Output CSV format (e.g. for Excel)')
args = parser.parse_args()

if args.life:
    factor = 'lifetime'
    # Life expectancy data from ONS
    ages = collections.defaultdict(dict)

    with open('life.csv', 'rb') as csvfile:
        lifereader = csv.reader(csvfile, delimiter=',')
        for row in lifereader:
            ages[int(row[0])]['M'] = float(row[5])
            ages[int(row[0])]['F'] = float(row[10])
elif args.age75:
    factor = 'age75'
else:
    factor = 'age80'

# Get current membership of the house of Lords.
url = ('http://data.parliament.uk/'
       '/membersdataplatform/services/mnis/members/query/House=Lords/BasicDetails/')
r = requests.get(url)
root = etree.fromstring(r.text)

lords = []

for lord in root:
    l = {}
    l['gender'] = lord.find('Gender').text
    l['dob'] = datetime.datetime.strptime(lord.find('DateOfBirth').text[:10], '%Y-%m-%d')
    l['age'] = int(calculate_age(l['dob']))
    l['party'] = lord.find('Party').text
    l['name'] = lord.find('DisplayAs').text
    l['type'] = lord.find('MemberFrom').text

    # The important numbers - age at 75, 80 and life expectancy
    if args.life:
        l['lifetime'] = int(today.year + ages[l['age']][l['gender']])
    l['age80'] = int(today.year + 80 - l['age'])
    l['age75'] = int(today.year + 75 - l['age'])
    lords.append(l)

header = ['Year', 'Total'] + partynames.values() + ['Oth']
output = []
for year in range(2017, 2061):
    output.append(summarise(year, lords, factor))

if args.csv:
    for l in [header] + output:
        print ','.join(map(str, l))
else:
    print tabulate.tabulate(output, headers=header)

from urllib.request import Request, urlopen
import argparse
from html.parser import HTMLParser
import subprocess
import re
import platform
import io


language_params = {
    'c++17' : {
        'TEMPLATE'    : 'template.cpp',
        'DEBUG_FLAGS' : '-DDEBUG',
        'COMPILE_CMD' : 'g++ -g -std=c++17 -Wall $DBG',
        'RUN_CMD'     : './a.out'
    },
    'go'    : {
        'TEMPLATE'    : 'main.go',
        'COMPILE_CMD' : 'go build $DBG -o a.out',
        'DEBUG_FLAGS' : '''"-ldflags '-X=main.DEBUG=Y'"''',
        'RUN_CMD'     : './a.out'
    },
    'kotlin' : {
        'TEMPLATE'    : 'main.kt',
        'COMPILE_CMD' : 'kotlinc -include-runtime -d out.jar',
        'DEBUG_FLAGS' : "-d",
        'RUN_CMD'     : 'java -jar out.jar $DBG'
    }
}


class ProblemParser(HTMLParser):
    def __init__(self,folder):
        HTMLParser.__init__(self)
        self.folder = folder
        self.num_tests = 0
        self.test_case = None
        self.start_copy = False
    
    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if attrs == [('class','input')]:
                self.num_tests += 1
                self.test_case = io.open(
                    '%s%s%d' % (self.folder, '/input', self.num_tests), 'wb')
            elif attrs == [('class','output')]:
                self.test_case = io.open(
                    '%s%s%d' % (self.folder,'/output' ,self.num_tests), 'wb')
        elif tag == 'pre':
            if self.test_case != None:
                self.start_copy = True
    
    def handle_endtag(self, tag):
        if tag == 'br':
            if self.start_copy:
                self.test_case.write('\n'.encode('utf-8'))
                self.end_line = True
        elif tag == 'pre':
            if self.start_copy:
                if not self.end_line:
                    self.test_case.write('\n'.encode('utf-8'))
                self.test_case.close()
                self.test_case = None
                self.start_copy = False
    def handle_entityref(self, name):
        if self.start_copy:
            self.test_case.write(self.unescape(('&%s;' % name)).encode('utf-8'))

    def handle_data(self, data):
        if self.start_copy:
            self.test_case.write(data.strip('\n').encode('utf-8'))
            self.test_case.write('\n'.encode('utf-8'))
            self.end_line = False



class ContestParser(HTMLParser):

    def __init__(self,contest):
        HTMLParser.__init__(self)
        self.contest = contest
        self.start_contest = False
        self.start_problem = False
        self.name = ''
        self.problem_name = ''
        self.problems = []
        self.problem_names = []

    def handle_starttag(self,tag,attrs):
        if self.name == '' and attrs == [ ('style', 'color: black'), ('href', '/contest/%s' % (self.contest))]:
            self.start_contest = True
        elif tag == 'option':
            if len(attrs) == 1:
                regexp = re.compile(r"'[A-Z][0-9]?'")
                st = str(attrs[0])
                search =  regexp.search(st)
                if search is not None:
                    self.problems.append(search.group(0).split("'")[-2])
                    self.start_problem = True
    def handle_endtag(self,tag):
        if tag == 'a' and self.start_contest:
            self.start_contest = False
        elif self.start_problem:
            self.problem_names.append(self.problem_name)
            self.problem_name = ''
            self.start_problem = False
    def handle_data(self,data):
        if self.start_contest:
            self.name = data
        elif self.start_problem:
            self.problem_name += data


def parse_problem(folder,contest,problem):
    url = 'https://codeforces.com/contest/%s/problem/%s' % (contest,problem)
    html = urlopen(Request(url,headers={"User-Agent": "Mozilla/5.0"}),timeout=20).read()
    parser = ProblemParser(folder)
    parser.feed(html.decode('utf-8'))
    return parser.num_tests



def parse_contest(contest):
    url = 'https://codeforces.com/contest/%s' % (contest)
    html = urlopen(Request(url,headers={"User-Agent": "Mozilla/5.0"}),timeout=20).read()
    parser = ContestParser(contest)
    parser.feed(html.decode('utf-8'))
    return parser

RED_F='\033[31m'
GREEN_F='\033[32m'
BOLD='\033[1m'
NORM='\033[0m'

WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'


if (platform.system() == "Darwin"):
    TIME_CMD='`which gtime` -o time.out -f "(%es)"'
else:
    TIME_CMD='`which time` -o time.out -f "(%es)"'
TIME_AP='`cat time.out`'

def generate_test_script(folder, language, num_tests, problem):
    param = language_params[language]
    open(folder+'/test.sh','x')
    with io.open(folder + '/test.sh', 'w', newline = '\n') as test:
        test.write(
            ('#!/bin/bash\n'
            'DBG=""\n'
            'while getopts ":d" opt; do\n'
            '  case $opt in\n'
            '    d)\n'
            '      echo "-d was selected; compiling in DEBUG mode!" >&2\n'
            '      DBG=' + param["DEBUG_FLAGS"] +'\n'
            '      ;;\n'
            '    \?)\n'
            '      echo "Invalid option: -$OPTARG" >&2\n'
            '      ;;\n'
            '  esac\n'
            'done\n'
            '\n'
            'if ! ' + param["COMPILE_CMD"] +' sol.{0}; then\n'
            '    exit\n'
            'fi\n'
            'INPUT_NAME='+'input'+'\n'
            'OUTPUT_NAME='+'output'+'\n'
            'MY_NAME='+'my_output'+'\n'
            'rm -R $MY_NAME* &>/dev/null\n').format(param["TEMPLATE"].split('.')[1]))
        test.write(
            'for test_file in $INPUT_NAME*\n'
            'do\n'
            '    i=$((${{#INPUT_NAME}}))\n'
            '    test_case=${{test_file:$i}}\n'
            '    if ! {5} {run_cmd} < $INPUT_NAME$test_case > $MY_NAME$test_case; then\n'
            '        echo {1}{4}Sample test \#$test_case: Runtime Error{2} {6}\n'
            '        echo ========================================\n'
            '        echo Sample Input \#$test_case\n'
            '        cat $INPUT_NAME$test_case\n'
            '    else\n'
            '        if diff --brief --ignore-space-change --ignore-blank-lines $MY_NAME$test_case $OUTPUT_NAME$test_case; then\n'
            '            echo {1}{3}Sample test \#$test_case: Accepted{2} {6}\n'
            '        else\n'
            '            echo {1}{4}Sample test \#$test_case: Wrong Answer{2} {6}\n'
            '            echo ========================================\n'
            '            echo Sample Input \#$test_case\n'
            '            cat $INPUT_NAME$test_case\n'
            '            echo ========================================\n'
            '            echo Sample Output \#$test_case\n'
            '            cat $OUTPUT_NAME$test_case\n'
            '            echo ========================================\n'
            '            echo My Output \#$test_case\n'
            '            cat $MY_NAME$test_case\n'
            '            echo ========================================\n'
            '        fi\n'
            '    fi\n'
            'done\n'
            .format(num_tests, BOLD, NORM, GREEN_F, RED_F, TIME_CMD, TIME_AP, run_cmd=param["RUN_CMD"])) 
        test.close()
 


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--language','-l',default='c++17',help='')
    parser.add_argument('contest',help='')
    args = parser.parse_args()
    contest = args.contest
    language = args.language
    print('Parsing contest %s for language %s, please wait...' % (contest,language))
    content = parse_contest(contest)
    print('*** Round Name: ' + content.name + ' ***')
    print('found %d problems! ' % (len(content.problems)))

    TEMPLATE = language_params[language]["TEMPLATE"]

    for index, problem in enumerate(content.problems):
        print('Downloading Problem %s...' % (content.problem_names[index]))
        folder = '%s\%s' % (contest,problem)
        subprocess.run(['mkdir',folder],shell=True)
        subprocess.run(['type','nul','>',folder+'\sol.cpp'],shell=True)
        subprocess.run(['echo','y|copy',TEMPLATE,folder+'\sol.cpp'],shell=True)
        subprocess.run(['@echo','off','timeout','/t','2','>','nul'],shell=True)
        num_tests = parse_problem(folder,contest,problem)
        ex = ''
        if num_tests > 1: ex = 's'
        print('%d sample test%s found.' % (num_tests,ex))
        generate_test_script(folder, language, num_tests, problem)
        print('========================================')
if __name__ == '__main__':
    main()
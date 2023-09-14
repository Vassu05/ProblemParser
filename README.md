
# Problem Parser for Codeforces

Problem Parser is a Python Script the helps in increasing the efficiency during an active Codeforces contest by creating directories and inserting template file for each problem of the contest. 

It also loads sample Inputs and expected outputs along with a pre generated script file to check the written solution. 



## Built With

- Python
- Shell Scripting
## Getting Started

### Prerequisites

- Make sure you have python or python3 installed on your computer.

### Installation

- Download the script files or clone the project using
```bash
git clone https://github.com/Vassu05/ProblemParser.git
```

- Go to the downloaded directory and perform the command
```bash
python3 main.py [CONTEST_NUMBER]
```

Note: Contest number is what appears in the url when you go to the contest, not the round number.

### Usage
 
- Go to the problem folder which you want to solve and open sol.cpp to start writing the solution.

- After writing the solution, run this command while being in the problem directory to test your solution against the samples
```bash
bash test.sh
```
- The test.sh file compares the received output and expected sample output and gives you a verdict right away.


import sys, os, re, copy
import json
import binascii
from z3 import *
from time import perf_counter_ns
from os import listdir
from os.path import isfile, join

#Bench Grammer Patterns
inputpattern = re.compile("INPUT\(([\w]+)\)")
outputpattern = re.compile("OUTPUT\((\w+)\)")
outergatepattern = re.compile("(\w+)\s*=\s*(\w+)\((.+)\)")
unarypattern = re.compile("(\w+)\s*=\s*(\w+)\(\s*(\w+)\s*\)")
#gate support
supportedGates = {"and":[And,"base"],"xor":[Xor,"base"],"or":[Or,"base"],"nand":[And,"composite"],"nor":[Or,"composite"],"nxor":[Xor,"composite"]}
inputGateList = []
password = []

def file_to_LogicTree(filename):
    absFilePath = os.path.join(benchDir,filename)
    z3Funcs = {}
    func = None
    if os.path.exists(absFilePath):
        currentFile = filename
        with open(absFilePath,'r') as openbench:
            line = openbench.readline()
            while line:
                if(line[0] != "#" and line[0] != "\r\n" and line[0] != "\r" and line[0] != "\n"):
                    if(len(re.findall(unarypattern,line))>0):#check for unary gates
                        temp = unarypattern.findall(line)[0]
                        z3Funcs[temp[0]] = Not(z3Funcs.get(temp[2]))
                        func = z3Funcs.get(temp[0])
                    elif(len(re.findall(outergatepattern,line))>0):#check for compound //any gate with n inputs
                        temp = (outergatepattern.findall(line))[0]
                        innertemp = temp[2].split(",")
                        controlVars = supportedGates[temp[1].lower()]
                        listofargs = [z3Funcs.get(x) for x in innertemp]
                        z3Funcs[temp[0]] = Not(controlVars[0](*listofargs)) if controlVars[1] == "composite" else controlVars[0](*listofargs)
                        func = z3Funcs.get(temp[0])
                    elif(len(re.findall(inputpattern,line))>0):#check for inputs
                        temp = inputpattern.findall(line)[0]
                        tempgate = Bool(temp)
                        inputGateList.append(tempgate)
                        z3Funcs[temp] = tempgate
                    elif(len(outputpattern.findall(line))>0):#output is root and must be stored elsewhere
                        pass
                    else:
                        print("Failed to match: ",line)
                line = openbench.readline()
            return func
    else:
        print("File:",filename," does not exist in the directory consume")

def solve(func):
    s = Solver()
    s.add(func)
    return [s.check(),s.model(), s.statistics()]

def setVisitedFiles():
    try:
        with open(os.path.join(tempDir,'visitedfiles.json')) as json_file:
            try:
                visitedFiles = json.load(json_file)
            except:
                print("Caught exception: visitedfiles.json is empty\nThis is the most common exception, however,check the json file to validate integrity as the same error can be thrown when the data is corrupted\n")
    except IOError:
        print("Caught exception file not found: visitedfiles.json\n")

#convert bin to ASCII
def text_from_bits(bits, encoding='utf-8', errors='surrogatepass'):
    n = int(bits, 2)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode(encoding, errors) or '\0'

def rollIter():
    f = []
    for (dirpath, dirnames, filenames) in os.walk(benchDir):
        f.extend(filenames)
        break
    for file_name in f:
        if(file_name in visitedFiles):
            continue
        print(file_name)
        func = file_to_LogicTree(file_name)

        #solution timer 
        start = perf_counter_ns()
        stop = perf_counter_ns()
        start
        solution = solve(func)
        stop
        elapsed = stop-start

        #write results to .txt file
        with open(os.path.join(finalDir,file_name),'a+') as out:
            out.write("Satisfiability:"+str(solution[0])+"\n")
            binaryList = []
            for x in range(len(inputGateList)):
                val = 0 if str(solution[1][inputGateList[x]])=="False" else 1
                password.append(str(val))
                binaryList.append(val)   
            out.write("Detected Password:"+''.join(password)+"\n")
            try:
                out.write("Detected Password in ASCII:"+text_from_bits(''.join(password))+"\n")
            except:
                pass
            out.write("Time elapsed in nanoseconds:"+str(elapsed)+"ns"+"\n")
            out.write("Statistics:" +str(solution[2])+"\n")
            out.write("Model:"+str(solution[1])+"\n")
        visitedFiles.append(file_name)
        with open(os.path.join(tempDir,"visitedfiles.json"),'w') as json_file:
            json.dump(visitedFiles,json_file)

        #clear stored array values
        password.clear()
        inputGateList.clear()

if __name__ == "__main__":
    #Utility Vars and setup
    visitedFiles = []
    currentfile = None
    os.chdir('..')
    cur_path = os.path.dirname(__file__)
    benchDir = os.path.join(os.getcwd(),'consume')
    tempDir = os.getcwd()
    finalDir = os.path.join(os.getcwd(),'final')
    setVisitedFiles()
    #begin
    print("Starting...")
    rollIter()
    print("Finished...")

    

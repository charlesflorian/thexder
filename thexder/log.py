def clearlog():
    open("log","w").close()

def writelog(string):
    f = open("log","a")
    f.write(string)
    f.close()

def newlinelog():
    f = open("log","a")
    f.write("\n")
    f.close()

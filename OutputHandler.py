import os
import datetime
import csv

# Getting current date and time 
CurrentDate=datetime.datetime.now().strftime("%B_%d_%Y")
CurrentTime=datetime.datetime.now().strftime("%I:%M:%S%P")

# Counter to keep track of total number of output files to be generated 
callcount=0

# Writes inputlist(List of dictionaries) into a csv format
# and all keyword arguments as header of the csv file

def writing(inputlist,**kwargs):
    global callcount
    callcount=callcount+1
    datafield=[]
    tempwritebuffer=[]
    currentPath=os.path.dirname(os.path.realpath(__file__))
    OutputPath=os.path.join(currentPath,"Output")

    try:
        os.makedirs(OutputPath)
    except OSError:
        pass

    DateFolderPath=os.path.join(OutputPath,CurrentDate)
    try:
        os.makedirs(DateFolderPath)
    except OSError:
        pass

    dest_dir=os.path.join(DateFolderPath,CurrentTime)
    try:
        os.makedirs(dest_dir)
    except OSError:
        pass
    
    path=os.path.join(dest_dir,"Outputfile"+str(callcount))

    with open(path,'w') as file:
		writer=csv.writer(file,delimiter=',')
		headerString=[]
		saved_args=locals()
		count=0;
		for i in  saved_args['kwargs']:
		    count+=1
		    temp=str(i)+'='+str(saved_args['kwargs'][i])
		    print i,saved_args['kwargs'][i]
		    headerString.append(temp)

		print headerString
		writer.writerow(headerString)
		for keys in sorted(inputlist[0]):
			datafield.append(keys)
			print datafield
		writer.writerow(datafield)
		for dicts in inputlist:
			for keys in sorted(dicts):
				tempwritebuffer.append(dicts[keys])
			writer.writerow(tempwritebuffer)
			tempwritebuffer=[]
#
#_______________________________________________________________________________
#


# Reads the csv file at path 'infilepath'
# writes the csv file's 'header parameters' into header data
# and writes the csv data as a 'list of dictionaries' into 'listofdata'
def reading(infilepath,listofdata,headerdata):
    temp={}
    with open(infilepath,"r") as file:
        reader=csv.reader(file,delimiter=",")
        header = reader.next()
        for k in header:
            datasplit=k.split('=')
            
            try:
                headerdata[datasplit[0]]=float(datasplit[1])
            except ValueError:
                headerdata[datasplit[0]]=datasplit[1]                

        datafields=reader.next()

        for i in reader:
            x=0
            while x<len(datafields):
                try:
                    temp[datafields[x]]=float(i[x])     
                except ValueError:
                    temp[datafields[x]]=None
                x+=1
            listofdata.append(temp)
            temp={}


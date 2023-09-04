import datetime

currentTime = datetime.datetime.now().time()
classtime = datetime.datetime(2020, 5, 13, 9, 10, 00) 
print(currentTime)
print(currentTime > classtime.time())
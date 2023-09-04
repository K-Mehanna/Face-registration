from train import train  # Imports train function from train.py,
import cv2               # OpenCV Version 2,
import face_recognition  # Face Recognition library, and
import numpy as np       # numpy
import datetime


encodings, nameslist = train('static\images') # Sets two variables to the lists returned by the train function
current_len = 0
    
def names(video_capture):   # Declares a function called name which takes a webcam feed as a parameter
    face_locations = []
    face_encodings = []
    face_names = []
    full_names = []
    video_capture = video_capture
    
    # Takes a single frame of the webcam feed
    ret, frame = video_capture.read() #assigns two variables to a boolean confirmation value and the frame

    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:  # Iterates over each face in the frame
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(encodings, face_encoding)
        name = "Unknown"  # Default name is Unknown


        # Or instead, use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:  # Checks that there is a match
            name = nameslist[best_match_index].title()  # Assigns variable to name from list 
            forename = name.split()[0]   # Assigns forename variable to student's first name
        else:
            forename=name

        full_names.append(name)  #List for full names of people in frame
        face_names.append(forename) # List for their first names

    return face_locations, face_names, full_names, frame
    # Returns location of face in frame, first and full names of students in frame, and the frame itself


def display(video_capture):
    video_capture = video_capture
    while True:
        face_locations, face_names, full_names, frame = names(video_capture)
        

        # Display the results
        for (top, right, bottom, left), forename in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            if forename != "Unknown":
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            else:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)

            # Draw a label with a name below the face
            
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, forename, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        # Encode frame from webcam feed as a jpg
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # "returns" frame then returns to the start of the while loop
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result



def difference(lesson_time, current_time):
    # Calculates difference between current time and lesson start time
    FMT = '%H:%M'
    tdelta = str(datetime.strptime(current_time, FMT) - datetime.strptime(lesson_time, FMT)).split(":")
    if tdelta[0] == '0':
        delta = tdelta[1]
        return delta
    else:
        delta = 60 + int(tdelta[1])
        return delta


def lessons():
    # Calculates studnts attendance, the time of the current lesson, the current day, and the current week
    currentDate = datetime.datetime.now()
    currentDay = currentDate.strftime("%A")
    currentWeek = currentDate.strftime("%W")
    currentTime = currentDate.strftime("%X")[:-3]

    # Determines whether it is a week A or B
    if int(currentWeek) % 2 == 1:
        week = "A"
    else:
        week = "B"

    # Determines whether student is on time, and if late then by how many minutes
    attendance = "L"
    if "9:10" <= currentTime <= "10:15":
        classTime = "9:15"
        if "9:10" <= currentTime <= "9:20":
            attendance = "/"
        else:
            delta = difference(classTime, currentTime)
            attendance = "L: " + delta
            
    elif "10:30" <= currentTime <= "11:35":
        classTime = "10:35"
        if "10:30" <= currentTime <= "10:40":
            attendance = "/"
        else:
            delta = difference(classTime, currentTime)
            attendance = "L: " + delta

    elif "11:30" <= currentTime <= "12:35":
        classTime = "11:35"
        if "11:30" <= currentTime <= "11:40":
            attendance = "/"
        else:
            delta = difference(classTime, currentTime)
            attendance = "L: " + delta

    elif "13:30" <= currentTime <= "14:35":
        classTime = "13:35"
        if "13:30" <= currentTime <= "13:40":
            attendance = "/"
        else:
            delta = difference(classTime, currentTime)
            attendance = "L: " + delta

    elif "14:30" <= currentTime <= "15:35":
        classTime = "14:35"
        if "14:30" <= currentTime <= "14:40":
            attendance = "/"
        else:
            delta = difference(classTime, currentTime)
            attendance = "L: " + delta
    else:
        attendance = 0
        classTime = "Invalid"
        
    return attendance, classTime, currentDay, week
    


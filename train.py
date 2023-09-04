import face_recognition # Imports the face recognition library
import os   # and os, which is used for navigating filesystems

def train(directory):    # Declares a function which takes the folder containing the images as a parameter
    directory = directory
    names = []
    encodings = []

    for filename in os.listdir(directory):  #Iterates through each file in the folder
        name = os.path.splitext(filename)[0]   # Splits the filename into the name and the extension
        names.append(name.title())  # Capitalises the start of every word

        location = os.path.join(directory, filename)   # Sets the variable equal to the location of the file
        image = face_recognition.load_image_file(location) # Loads the image in that location
        face_encoding = face_recognition.face_encodings(image)[0]  # Creates the encoding for that file
        encodings.append(face_encoding)  # Appends the encoding to a list
        
    return encodings, names  # Returns the encodings and names of each student in the folder,
                             # where the same index corresponds to the same student in both lists





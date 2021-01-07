import time
from pathlib import Path

import numpy as np
import cv2
# import pafy
import matplotlib.pyplot as plt

# #url of the video to predict Age and gender
# url = 'https://www.youtube.com/watch?v=c07IsbSNqfI&feature=youtu.be'
# vPafy = pafy.new(url)
# play = vPafy.getbest(preftype="mp4")

# cap = cv2.VideoCapture(play.url)

# cap.set(3, 480) #set width of the frame
# cap.set(4, 640) #set height of the frame

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']

gender_list = ['Male', 'Female']

BASE_PATH = Path(r"C:\Data\GIT\python_opencv_gender_age_classification")

def load_caffe_models():
 
    age_net = cv2.dnn.readNetFromCaffe(str(Path(BASE_PATH, 'deploy_age.prototxt')), str(Path(BASE_PATH, 'age_net.caffemodel')))
    
    path_prototxt = str(Path(BASE_PATH, "deploy_gender.prototxt"))
    caffemodel_path = str(Path(r"C:\Data\GIT\python_opencv_gender_age_classification\gender_net.caffemodel"))
    gender_net = cv2.dnn.readNetFromCaffe(path_prototxt, caffemodel_path)

    return(age_net, gender_net)

def detect_faces(cascade_path, test_image, scaleFactor = 1.1):
    # create a copy of the image to prevent any changes to the original one.
    image_copy = test_image.copy()

    #convert the test image to gray scale as opencv face detector expects gray images
    gray_image = cv2.cvtColor(image_copy, cv2.COLOR_BGR2GRAY)
    

    print(cascade_path)
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Applying the haar classifier to detect faces
    faces_rect = face_cascade.detectMultiScale(gray_image, scaleFactor=scaleFactor, minNeighbors=5)
    
    return faces_rect
    # for (x, y, w, h) in faces_rect:
        # cv2.rectangle(image_copy, (x, y), (x+w, y+h), (0, 255, 0), 15)

    # return image_copy

def age_and_gender_from_picture(picture_path, age_net, gender_net, display=False):
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    image = cv2.imread(picture_path,0) # reads image 'opencv-logo.png' as grayscale
    
    #loading image
    image = cv2.imread(picture_path)

    faces = detect_faces(
        str(Path(BASE_PATH,'haarcascade_frontalface_alt.xml')),  # was haarcascade_frontalface_alt
        image,
        1.1,
        )
    
    if(len(faces)>0):
        print("Found {} faces".format(str(len(faces))))
    
    for (x, y, w, h )in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 255, 0), 2)

    #Get Face 
        face_img = image[y:y+h, h:h+w].copy()
        blob = cv2.dnn.blobFromImage(face_img, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

    #Predict Gender
        gender_net.setInput(blob)
        gender_preds = gender_net.forward()
        gender = gender_list[gender_preds[0].argmax()]
        print("Gender : " + gender)

    #Predict Age
        age_net.setInput(blob)
        age_preds = age_net.forward()
        age = age_list[age_preds[0].argmax()]
        print("Age Range: " + age)

        overlay_text = "%s %s" % (gender, age)
        cv2.putText(image, overlay_text, (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    if display:    
        scale_percent = 60 # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

        cv2.namedWindow( "Display window"); #  Create a window for display.
        cv2.resizeWindow("Display window", 100, 100)
        cv2.imshow( "Display window", image );                    #  Show our image inside it.

    # return (

    # cv2.imshow('frame', image)  
    #0xFF is a hexadecimal constant which is 11111111 in binary.
    # if cv2.waitKey(1) & 0xFF == ord('q'): 
    #    time.sleep(2)

    # time.sleep(10)

    # cv2.imshow('dst_rt', img)
    cv2.waitKey(0)
       

if __name__ == "__main__":
    age_net, gender_net = load_caffe_models()

    PICTURES_BASE_PATH = Path(r"C:\Temp\memcard9\20210106")
    picture_path = str(Path(PICTURES_BASE_PATH, "IMG_20210106_170638379.jpg"))
    # picture_path = str(Path(PICTURES_BASE_PATH, "IMG_20210106_170247561_BURST000_COVER_TOP.jpg")
    age_and_gender_from_picture(picture_path, age_net, gender_net, display=True)

import time
from pathlib import Path

import numpy as np
import cv2
# import pafy
import matplotlib.pyplot as plt

import classification_database_operations

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

def age_and_gender_from_picture(picture_path, age_net, gender_net, display=False, save_path=None):
    # ONLY RETURN DATA FOR ONE FACE


    font = cv2.FONT_HERSHEY_SIMPLEX
    
    picture_path = str(picture_path)

    image = cv2.imread(picture_path,0) # reads image 'opencv-logo.png' as grayscale
    
    #loading image
    image = cv2.imread(picture_path)


    # haar_cascade = 'haarcascade_frontalface_alt.xml'
    haar_cascade = 'haarcascade_frontalface_default.xml'
    faces = detect_faces(
        str(Path(BASE_PATH,haar_cascade)),  
        image,
        1.1,
        )
    
    if(len(faces)>0):
        print("Found {} faces".format(str(len(faces))))
    

    gender = "no_face_found"
    gender_text = "no_face_found"
    age = "no_age_found"
    return_dict = {
        "age_guess_min":0,
        "age_guess_max":0,
        "gender":"unknown",
        "gender_percentage":0,
        "faces_count":0,
        }

    # biggest rectangle most likely match
    biggest_face_index = 0
    biggest_face_width = 0

    for i, (x, y, w, h )in enumerate(faces):
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 255, 0), 2)

        #Get Face 
        face_img = image[y:y+h, h:h+w].copy()
        blob = cv2.dnn.blobFromImage(face_img, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

        #Predict Gender
        gender_net.setInput(blob)
        gender_preds = gender_net.forward()
        print(gender_preds)

        i = gender_preds[0].argmax()
        print(i)
        percentage = round((gender_preds[0][i] * 100),1)
        gender = gender_list[i]
        gender_text = "{} ({}%)".format(gender, percentage)
        print("Gender : {} ({}%)".format(gender, percentage))

        #Predict Age
        age_net.setInput(blob)
        age_preds = age_net.forward()
        age = age_list[age_preds[0].argmax()]
        print("Age Range: " + age)

        overlay_text = "%s %s" % (gender_text, age)
        cv2.putText(image, overlay_text, (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

        if w >biggest_face_width:
            biggest_face_index = i
            biggest_face_width = w
            return_dict = {
                "age_guess_min":age,
                "age_guess_max":age,
                "gender":gender,
                "gender_percentage":percentage,
                "faces_count":len(faces),
                }


    if display:    
        scale_percent = 30 # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)

        cv2.namedWindow( "Display window"); #  Create a window for display.
        cv2.resizeWindow("Display window", 100, 100)
        cv2.imshow( "Display window", image );                    #  Show our image inside it.

        cv2.waitKey(0)

    if save_path is not None:

        path_part = save_path.parent

        gender_path = Path(path_part, return_dict["gender"])
        new_name = "{}({}%)_{}_{}".format(return_dict["gender"], return_dict["gender_percentage"], age, save_path.name)

        if not gender_path.is_dir():
            gender_path.mkdir(parents=True, exist_ok=True)
            print(gender_path)

        final_save_path = str(Path(gender_path, new_name))

        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
        cv2.imwrite(final_save_path, image_gray)

    return return_dict

# def classify_directory(dir, save_dir, age_net, gender_net):
#     files = sorted(Path(dir).glob('*.jpg'))  # all files in current directory, no directory names.

#     for i, picture_path in enumerate(files):
#         print("process picture: {} of {}. ({})".format(
#             i,
#             len(files),
#             picture_path,
#             ))

#         picture_name = Path(picture_path).name
#         # picture_path = Path(PICTURES_BASE_PATH, picture_name)
#         picture_save_path = Path(save_dir, picture_name)

#         age_and_gender_from_picture(picture_path, age_net, gender_net, display=False, save_path=picture_save_path)

def process_picture_from_database(record, save_dir, age_net, gender_net):
    picture_path = Path(record["path"])

    picture_name = Path(picture_path).name

    picture_save_path = Path(save_dir, picture_name)

    return age_and_gender_from_picture(picture_path, age_net, gender_net, display=False, save_path=picture_save_path)


def process_pictures_from_database( save_dir, age_net, gender_net):
    DATABASE_PATH = r"C:\Temp\memcard9\classification\classification.db"
    db = classification_database_operations.ImageClassificationDatabaseOperations(DATABASE_PATH)
    
    records = db.get_records_by_status_and_change_status("TODO", "BUSY", count=10)
    while len(records)>0:
    
        for record in records:
            print(record)
            try:
                classification_data = process_picture_from_database(record, save_dir, age_net, gender_net)
                classification_data["primary_key_name"] = record["primary_key_name"]
                classification_data["primary_key_value"] = record["primary_key_value"]
                classification_data["process_status"] = "DONE"
                db.update_record(classification_data)
            except Exception as e:
                print("FAILED!!!")
                print(e)

        records = db.get_records_by_status_and_change_status("TODO", "BUSY", count=10)

    
def add_directory_to_database():

    
    # PICTURES_BASE_PATH = Path(r"C:\Temp\memcard9\20210106")
    # PICTURES_BASE_PATH = Path(r"C:\Temp\memcard9\20201013")
    # PICTURES_BASE_PATH = Path(r"C:\Temp\memcard9\20201013\nikon")

    DATABASE_PATH = r"C:\Temp\memcard9\classification\classification.db"
    db = classification_database_operations.ImageClassificationDatabaseOperations(DATABASE_PATH)

   
    db.add_directory(Path(r"C:\Temp\memcard9\20201013\nikon"))

def independent_classify_one_picture():
    
    PICTURES_SAVE_SUBFOLDER = "classified"
    PICTURES_BASE_PATH = r"C:\Temp\memcard9\20210106"
    pictures_save_base_path = Path(PICTURES_BASE_PATH, PICTURES_SAVE_SUBFOLDER)

    picture_name = "IMG_20210106_164121656_BURST000_COVER_COMP.jpg"
    picture_path = Path(PICTURES_BASE_PATH, picture_name)
    picture_save_path = Path(pictures_save_base_path, picture_name)

    print(age_and_gender_from_picture(picture_path, age_net, gender_net, display=True, save_path=picture_save_path))


if __name__ == "__main__":

    age_net, gender_net = load_caffe_models()
    add_directory_to_database()
    
    process_pictures_from_database(r"C:\Temp\memcard9\classification\results",age_net, gender_net)

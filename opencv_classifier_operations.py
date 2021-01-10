import time
from pathlib import Path

import numpy as np
import cv2
import matplotlib.pyplot as plt


MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']

gender_list = ['Male', 'Female']

OVERLAY_TEXT_COLOUR =  (255, 83, 232)


class Classifier:

    def __init__(self, base_path, face=False, age=False, gender=False):
        self.age_net = None
        self.gender_net = None
        self.face_cascade = None
        
        self.base_path = base_path

        self.load_haar_cascades(face)
        if not face and (age or gender):
            print("To detect age or gender, face detection needs to be active")
            raise ValueError

        self.load_caffe_models(age, gender)
        self.image = None

        self.overlay_text_colour = OVERLAY_TEXT_COLOUR

        self.reset()

    def get_image(self):
        return self.image

    def set_image(self, image):
        self.image = image
        
    def load_image(self, picture_path):
         
        picture_path = str(picture_path)

        image = cv2.imread(picture_path,0) # reads image 'opencv-logo.png' as grayscale
        
        #loading image
        image = cv2.imread(picture_path)

        # create a copy of the image to prevent any changes to the original one.
        self.image = image.copy()
    
    def reset(self):
        self.faces = []
        
        cv2.destroyAllWindows()
        if self.image is not None:
            try:
                self.image.release()
            except Exception as e:
                pass

            self.image = None

    def save_picture(self, save_path):
        image_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(save_path, image_gray)
       
    def display_picture(self, wait_for_user=True):
        h, w, channels = self.image.shape

        scale_percent = 100  # percent of original size
        while w > 1000:
            scale_percent *= 0.9
            w*=0.9

        width = int(self.image.shape[1] * scale_percent / 100)
        height = int(self.image.shape[0] * scale_percent / 100)
        dim = (width, height)

        display_image = cv2.resize(self.image, dim, interpolation = cv2.INTER_AREA)

        cv2.namedWindow( "Display window");  # Create a window for display.
        # cv2.resizeWindow("Display window", 100, 100)
        cv2.imshow( "Display window", display_image);  #  Show our image inside it.

        if wait_for_user:
            cv2.waitKey(0)  

    ########################
    # haar cascade object recognition

    def load_haar_cascades(self, face=False):
        if face:
            haar_cascade = 'haarcascade_frontalface_alt.xml'
            haar_cascade = 'haarcascade_frontalface_default.xml'

            face_cascade_path = str(Path(self.base_path, haar_cascade))
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)

    def detect_faces(self, scaleFactor = 1.1):
        #convert the test image to gray scale as opencv face detector expects gray images
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # Applying the haar classifier to detect faces
        self.faces = self.face_cascade.detectMultiScale(gray_image, scaleFactor=scaleFactor, minNeighbors=5)

    ########################
    # caffe models

    def load_caffe_models(self, age=False, gender=False ):
        if age:
            path_prototext_age = str(Path(self.base_path, 'deploy_age.prototxt'))
            caffemodel_path_age = str(Path(self.base_path,"age_net.caffemodel"))
            self.age_net = cv2.dnn.readNetFromCaffe(path_prototext_age, caffemodel_path_age)

        if gender:
            path_prototxt_gender = str(Path(self.base_path, "deploy_gender.prototxt"))
            caffemodel_path_gender = str(Path(self.base_path,"gender_net.caffemodel"))
            self.gender_net = cv2.dnn.readNetFromCaffe(path_prototxt_gender, caffemodel_path_gender)

    def detect_age_gender(self):

        self.detect_faces()

        print(self.faces)
        
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

        font = cv2.FONT_HERSHEY_SIMPLEX

        self.draw_faces()
        biggest_faces = self.get_biggest_faces(count=1)
        
        for i, (x, y, w, h )in enumerate(biggest_faces):
            # cv2.rectangle(self.image, (x, y), (x+w, y+h), (255, 255, 0), 2)

            #Get Face 
            face_img = self.image[y:y+h, h:h+w].copy()


            blob = cv2.dnn.blobFromImage(face_img, 1, (227, 227), MODEL_MEAN_VALUES, swapRB=False)

            #Predict Gender
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()

            i = gender_preds[0].argmax()
            percentage = round((gender_preds[0][i] * 100),1)
            gender = gender_list[i]
            gender_text = "{} ({}%)".format(gender, percentage)
            tmp_txt = "Gender : {} ({}%)".format(gender, percentage)

            #Predict Age
            self.age_net.setInput(blob)
            age_preds = self.age_net.forward()
            age = age_list[age_preds[0].argmax()]
            print("{} , Age Range: {}".format(tmp_txt,age))

            overlay_text = "%s %s" % (gender_text, age)
            cv2.putText(self.image, overlay_text, (x, y), font, 1, self.overlay_text_colour, 2, cv2.LINE_AA)

            # if w >biggest_face_width:
                # biggest_face_index = i
                # biggest_face_width = w
            return_dict = {
                "age_guess_min":age,
                "age_guess_max":age,
                "gender":gender,
                "gender_percentage":percentage,
                "faces_count":len(self.faces),
                }
        return return_dict

    def get_biggest_faces(self, count=1):
        if count != 1:
            print("not implemented yet")
            raise NotImplementedError

        if len(self.faces) == 0:
            return []

        # biggest rectangle most likely match
        biggest_face_index = 0
        biggest_face_width = 0

        for i, (x, y, w, h )in enumerate(self.faces):
            if w >biggest_face_width:
                biggest_face_index = i
                biggest_face_width = w
        
        return [self.faces[biggest_face_index]]

    def draw_face(self, face):
        # for (x, y, w, h) in faces_rect:
        x,y,w,h = face
        cv2.rectangle(self.image, (x, y), (x+w, y+h), self.overlay_text_colour, 3)  # rgb

    def draw_faces(self):
        # show faces as rectangles
        for face in self.faces:
            self.draw_face(face)

    def draw_text(self, overlay_text, pos_x, pos_y):
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(self.image, overlay_text, (pos_x, pos_y), font, 1, self.overlay_text_colour, 2, cv2.LINE_AA)

if __name__ == "__main__":
    pass
  
    

    
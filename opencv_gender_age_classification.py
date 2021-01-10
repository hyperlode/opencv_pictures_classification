import time
from pathlib import Path

import numpy as np
import cv2
# import matplotlib.pyplot as plt

import classification_database_operations
import opencv_classifier_operations

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

age_list = ['(0, 2)', '(4, 6)', '(8, 12)', '(15, 20)', '(25, 32)', '(38, 43)', '(48, 53)', '(60, 100)']

gender_list = ['Male', 'Female']

BASE_PATH = Path(r"C:\Data\GIT\python_opencv_gender_age_classification")
DATABASE_PATH = r"C:\Temp\memcard9\classification\classification.db"

#################################
#   ONE PICTURE

def age_and_gender_from_picture(picture_path, display=False, save_path=None):
    # ONLY RETURN DATA FOR ONE FACE

    classifier = opencv_classifier_operations.Classifier(BASE_PATH, True, True, True)
    classifier.load_image(picture_path)

    return_dict = classifier.detect_age_gender()

    if display:    
        classifier.display_picture()

    if save_path:
        path_part = save_path.parent

        gender_path = Path(path_part, return_dict["gender"])
        new_name = "{}({}%)_{}_{}".format(return_dict["gender"], return_dict["gender_percentage"], return_dict["age_guess_max"], save_path.name)

        if not gender_path.is_dir():
            gender_path.mkdir(parents=True, exist_ok=True)
            print(gender_path)

        final_save_path = str(Path(gender_path, new_name))

        classifier.save_picture(final_save_path)

    return return_dict

##################################
# MULTIPLE PICTURES

def process_picture_from_database(record, save_dir):
    picture_path = Path(record["path"])

    picture_name = Path(picture_path).name

    picture_save_path = Path(save_dir, picture_name)

    return age_and_gender_from_picture(picture_path, display=False, save_path=picture_save_path)

def process_pictures_from_database( save_dir):
    db = classification_database_operations.ImageClassificationDatabaseOperations(DATABASE_PATH)
    
    records = db.get_records_by_status_and_change_status("TODO", "BUSY", count=10)
    while len(records)>0:
    
        for record in records:
            print(record)
            try:
                classification_data = process_picture_from_database(record, save_dir)
                classification_data["primary_key_name"] = record["primary_key_name"]
                classification_data["primary_key_value"] = record["primary_key_value"]
                classification_data["process_status"] = "DONE"
                db.update_record(classification_data)
            except Exception as e:
                print("FAILED!!!")
                print(e)

        records = db.get_records_by_status_and_change_status("TODO", "BUSY", count=10)
    
def add_directory_to_database(directory):
    db = classification_database_operations.ImageClassificationDatabaseOperations(DATABASE_PATH)
    db.add_directory(Path(directory))

def restore_faulty_busy_database():
    db = classification_database_operations.ImageClassificationDatabaseOperations(DATABASE_PATH)
    db.reset_busy_to_todo_all_records()


#################################
#   VIDEO 

def process_videos_in_directory(directory, extensions, frames_per_check=5, video_out_directory=None):

    extensions = [e.lower() for e in extensions]

    files = []
    for extension in extensions:
        files.extend (sorted(Path(directory).glob('*.{}'.format(extension))))  # all files in current directory, no directory names.
        print(extension)
    print(files)
    for i, video_path in enumerate(files):
        print("videos to process: {} of {}. ({})".format(
            i,
            len(files),
            video_path,
            ))

        detect_from_video(video_path=video_path, frames_per_check=5, video_out_directory=video_out_directory)
    
        

#################################
#   ONE PICTURE

def independent_classify_one_picture():
    
    PICTURES_SAVE_SUBFOLDER = "classified"
    PICTURES_BASE_PATH = r"C:\Temp\memcard9\20210106"
    pictures_save_base_path = Path(PICTURES_BASE_PATH, PICTURES_SAVE_SUBFOLDER)

    picture_name = "IMG_20210106_164121656_BURST000_COVER_COMP.jpg"
    picture_path = Path(PICTURES_BASE_PATH, picture_name)
    picture_save_path = Path(pictures_save_base_path, picture_name)

    print(age_and_gender_from_picture(picture_path, display=True, save_path=picture_save_path))

#################################
#   ONE VIDEO
def process_one_video():
    video_path = None
    # video_path = r"C:\Temp\memcard9\202003xx\2020-03-26 21-48-41.mp4"
    # video_path = r"C:\Temp\memcard9\20210106\VID_20210106_163232639.mp4"
    # video_path = r"C:\Temp\memcard9\20210106\VID_20210106_163801073.mp4"
    video_path = r"C:\Temp\memcard9\202003xx\2020-03-26 21-45-55.mp4"

    # video_path = r"C:\Users\lode.ameije\Videos\Goli memories\2020-04-05 16-18-40.mp4"  # m
    # video_path = r"C:\Temp\memcard9\20210106\VID_20210106_164259315.mp4"  # mixed
    video_out_directory = Path(r"c:\Temp\memcard9\classification")
    detect_from_video( video_path, 10, video_out_directory)

def detect_from_video(video_path=None, frames_per_check=5, video_out_directory=None):

    classifier = opencv_classifier_operations.Classifier(BASE_PATH, True, True, True)

    if video_path is not None:
        video_capture= cv2.VideoCapture(str(video_path))

    else:
        video_capture = cv2.VideoCapture(0)
    
    # Default resolutions of the frame are obtained.The default resolutions are system dependent.
    # We convert the resolutions from float to integer.
    frame_width = int(video_capture.get(3))
    frame_height = int(video_capture.get(4))

    if video_out_directory is not None:
        # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
        # Define the fps to be equal to 10. Also frame size is passed.

        video_out_directory = Path(video_out_directory)
        if video_path is None:
            name = "cam"

        else:
            name = Path(video_path).stem

        video_out_path = Path(video_out_directory, "{}_overlayed.avi".format(name))
        print(video_out_path)

        out = cv2.VideoWriter(str(video_out_path),
            cv2.VideoWriter_fourcc('M','J','P','G'),
            10,
            (frame_width,frame_height))

    frames_checked = 0
    frame_count = 0
    gender_percentages_average = [0,0]
    gender_samples = [0,0]
    
    while True:
        while True:
            # Capture frame-by-frame
            ret, frame = video_capture.read()
            frame_count += 1

            if (frame_count % frames_per_check) == 0:
                break
        
        frames_checked +=1
        
        if frame is None:
            # end of video file
            break
        classifier.set_image(frame)
        
        results= classifier.detect_age_gender()

        i = 666
        if (results["gender"] == gender_list[0]):
            i = 0
        elif  (results["gender"] == gender_list[1]):
            i = 1
        
        if i != 666:
            gender_percentages_average[i] = round((results["gender_percentage"]  + gender_percentages_average[i] * gender_samples[i]) / (gender_samples[i] + 1),1)
            gender_samples[i] += 1

        overlay_text = "Male:{}({}%), Female:{}({}%) frame check:{}/{}".format(
            gender_samples[0],
            gender_percentages_average[0],
            gender_samples[1],
            gender_percentages_average[1],
            frames_checked,
            frame_count,
            )
                
        classifier.draw_text(overlay_text, 10, 50)
        
        
        if video_out_directory is not None:
            out.write(classifier.get_image())

        # Display the resulting frame
        # cv2.imshow('Video', frame)
        classifier.display_picture(wait_for_user=False)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release everything if job is finished
    # image.release()
    out.release()
    classifier.reset()

if __name__ == "__main__":

    # independent_classify_one_picture()

    # restore_faulty_busy_database()
    # add_directory_to_database(r"C:\Temp\memcard9\20210106\google compressed")
    # process_pictures_from_database(r"C:\Temp\memcard9\classification\results")

    # process_one_video()

    video_out_directory = Path(r"c:\Temp\memcard9\classification")
    detect_from_video(None, 5, video_out_directory)

    # video_directory = r"C:\Temp\memcard9\20210106" 
    # video_directory = r"C:\Temp\memcard9\20210106" 
    # video_directory = r"C:\Temp\memcard9\202003xx" 
    # video_out_directory = Path(r"c:\Temp\memcard9\classification")
    # process_videos_in_directory(video_directory, ["mp4"], 10, video_out_directory)

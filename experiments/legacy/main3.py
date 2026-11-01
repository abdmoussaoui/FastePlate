# import os

# # Débloquer l'accès au dossier (Windows)
# dataset_path = r"D:\cours licence\s6\FastePlate\moroccan-license-plate-detection-4"
# os.system(f'attrib -R "{dataset_path}" /S /D')

# # Vérifier si le dossier est accessible
# if os.access(dataset_path, os.R_OK):
#     print("Le dossier est accessible !")
# else:
#     print("Problème d'accès au dossier.")



# get dataset from roboflow

# from ultralytics import YOLO
# from IPython.display import display,Image

# from roboflow import Roboflow
# rf = Roboflow(api_key=os.environ["ROBOFLOW_API_KEY"])
# project = rf.workspace("naima-el-menani").project("moroccan-license-plate-detection")
# version = project.version(4)
# dataset = version.download("yolov8")


# real work goes here:

# import os
# os.chdir(r"D:\cours licence\s6\FastePlate\moroccan-license-plate-detection-4")
from ultralytics import YOLO
import cv2
import numpy as np
import matplotlib.pyplot as plt
from  segmentation import segment_characters
from segmentation import segment_characters_histogram



# 9lb 3la had util
import util

# sort kayn
from sort.sort import *

from util import get_car ,read_license_plate,write_csv


results ={}
mot_tracker = Sort()


# load model

cocco_model = YOLO('yolov8n.pt')
license_plate_detector = YOLO('best.pt')

# load video
cap = cv2.VideoCapture('maroc.jpg')

# pour d autre type de véhicules:
vehicles =[2,3,5,7]

# read frames:
frame_nmr=-1
ret = True

while ret:
    frame_nmr+=1
    ret,frame =cap.read()
    if ret :
        results[frame_nmr]={}
        # print(results)
        
        # detect vehicules
        detections =cocco_model(frame)[0]
        detections_=[]
        for detection in detections.boxes.data.tolist():
            x1,y1,x2,y2,score,class_id=detection
            if int(class_id) in vehicles:
                detections_.append([x1,x2,y1,y2,score])
                
        # track vehicles :
        
        track_ids = mot_tracker.update(np.asarray(detections_))
        # print('track_ids',track_ids)

        
        # detect licence :
        license_plates = license_plate_detector(frame)[0]
        for license_plate in license_plates.boxes.data.tolist()[0:1]:
            x1,y1,x2,y2 ,score,class_id=license_plate
            
            # assign license plate to car
            xcar1,ycar1,xcar2,ycar2,car_id=get_car(license_plate,track_ids)
            
            # if car_id !=-1:
                
            # crop license plate
            license_plate_crop = frame[int(y1):int(y2),int(x1):int(x2),:]
            
            #  process license plate
            license_plate_crop_gray = cv2.cvtColor(license_plate_crop,cv2.COLOR_BGR2GRAY)
            # moussaoui
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            license_plate_crop_gray = clahe.apply(license_plate_crop_gray)
            # fin moussaoui
            _,license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray,64,25,cv2.THRESH_BINARY_INV)

            # cv2.imshow('original_crop',license_plate_crop)
            # cv2.imshow('threshhold',license_plate_crop_thresh)

            plt.imshow(cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2RGB))
            # plt.imshow(cv2.cvtColor(license_plate_crop_thresh, cv2.COLOR_BGR2RGB))
            plt.axis('off')
            plt.show()
            
            # segmentation des caracteres : 
           
        segment_characters(license_plate_crop)
        # print(segment_characters(license_plate_crop))
        # segment_characters_histogram(license_plate_crop)
               

            

           




# import easyocr

# reader = easyocr.Reader(['ar','en'], gpu=False)  # Langue arabe (pour le Maroc)
# text = reader.readtext('maroc.jpg', detail=0)
# print("Numéro détecté :", text)

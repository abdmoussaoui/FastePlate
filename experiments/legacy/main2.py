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
import pandas as pd
import matplotlib.pyplot as plt



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
cap = cv2.VideoCapture('testfolder/4.jpg')

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
        for license_plate in license_plates.boxes.data.tolist():
            x1,y1,x2,y2 ,score,class_id=license_plate
            
            # assign license plate to car
            xcar1,ycar1,xcar2,ycar2,car_id=get_car(license_plate,track_ids)
            
            # if car_id !=-1:
                
            # crop license plate
            license_plate_crop = frame[int(y1):int(y2),int(x1):int(x2),:]
            
            #  process license plate
            # license_plate_crop_gray = cv2.cvtColor(license_plate_crop,cv2.COLOR_BGR2GRAY)
            # # moussaoui
            # clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            # license_plate_crop_gray = clahe.apply(license_plate_crop_gray)
            # # fin moussaoui
            # _,license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray,64,25,cv2.THRESH_BINARY_INV)

            # cv2.imshow('original_crop',license_plate_crop)
            # cv2.imshow('threshhold',license_plate_crop_thresh)

            # plt.imshow(cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2RGB))
            # plt.imshow(cv2.cvtColor(license_plate_crop_thresh, cv2.COLOR_BGR2RGB))
            # plt.axis('off')
            # plt.show()
            
            print(license_plate_crop.shape)
            h,w,c = license_plate_crop.shape
            ar= w/h
            targetwidth = 600
            targetheight = int(targetwidth/ar)
            # license_plate_crop = cv2.resize(license_plate_crop,(targetwidth,targetheight),interpolation=cv2.INTER_CUBIC)
            
            # plt.imshow(license_plate_crop)
            # plt.imshow(cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2RGB))
            # plt.show()

            
            # blurring and spliting
            license_plate_crop_blf = cv2.bilateralFilter(license_plate_crop,5,7,7)
            
            lab = cv2.cvtColor(license_plate_crop_blf,cv2.COLOR_BGR2LAB)
            l,a,b = cv2.split(lab)
            
            # clhe
            clahe = cv2.createCLAHE(clipLimit=2.0 , tileGridSize=(8,4))
            cl=clahe.apply(l)
            limg = cv2.merge((cl,a,b))
            # coulor conversion
            
            cimg = cv2.cvtColor(limg,cv2.COLOR_LAB2BGR)
            gray = cv2.cvtColor(cimg,cv2.COLOR_BGR2GRAY)
            # plt.imshow(gray,cmap='gray')
            # plt.show()
            
            
            # determinig background color : 
            
            def check_bg_color(image):
                
                check = cv2.threshold(image,0,255,cv2.THRESH_OTSU)[1]
                print(check)
                
                u,c =np.unique(check,return_counts=True)
                d=dict(zip(u,c))
                print(d)
                
                srt = sorted(d.items(),key=lambda x : x[1],reverse=True)
                print(srt)
                
                return srt[0][0]
            
            
            bg_color = check_bg_color(gray)
            
            #  check bachground color  : 
            
            if bg_color == 255 :
                
                ret4,final_img2 = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
                
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
                
                morp = cv2.morphologyEx(final_img2,cv2.MORPH_OPEN,(5,5))
                
                plt.imshow(morp,cmap='gray')
                plt.show()
                
            elif bg_color ==0 :
                ret4,final_img2 = cv2.threshold(gray,0,255,cv2.THRESH_OTSU)
                
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
                
                morp = cv2.morphologyEx(final_img2,cv2.MORPH_OPEN,(5,5))
                
                plt.imshow(morp,cmap='gray')
                plt.show()
                
            #  jusque ici c bon mais pas unssifisant :

                
            # horizontal projections :
            
            # im = morp.copy()
            
            # horizontal_hist = np.sum(im,axis=1,keepdims=True)/255
            # v= horizontal_hist.flatten()
            
            # df=pd.DataFrame(v)
            # df=df.T
            
            # plloting horizontal:
            
            # df.plot(kind='barh',color='k',legend=False , figsize=(3,4))
            # plt.tick_params(axis='y',which='both',labelright=True,right=True,labelleft=False,left=False)
            
            # u=np.max(df.values)+20
            # plt.xlim(u,0)
            # plt.gca().invert_yaxis()
            # plt.show()
            
                
            
            

                # read licen plate number
            license_plate_text,license_plate_text_score = read_license_plate(morp)
            print(license_plate_text)
            # if license_plate_text is None:
            #     # results[frame_nmr][car_id]={'car':{'bbox':[xcar1,ycar1,xcar2,ycar2]},
            #     #                         'license_plate':{'bbox':[x1,y1,x2,y2]  ,
            #     #                         'text':license_plate_text,
            #     #                         'text_score':license_plate_text_score}}
                
                # print('لاانمةكك')

            #             # print(results)
              

# write results

# print('tex',license_plate_text)
# write_csv(results,'results.csv')




# import easyocr

# reader = easyocr.Reader(['ar','en'], gpu=False)  # Langue arabe (pour le Maroc)
# text = reader.readtext('maroc.jpg', detail=0)
# print("Numéro détecté :", text)

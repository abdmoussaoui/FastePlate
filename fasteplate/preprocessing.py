import cv2
import numpy as np

def prepare(crop, mode='color'):
    if not crop.size:
        raise ValueError('Découpe de plaque vide.')
    if mode == 'color':
        return crop
    scale = max(1.,min(4.,96/crop.shape[0],1600/crop.shape[1]))
    image = cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    if mode == 'resize':
        return image
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    if mode == 'legacy-main':
        gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
        return cv2.threshold(cv2.createCLAHE(3,(8,8)).apply(gray),64,25,cv2.THRESH_BINARY_INV)[1]
    if mode == 'legacy-main2':
        lab=cv2.cvtColor(cv2.bilateralFilter(crop,5,7,7),cv2.COLOR_BGR2LAB)
        lab[:,:,0]=cv2.createCLAHE(2,(8,4)).apply(lab[:,:,0])
        gray=cv2.cvtColor(cv2.cvtColor(lab,cv2.COLOR_LAB2BGR),cv2.COLOR_BGR2GRAY)
        binary=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
        if (binary==255).sum()>(binary==0).sum(): binary=255-binary
        return cv2.morphologyEx(binary,cv2.MORPH_OPEN,(5,5))
    gray=cv2.createCLAHE(2,(8,4)).apply(cv2.bilateralFilter(gray,5,20,20))
    if mode == 'threshold':
        return cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,31,9)
    if mode == 'contrast':
        return cv2.addWeighted(gray,1.5,cv2.GaussianBlur(gray,(0,0),1),-.5,0)
    if mode == 'perspective':
        # Explicit optional mode: accept only a large convex quadrilateral.
        edges=cv2.Canny(gray,60,180)
        contours,_=cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours,key=cv2.contourArea,reverse=True):
            q=cv2.approxPolyDP(contour,.025*cv2.arcLength(contour,True),True)
            if len(q)!=4 or not cv2.isContourConvex(q) or cv2.contourArea(q)<.5*gray.size: continue
            pts=q.reshape(4,2).astype('float32')
            ordered=np.array([pts[np.argmin(pts.sum(1))],pts[np.argmin(np.diff(pts,axis=1))],pts[np.argmax(pts.sum(1))],pts[np.argmax(np.diff(pts,axis=1))]],dtype='float32')
            if len(np.unique(ordered,axis=0)) != 4: continue
            h,w=gray.shape
            return cv2.warpPerspective(image,cv2.getPerspectiveTransform(ordered,np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])),(w,h))
        return image
    raise ValueError('Prétraitement inconnu : '+mode)

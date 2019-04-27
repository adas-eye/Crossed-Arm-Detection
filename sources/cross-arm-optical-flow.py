import numpy as np
import cv2 as cv
import scipy.spatial.distance as dist
import os

files = os.listdir("./videos")
# print(files)
cap = cv.VideoCapture('./videos/bob1-left.avi')

# params for ShiTomasi corner detection
feature_params = dict( maxCorners = 1000,
                       qualityLevel = 0.2,
                       minDistance = 7,
                       blockSize = 7 )

# Parameters for lucas kanade optical flow
lk_params = dict( winSize  = (15,15),
                  maxLevel = 2,
                  criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03))

# Take first frame and find corners in it
ret, old_frame = cap.read()
height, width, _ = old_frame.shape
old_gray = cv.cvtColor(old_frame, cv.COLOR_BGR2GRAY)

p0 = cv.goodFeaturesToTrack(old_gray, mask = None, **feature_params)

# Select keypoint from bottom region only
p0 = p0[p0[:,:,1] > (height//2 - 100)].reshape(-1,1,2)
p_init = p0.copy()

# Get Left Hand Keypoint Index
lh_idx = np.argwhere(p0[:,:,0] > (width//2))
lh_idx_num = list(lh_idx[:,0])

# Get Right Hand Keypoint Index
rh_idx = np.argwhere(p0[:,:,0] <= (width//2))
rh_idx_num = list(rh_idx[:,0])

# Create a mask image for drawing purposes
mask = np.zeros_like(old_frame)

frame_num = 0
detecting = False

while True:
    ret, frame = cap.read()
    if ret:
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # Draw boundary lines
        frame = cv.line(frame, (0,height//2 - 100),(width,height//2 - 100), (255,0,0), 2)
        frame = cv.line(frame, (width//2,height),(width//2,0), (255,0,0), 2)

        # calculate optical flow
        p1, st, err = cv.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
        # Select good points
        good_new = p1[st==1]
        good_old = p0[st==1]

        # Get lost keypoint index
        lost_idx = np.argwhere(st == 0)

        # If there are missing keypoint, delete those index from list
        if len(lost_idx) > 0:
            delete_num = lost_idx[:,0]
            p_init = np.delete(p_init, delete_num, axis=0)
            p_init = p_init[p_init[:,:,1] > (height//2 - 100)].reshape(-1,1,2)
            lh_idx = np.argwhere(p_init[:,:,0] > (width//2))
            lh_idx_num = list(lh_idx[:,0])
            rh_idx = np.argwhere(p_init[:,:,0] <= (width//2))
            rh_idx_num = list(rh_idx[:,0])
        
        # Draw Optical Flow
        for i in range(len(good_new)):
            color = (0,0,0)
            # Draw red line for left hand and yellow line for right hand
            if i in lh_idx_num:
                color = (0, 0, 255)
            elif i in rh_idx_num:
                color = (0, 255, 255)
            mask = cv.line(mask, (good_old[i,0],good_old[i,1]),(good_new[i,0],good_new[i,1]), color, 2)
            frame = cv.circle(frame,(good_old[i,0],good_old[i,1]),5, color, -1)
        img = cv.add(frame,mask)
        
        # Get latest position of right hand keypoint and left hand keypoint
        lhcross_idx = np.where(good_new[lh_idx_num,0] < (width//2))
        rhcross_idx = np.where(good_new[rh_idx_num,0] >= (width//2))

        # If right hand keypoint already in left region and left hand keypoint already in right region
        if len(lhcross_idx[0]) > 0 and len(rhcross_idx[0]):
            detecting = True

        # Estimating position of right and left hand by comparing which one in top 
        if detecting:
            min_val = np.argmin(good_new, axis=0)
            if min_val[1] in lh_idx_num:
                img = cv.putText(img,'Left Hand on Top', (10,100), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
                print("Left Hand on Top")
            elif min_val[1] in rh_idx_num:
                img = cv.putText(img,'Right Hand on Top', (10,100), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
                print("Right Hand on Top")

        img = cv.putText(img,'Frame ' + str(frame_num), (10,50), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv.LINE_AA)
        cv.imshow('frame',img)
        k = cv.waitKey(50) & 0xff
        if k == 27:
            break
            
        # Now update the previous frame and previous points
        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1,1,2)
        frame_num += 1
    else:
        break
cv.destroyAllWindows()
cap.release()
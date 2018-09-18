import cv2
import numpy as np
import matplotlib.pyplot as plt

def preprocessing(img):
    # gaussian blur image and convert to grayscale
    blur = cv2.GaussianBlur(img, (5,5), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)

    # perform a close operation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
    closed_img = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)

    # divide the original image by the close of the image
    div = np.float32(gray) / closed_img
    res = np.uint8(cv2.normalize(div,div,0,255,cv2.NORM_MINMAX))
    return res


def get_area(img):
    # perform adaptive thresholding
    thresh = cv2.adaptiveThreshold(img, 255., 0, 1, 19, 2)
    _,contour,hier = cv2.findContours(thresh,
                                      cv2.RETR_TREE,
                                      cv2.CHAIN_APPROX_SIMPLE)

    # get the contour with the largest area
    max_area = 0
    best_cnt = None
    for cnt in contour:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt


    # black out the area outside of the contour
    mask = np.zeros((img.shape), np.uint8)
    cv2.drawContours(mask, [best_cnt], 0, 255, -1)
    cv2.drawContours(mask, [best_cnt], 0, 0, 2)
    dst = cv2.cornerHarris(mask, 5, 5, 0.04)

    _,thresh = cv2.threshold(np.uint8(dst), 0, 255, cv2.THRESH_OTSU)
    _,contour,_ = cv2.findContours(thresh,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    corners = []
    for i,cnt in enumerate(contour):
        mom = cv2.moments(cnt)
        if mom['m00'] != 0:
            x,y = int(mom['m10']/mom['m00']), int(mom['m01']/mom['m00'])
            corners.append((x,y))

    res = cv2.bitwise_and(img,mask)
    return corners,res


def unwarp(img, corners):
    rows,cols = img.shape
    # map three corners of the convex plane to the corners of a square
    pts1 = np.float32([corners[3], corners[2], corners[1], corners[0]])
    pts2 = np.float32([[rows-1,0], [0,0], [0,cols-1], [rows-1,cols-1]])

    M = cv2.getPerspectiveTransform(pts1,pts2)
    res = cv2.warpPerspective(img,M,(cols,rows))
    return res


if __name__ == '__main__':
    img = cv2.imread("sudoku.jpg")
    img = preprocessing(img)
    corners,img = get_area(img)
    img = unwarp(img, corners)
    plt.imshow(img, cmap='gray')
    plt.show()


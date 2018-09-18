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

    res = cv2.bitwise_and(img,mask)
    return res



if __name__ == '__main__':
    img = cv2.imread("sudoku.jpg")
    img = preprocessing(img)
    img = get_area(img)
    plt.imshow(img, cmap='gray')
    plt.show()


#coding: utf-8
import dlib
import numpy
import cv2
from time import time


class getEyesApp(object):

    eyesareas = []
    perclos = []
    mouthareas = []
    sum_time = 0
    frame_count = 0
    yawn_count = 0

    def __init__(self):
        self.predictor_path = "D:/Python27/workspace/faceswap/shape_predictor_68_face_landmarks.dat"
        self.predictor = dlib.shape_predictor(self.predictor_path)

    def handleEyesArea(self, areas):
        max_areas = max(areas)
        min_areas = min(areas)
        # 眼球极值
        D = max_areas - min_areas

        # 最大值阈值
        threshold_max = min_areas + D * 0.8
        # 大于阈值的都与取做最大值的平均
        j = 0
        vj = 0
        for area in areas:
            if area >= threshold_max:
                vj = vj + area
                j = j + 1
        # 相对最大值
        relative_max = 1.0 * vj / j
        return min_areas, relative_max

    #计算PERCLOS值
    def cal_perclos(self, areas):
        if len(areas) < 100:
            return 0
        min_areas, relative_max = self.handleEyesArea(areas)
        count = len(areas)
        pi = []
        eyeclose=0 #眼睛闭上的个数
        for mi in areas:
            temp=abs(1.0*(mi-min_areas)/(relative_max-min_areas))
    #             print "temp=",temp
            if temp>0.2:
                pi.append(0)
            else:
                pi.append(1)
                eyeclose += 1
        print 'eyeclose=',eyeclose
        sigma_pi=0
        sum = 1.0
        for pii in pi:
            if pii == 1:
                sigma_pi = sigma_pi + 1
        perclos = 1.0*sigma_pi/count
        print 'perclos=', perclos
        print 'count=', count
        return perclos

    def getEyesAreaList(self, frame, faceRects):

        # videoCapture = cv2.VideoCapture(sys.argv[2])
        # detector = dlib.get_frontal_face_detector()

        left = 36
        right = 42
        mouth_start_point = 60
        mouth_end_point = 67
        # success, frame = videoCapture.read()
        # classifier = cv2.CascadeClassifier(
        #     "C:/Users/zsw/Desktop/webcam-pulse-detector-master/cascades/haarcascade_frontalface_alt.xml")

        startTime = time()
        # size = frame.shape[:2]
        # image = cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY)
        # cv2.equalizeHist(image, image)
        # divisor = 8
        # h1, w1 = size
        # minSize = (w1 / divisor, h1 / divisor)
        # faceRects = classifier.detectMultiScale(frame)
        # faceRects = classifier.detectMultiScale(image, 1.5, 2, cv2.CASCADE_SCALE_IMAGE, minSize)
        # if len(faceRects) > 0:
            # t1=time()
        x, y, w, h = faceRects[0]
        shape = self.predictor(frame, dlib.dlib.rectangle(x, y, x+w, y+h))
        # print 'prediction_time=',time()-t1
        # for k, d in enumerate(dets):
        # Get the landmarks/parts for the face in box d.
        # shape = predictor(frame, dlib.dlib.rectangle(100,200,300,400))
        # use six points to describe one eye,left eye is 36-41,right eye is 42-47.
        left_contour = numpy.array([[[shape.part(left + 5).x, shape.part(left + 5).y]]])
        right_contour = numpy.array([[[shape.part(right + 5).x, shape.part(right + 5).y]]])
        mouth_contour = numpy.array([[[shape.part(mouth_end_point).x, shape.part(mouth_end_point).y]]])
        for i in range(5):
            cv2.line(frame, (shape.part(left + i).x, shape.part(left + i).y),
                     (shape.part(left + i + 1).x, shape.part(left + i + 1).y), (255, 0, 0), 1)
            left_contour = numpy.concatenate(
                (left_contour, [[[shape.part(left + i).x, shape.part(left + i).y]]]))
            cv2.line(frame, (shape.part(right + i).x, shape.part(right + i).y),
                     (shape.part(right + i + 1).x, shape.part(right + i + 1).y), (255, 0, 0), 1)
            right_contour = numpy.concatenate(
                (right_contour, [[[shape.part(right + i).x, shape.part(right + i).y]]]))
        for i in range(7):
            cv2.line(frame, (shape.part(mouth_start_point + i).x, shape.part(mouth_start_point + i).y),
                     (shape.part(mouth_start_point + i + 1).x, shape.part(mouth_start_point + i + 1).y), (255, 0, 0), 1)
            mouth_contour = numpy.concatenate(
                (mouth_contour, [[[shape.part(mouth_start_point + i).x, shape.part(mouth_start_point + i).y]]]))

        cv2.line(frame, (shape.part(left + 5).x, shape.part(left + 5).y),
                 (shape.part(left).x, shape.part(left).y), (255, 0, 0), 1)
        cv2.line(frame, (shape.part(right + 5).x, shape.part(right + 5).y),
                 (shape.part(right).x, shape.part(right).y), (255, 0, 0), 1)
        # left_eye_of_area = cv2.contourArea(left_contour)
        # right_eye_of_area = cv2.contourArea(right_contour)
        mouth_of_area = cv2.contourArea(mouth_contour)
        self.mouthareas.append(mouth_of_area)
        if mouth_of_area > 400:
            self.frame_count = self.frame_count + 1
        left_eye_of_area = (shape.part(left + 5).y - shape.part(left + 1).y + shape.part(left + 4).y - shape.part(
            left + 2).y) / 2.0
        right_eye_of_area = (shape.part(right + 5).y - shape.part(right + 1).y + shape.part(right + 4).y - shape.part(
            right + 2).y) / 2.0
        average_area = (left_eye_of_area + right_eye_of_area) / 2.0
        axis_y = average_area
        self.eyesareas.append(axis_y)
        perclos = self.cal_perclos(self.eyesareas)
        self.perclos.append(perclos)
        print 'average_area=', average_area
        endTime = time()
        self.sum_time = self.sum_time + (endTime - startTime)
        if (self.sum_time > 1):
            if (self.frame_count >= 20):
                self.yawn_count = self.yawn_count + 1
            self.sum_time = 0
            self.frame_count = 0
        print 'yawn_count:', self.yawn_count
        # cv2.imshow("image", frame)
        return axis_y





        # cal_perclos(axis_y, len(axis_x))
        # plt.plot(axis_x, axis_y)
        # plt.show()

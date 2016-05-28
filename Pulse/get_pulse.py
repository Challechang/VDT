# coding:utf-8
from lib.device import Camera
from lib.processors import findFaceGetPulse
from lib.interface import plotXY, imshow, waitKey,destroyWindow, moveWindow
import numpy as np      
import datetime
from cv2 import CascadeClassifier

class getPulseApp(object):
    """
    Python application that finds a face in a webcam stream, then isolates the
    forehead.

    Then the average green-light intensity in the forehead region is gathered 
    over time, and the detected person's pulse is estimated.
    """
    eyesArea = []
    perclos = []
    eyesCalssfier = CascadeClassifier("cascades/haarcascade_eye.xml")
    def __init__(self):
        #Imaging device - must be a connected camera (not an ip camera or mjpeg
        #stream)
        self.camera = Camera(camera=0) #first camera by default
        self.w,self.h = 0,0
        self.pressed = 0
        #Containerized analysis of recieved image frames (an openMDAO assembly)
        #is defined next.

        #This assembly is designed to handle all image & signal analysis,
        #such as face detection, forehead isolation, time series collection,
        #heart-beat detection, etc. 

        #Basically, everything that isn't communication
        #to the camera device or part of the GUI
        self.processor = findFaceGetPulse(bpm_limits = [50,160],
                                          data_spike_limit = 2500.,
                                          face_detector_smoothness = 10.)  

        #Init parameters for the cardiac data plot
        self.bpm_plot = False
        self.plot_title = "Cardiac info - raw signal, filtered signal, and PSD"

        #Maps keystrokes to specified methods
        #(A GUI window must have focus for these to work)
        self.key_controls = {"s" : self.toggle_search,
                             "d" : self.toggle_display_plot,
                             "f" : self.write_csv}
        
    def write_csv(self):
        """
        Writes current data to a csv file
        """
        bpm = " " + str(int(self.processor.measure_heart.bpm))
        fn = str(datetime.datetime.now()).split(".")[0] + bpm + " BPM.csv"
        
        data = np.array([self.processor.fft.times, 
                         self.processor.fft.samples]).T
        np.savetxt(fn, data, delimiter=',')
        


    def toggle_search(self):
        """
        Toggles a motion lock on the processor's face detection component.

        Locking the forehead location in place significantly improves
        data quality, once a forehead has been sucessfully isolated. 
        """
        state = self.processor.find_faces.toggle()
        if not state:
        	self.processor.fft.reset()
        print "face detection lock =",not state

    def toggle_display_plot(self):
        """
        Toggles the data display.
        """
        if self.bpm_plot:
            print "bpm plot disabled"
            self.bpm_plot = False
            destroyWindow(self.plot_title)
        else:
            print "bpm plot enabled"
            self.bpm_plot = True
            self.make_bpm_plot()
            moveWindow(self.plot_title, self.w,0)

    def make_bpm_plot(self):
        """
        Creates and/or updates the data display
        """
        plotXY([[self.processor.fft.times, 
                 self.processor.fft.samples],
                [self.processor.fft.even_times[4:-4], 
                 self.processor.measure_heart.filtered[4:-4]],
                [self.processor.measure_heart.freqs, 
                 self.processor.measure_heart.fft]], 
               labels = [False, False, True],
               showmax = [False,False, "bpm"], 
               label_ndigits = [0,0,0],
               showmax_digits = [0,0,1],
               skip = [3,3,4],
               name = self.plot_title, 
               bg = self.processor.grab_faces.slices[0])

    def key_handler(self):    
        """
        Handle keystrokes, as set at the bottom of __init__()

        A plotting or camera frame window must have focus for keypresses to be
        detected.
        """

        self.pressed = waitKey(10) & 255 #wait for keypress for 10 ms
        if self.pressed == 27: #exit program on 'esc'
            print "exiting..."
            self.camera.cam.release()
            exit()

        for key in self.key_controls.keys():
            if chr(self.pressed) == key:
                self.key_controls[key]()
    
    def get_perclos(self):
#         eyesCalssfier = "cascades/haarcascade_eye.xml"
        eye = self.getEyesArea(self.processor.grab_faces.slices[0])
        if eye!=None:
            self.eyesArea.append(eye)
        if len(self.eyesArea)>=100:
            tempPerclos = self.cal_perclos(self.eyesArea, len(self.eyesArea))
            self.perclos.append(tempPerclos)
            self.eyesArea[:] = self.eyesArea[0:75]
            if len(self.perclos)>=10:
                self.perclos[:] = self.perclos[1:10]
            
            
    def getEyesArea(self,face,classfier=eyesCalssfier):
        eyes = []
        eyesRects = classfier.detectMultiScale(face)
        # 如果检测到人眼，返回，否则返回空
        if len(eyesRects)>0:
            for (ex,ey,ew,eh) in eyesRects:
                eyes.append(ew*eh)
            aveEyeArea = float(sum(eyes))/len(eyes)
            return aveEyeArea
        else:
            return None
    def handleEyesArea(self,areas):
        max_areas=max(areas)
        min_areas=min(areas)
        #眼球极值
        D=max_areas-min_areas

        #最大值阈值
        threshold_max=min_areas+D*0.8
        #大于阈值的都与取做最大值的平均
        j=0
        vj=0
        for area in areas:
            if area>=threshold_max:
                vj=vj+area
                j=j+1
        #相对最大值
        relative_max=1.0*vj/j
        return min_areas,relative_max
    #计算PERCLOS值
    def cal_perclos(self,areas,count):
        min_areas,relative_max=self.handleEyesArea(areas)
        pi=[]
        eyeclose=0 #眼睛闭上的个数
        for mi in areas:
            temp=abs(1.0*(mi-min_areas)/(relative_max-min_areas))
#             print "temp=",temp
            if temp>0.2:
                pi.append(0)            
            else:            
                pi.append(1)
                eyeclose+=1
        sigma_pi=0
        sum = 1.0
        for pii in pi:
            if pii==1:
                sigma_pi=sigma_pi+1
        perclos=1.0*sigma_pi/count
        return perclos        
    def main_loop(self):
        """
        Single iteration of the application's main loop.
        """
        # Get current image frame from the camera
        frame = self.camera.get_frame()
        self.h,self.w,_c = frame.shape
        

        #display unaltered frame
        # imshow("Original",frame)

        #set current image frame to the processor's input
        self.processor.frame_in = frame
        #process the image frame to perform all needed analysis
        self.processor.run()
        #collect the output frame for display
        output_frame = self.processor.frame_out

        #show the processed/annotated output frame
        # imshow("Processed",output_frame)

        #create and/or update the raw data display if needed
        if self.bpm_plot:
            self.make_bpm_plot()

        #handle any key presses
        self.key_handler()
        self.get_perclos()

# if __name__ == "__main__":
#     App = getPulseApp()
#     while True:
#         App.main_loop()

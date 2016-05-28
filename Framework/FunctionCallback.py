#  coding:utf-8
import cv2
import threading
import os
import time
import datetime
import PIL.Image
import PIL.ImageTk
import numpy as np
from tkFileDialog import askopenfilename
from tkMessageBox import showerror
from tkSimpleDialog import askstring
from Pulse.get_pulse import *
bufferFace = []
app = getPulseApp()
def callOpenFile():
    filename = askopenfilename()
    if filename:
#             读取该路径的视频文件
        videoCapture = cv2.VideoCapture(filename)
        fps = videoCapture.get(cv2.cv.CV_CAP_PROP_FPS)
        if fps==0.0:
#                 该文件不是视频文件
            showerror('error', '该文件不是视频文件')
            return
#         size = (int(videoCapture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), 
#         int(videoCapture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
        #读帧
        success,frame = videoCapture.read()
        while success:
            cv2.imshow('frame',frame)
            cv2.waitKey(5000/int(fps))
            #读取下一帧
            success,frame = videoCapture.read()
    else:
        showerror("error", "文件不存在!")
def callCapVideo():
    while True:
        target = askstring('录制视频','录制间隔，单位：分钟(min)')
        if target==None:
            return
        try:
            intervalTime = float(target)*60.0
            if intervalTime<=0:
                showerror('error', '时间间隔必须大于0')
            else:
                break
        except:
            showerror('error', '输入必须为数字')       
    t = threading.Thread(target=capVideoThread,args=(intervalTime,))
    t.setDaemon(True)
    t.start()

#     录制视频按钮回调函数 
def capVideoThread(intervalTime):
    while True:
        recordTime = 30.0
        cap = cv2.VideoCapture(0)
        # Define the codec and create VideoWriter object
#         fourcc = cv2.cv.FOURCC(*'XVID')
        """视频输出格式"""
        fourcc = cv2.cv.FOURCC(*'XVID')
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        try:
            os.makedirs(r'../videos/'+date)
        except WindowsError:
            print('文件夹已创建')
        out = cv2.VideoWriter('../videos/'+date+'/'+datetime.datetime.now().strftime("%H-%M-%S")+'.avi',fourcc, 25.0, (640,480))
        start=time.time()
        while(cap.isOpened()):
            _, frame = cap.read()
            #frame = cv2.flip(frame,180)
            if frame!=None:
#                 cv2.imshow('frame',frame)
#                 cv2.imwrite('C:\\Users\\Challe\\Desktop\\1.jpg',frame)
                out.write(frame)
            end=time.time()
            if (end-start)>=recordTime:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # Release everything if job is finished
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        time.sleep(intervalTime)

def update_image(image_label, cv_capture,facesclassfier):
    app.main_loop()
    
#     cv_image = cv_capture.read()[1]
#     cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
#     temp = grabFaces(cv_image, facesclassfier) 
#     if temp!=None:
#         cv_image = temp[0]
#     cv_image = cv2.resize(cv_image,(120,120),interpolation=cv2.INTER_CUBIC)
    cv_image = cv2.resize(app.processor.grab_faces.slices[0],(120,120),interpolation=cv2.INTER_CUBIC)
    pil_image = PIL.Image.fromarray(cv_image)
    tk_image = PIL.ImageTk.PhotoImage(image=pil_image)
    image_label.configure(image=tk_image)
    image_label._image_cache = tk_image  # avoid garbage collection
    image_label.update()
# 更新头像
def update_all(root, image_label, cv_capture,facesclassfier):
    if root.quit_flag:
        root.destroy()  # this avoids the update event being in limbo
    else:
        update_image(image_label, cv_capture,facesclassfier)
        image_label.after(0, func=lambda: update_all(root, image_label, cv_capture,facesclassfier))
def updatePerclos(canvas,figure,y,length):
    #清空原图像
    perclosPlot = figure.add_subplot(211)
    perclosPlot.cla()
    perclosPlot.set_title("PERCLOS",color="#FFFFFF")
    perclosPlot.set_yticks([])
#     tempx = []
#     tempy = []
#     leny = len(y)
#     if leny>length:
#         tempy[:] = y[0:length]
#         if length>50:
#             y[:] = y[1:leny]
#     else:
#         tempy[:] = y[0:leny]
#         
#     for i in range(0,len(tempy)):
#         tempx.append(i)
#     perclosPlot.plot(tempx,tempy)
    if len(app.perclos)==0:
        perclosPlot.plot(0)
    else:
        print app.perclos
        perclosFFT = np.fft.fft(app.perclos)
        perclosPlot.set_ylim(0,1)
        
        tempPerclos = int(sum(app.perclos)/len(app.perclos)*100)
        perclosPlot.plot(app.perclos,label="perclos:"+str(tempPerclos)+"%")
        perclosPlot.legend(loc="upper right")
    
    ppgPlot = figure.add_subplot(212)
    ppgPlot.cla()
    ppgPlot.set_yticks([])
    ppgPlot.set_title("PPG",color="#FFFFFF")
#     ppgPlot.set_xlim(1,50)
#     ppgPlot.set_ylim(0,30000)
#     ppgPlot.grid()   
    bmp = str(int(app.processor.show_bpm_text.bpm+0.5))
    ppgPlot.plot(app.processor.measure_heart.fft,label="bpm:"+bmp)
    ppgPlot.legend(loc="upper right")
    canvas.show()
 # 更新Perclos曲线图
def updateCurve(root,canvas,figure,y,length=0):
    if root.quit_flag:
        root.destroy()
    else:
        if length<=50:
            length += 1
        updatePerclos(canvas,figure,y,length)
        canvas._tkcanvas.after(10,func=lambda:updateCurve(root, canvas,figure,y,length))

def updateWarnbar(canvas):
    canvas.create_oval((40,40,180,180),fill="red",outline="red",dash=(10,10))
    canvas.create_oval((40,210,180,350),fill="yellow",outline="green",dash=(10,10))
    canvas.update()
    canvas.after(10000,func=lambda:updateWarnbar(canvas))

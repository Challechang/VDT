# coding: utf-8
from Tkinter import *
from tkMessageBox import *
from FileDialog import *
from tkFileDialog import askopenfilename
from tkSimpleDialog import askstring
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from Tools.imtool import grabFaces
from FunctionCallback import *
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import cv2
import time
import datetime
import threading
import PIL
import PIL.ImageTk
import math
import tkFont

"""
    尚未解决：
    1. 程序卡顿
    2.排程安排次序问题
    2016-04-19

"""
class MainFrame(Frame):
    background = "#555555"
    widgetcolor = "#555555"
    fontcolor = "#FFFFFF"
    def __init__(self,parent=None):
        Frame.__init__(self, parent)
        self.master.config(bg=self.background)
        self.master.resizable(False,False)
#         self.pack(expand=YES,fill=BOTH)''
        self.createWidgets()
        self.master.title('VDT')
        self.master.iconname('VDTICON')

#     创建组件
    def createWidgets(self):
        self.makeMenubar()
        self.makeToolbar()
        self.makeCurvebar()
        self.makeWarnbar()
#         创建顶部导航
    def makeMenubar(self):
        self.menubar = Menu(self.master)
        self.master.config(menu=self.menubar,bg=self.background)
        self.fileMenu()
        self.editMenu()

#     工具选项
    def makeToolbar(self):
        toolbar = PanedWindow(self.master,relief=RIDGE,bg=self.background)
        toolbar.pack(anchor="nw",fill="x")

        faceWindow = PanedWindow(toolbar,relief=RIDGE,bg=self.background)
        faceLabel = Label(faceWindow,relief=SUNKEN,bg=self.widgetcolor,width=120,height=10)
        faceWindow.add(faceLabel)
#         cvCapture = cv2.VideoCapture(0)
#         facesclassfier = cv2.CascadeClassifier("D:/opencv/opencv/sources/data/haarcascades/haarcascade_frontalface_default.xml")   #定义分类器
        cvCapture = None
        facesclassfier = None
        faceLabel.after(0, func=lambda:update_all(self.master, faceLabel, cvCapture,facesclassfier))
        toolbar.add(faceWindow)

        axisWindow = PanedWindow(toolbar,relief=RIDGE,bg=self.background)
        # 第一行控件
        Label(axisWindow,text="xmin", fg=self.fontcolor, bg=self.widgetcolor).grid(row=0,column=0)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=1)
        Label(axisWindow,text="ymin",fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=2)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=3)
        Label(axisWindow,text="major xtick",fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=4)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=5)
        Label(axisWindow,text="minor xtick",fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=6)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=7)
        #第二行控件
        Label(axisWindow,text="xmax",fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=0)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=1)
        Label(axisWindow,text="ymax",fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=2)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=3)
        Label(axisWindow,text="major ytick",fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=4)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=5)
        Label(axisWindow,text="minor ytick",fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=6)
        Entry(axisWindow,width=5,fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=7)
        #第三行控件
        Button(axisWindow,text="Confirm",fg=self.fontcolor,width=8,bg=self.widgetcolor).grid(row=2,column=3,padx=1,pady=2)
        Button(axisWindow,text="Auto",fg=self.fontcolor,width=8,bg=self.widgetcolor).grid(row=2,column=4,padx=1,pady=2)
        #第四行控件
        Label(axisWindow,text="Axis",fg=self.fontcolor,bg=self.widgetcolor).grid(row=3,column=3,columnspan=2,pady=13)
        toolbar.add(axisWindow)

        controlWindow = PanedWindow(toolbar,relief=RIDGE,bg=self.background)
        Button(controlWindow,text="Clear All",width=8,fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=0,pady=1)
        Button(controlWindow,text="Del Sel",width=8,fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=0,pady=1)
        Button(controlWindow,text="Del UnSel",width=8,fg=self.fontcolor,bg=self.widgetcolor).grid(row=2,column=0,pady=1)
        Button(controlWindow,text="Cap Video",width=8,fg=self.fontcolor,bg=self.widgetcolor,command=self.capVideo).grid(row=3,column=0,pady=1)
        toolbar.add(controlWindow)

        messageWindow = PanedWindow(toolbar,relief=RIDGE,bg=self.background)
        Checkbutton(messageWindow,text="Show Msg Panel",fg=self.fontcolor,bg=self.widgetcolor).grid(row=0,column=0,sticky="w")
        Checkbutton(messageWindow,text="Show std out",fg=self.fontcolor,bg=self.widgetcolor).grid(row=1,column=0,sticky="w")
        Checkbutton(messageWindow,text="Show stderr",fg=self.fontcolor,bg=self.widgetcolor).grid(row=2,column=0,sticky="w")
        Label(messageWindow,text="Message",fg=self.fontcolor,bg=self.widgetcolor).grid(row=3,column=0,columnspan=2,pady=13)
        toolbar.add(messageWindow)

#         视频控件
    def makeCurvebar(self):
        figure = Figure(figsize=(5,4),dpi=100,facecolor=self.background)
        curvebar = PanedWindow(self.master,relief=RIDGE,bg=self.background)
        curvebar.pack(side = LEFT)
        canvas = FigureCanvasTkAgg(figure,master=curvebar)
#         canvas.show()
#         perclosPlot.set_ylim(-1,1)
        y = []
        i = 0
        while i<=750:
            i += 0.1
            y.append(math.sin(i))

        updateCurve(self.master, canvas, figure,y)
#         updatePPGCurve(self.master, canvas, figure,y)
        canvas.get_tk_widget().config(bg=self.background)
        canvas.get_tk_widget().pack(side=TOP)

    def makeWarnbar(self):
        warnbar = PanedWindow(self.master,relief=RIDGE,bg=self.background)
        warnbar.pack(side=RIGHT)
        canvas = Canvas(warnbar,width=205,height=410,bg=self.background)
        canvas.grid(row=0,column=0)
#         canvas.create_oval((40,40,180,180),fill="green",outline="red",dash=(10,10))
        font1 = tkFont.Font(size=15)
        canvas.create_oval((40,80,180,220),fill="green")
        canvas.create_text(110,240,text="Red：Dangerous ",fill="red",font=font1)
        canvas.create_text(110,270,text="Yellow：Warning",fill="yellow",font=font1)
        canvas.create_text(110,300,text="Green：Good    ",fill="green",font=font1)
#         canvas.after(100000, func=lambda:updateWarnbar(canvas))

    def fileMenu(self):
        file = Menu(self.menubar,bg=self.widgetcolor)
        file.add_command(label='New...',command=self.notdone,underline=0)
        file.add_command(label='Open...',command=self.openFile,underline=0)
        file.add_command(label='Quit',command=self.master.destroy,underline=0)
        self.menubar.add_cascade(label='File',menu=file,underline=0)
    def editMenu(self):
        edit = Menu(self.menubar,bg=self.widgetcolor)
        edit.add_command(label='Cut',command=self.notdone,underline=0)
        edit.add_command(label='Paste',command=self.notdone,underline=0)
        self.menubar.add_cascade(label='Edit',menu=edit,underline=0)
#     打开文件菜单回调函数
    def openFile(self):
        callOpenFile()
    def capVideo(self):
        callCapVideo()
    def notdone(self):
        showerror('error', "not done yet!!!")

if __name__=='__main__':
    root = Tk()

    setattr(root, 'quit_flag', False)
    def set_quit_flag():
        root.quit_flag = True
    root.protocol('WM_DELETE_WINDOW', set_quit_flag)  # avoid errors on exit
    framework = MainFrame(root)
    root.mainloop()

# coding: utf-8
from numpy import *
from math import sin,cos
import numpy as np
import cv2
"""
    从图像中获取人脸部分
@param: frame-图像     classfier-分类器
@return: faces-该图像中所有人脸的列表
"""
def grabFaces(frame,classfier):
    size=frame.shape[:2]#获得当前桢彩色图像的大小
    image=np.zeros(size,dtype=np.float16)#定义一个与当前桢图像大小相同的的灰度图像矩阵
    image = cv2.cvtColor(frame, cv2.cv.CV_BGR2GRAY)#将当前桢图像转换成灰度图像
    cv2.equalizeHist(image, image)#灰度图像进行直方图等距化
    #如下三行是设定最小图像的大小
    divisor=8
    h, w = size
    minSize=(w/divisor, h/divisor)
    faceRects = classfier.detectMultiScale(image, 1.2, 2, cv2.CASCADE_SCALE_IMAGE,minSize)#人脸检测
    #将截取到的所有人脸保存到faces中
    faces = []
    #如果检测到人脸，则将所有人脸返回，否则返回空
    if len(faceRects)>0:#如果人脸数组长度大于0
        for faceRect in faceRects: #对每一个人脸画矩形框
                x, y, w, h = faceRect
                faces.append(frame[y:y+h,x:x+w])
        return faces
    else :
        return None
"""对灰色图像进行均衡化"""
def histeq(im,nbr_bins=256):

    #计算直方图
    imhist,bins = histogram(im.flatten(),nbr_bins,normed=True)
    cdf = imhist.cumsum()
    cdf = 255 * cdf / cdf[-1] #归一化
    # 使用累积分分布的线性插值，计算新的像素值、
    im2 = interp(im.flatten(),bins[:-1],cdf)
    
    return im2.reshape(im.shape), cdf


"""rof模型，去除图像噪声"""
def denoise(im,U_init,tolerance=0.1,tau=0.125,tv_weight=100):
    m,n = im.shape  #噪声图像的大小
    #初始化
    U = U_init
    Px = im # 对偶域的x分量
    Py = im # 对偶域的y分量
    error = 1
    while(error > tolerance):
        Uhold = U
        # 原始变量的梯度
        GradUx = roll(U,-1,axis=1)-U # 变量U梯度的x分量
        GradUy = roll(U,-1,axis=0)-U # 变量U梯度的y分量
        
        # 更新对偶变量
        PxNew = Px + (tau/tv_weight)*GradUx
        PyNew = Py + (tau/tv_weight)*GradUy
        NormNew = maximum(1,sqrt(PxNew**2+PyNew**2))
        
        Px = PxNew/NormNew # 更新x分量(对偶)
        Py = PyNew/NormNew # 更新y分量(对偶)
        
        # 更新原始变量
        RxPx = roll(Px,1,axis=1) # 对x分量进行向右x轴平移
        RyPy = roll(Py,1,axis=0) # 对y分量进行向右y轴平移
        
        DivP = (Px-RxPx)+(Py-RyPy) # 对偶域的散度
        U = im + tv_weight*DivP # 更新原始变量
        
        # 更新误差
        error = linalg.norm(U-Uhold)/sqrt(n*m)
    return U,im-U
'''
    对图像进行积分投影
    @return: x-横坐标 Sy-垂直积分投影 y-纵坐标 Sx-水平积分投影
'''
def projection(img):
    height,width = img.shape[:2]
    print width
   # 垂直投影
    Sy = []
    for i in range(width):
        Sy.append(sum(img[0:height,i])/width)
    x = np.arange(0,width,1)
    # 水平投影
    Sx = []
    for i in range(height):
        Sx.append(sum(img[i,0:width])/height)
    y = np.arange(0,height,1)
    return x,Sy,y,Sx
'''
    @return: t 大于1为非肤色，小于等于1为肤色
'''
def isFace(Y,CbY,CrY):
    # 计算肤色区域的中轴线
    
    # 非线性分段色彩变换的分段阈值
    Ki = 125
    Kh = 188
    
    # 肤色聚类区域中Y分量的最大和最小值
    Ymax = 235
    Ymin = 16
    # Y = 0
    # CbY = 0
    # CrY = 0
    # 计算肤色区域的中轴线
    if Y < Ki:
        MidCrY = 154 + 1.0*(Ki - Y)*(154 - 144)/(Ki - Ymin)
        MidCbY = 108 + 1.0*(Ki - Y)*(118 - 108)/(Ki - Ymin)
    elif Y >= Kh:
        MidCrY = 154 + 1.0*(Y - Kh)*(154 - 132)/(Ymax - Kh)
        MidCbY = 108 + 1.0*(Y - Kh)*(118 - 108)/(Ymax - Kh)
    
    # 肤色区域用WCbY,WCrY表示
    WCb = 46.97
    WLCb = 23
    WHCb = 14
    WCr = 38.76
    WLCr = 20
    WHCr = 10
    if Y < Ki:
        WCbY = WLCb + 1.0*(Y - Ymin)*(WCb - WLCb)/(Ki - Ymin)
        WCrY = WLCr + 1.0*(Y - Ymin)*(WCr - WLCr)/(Ki - Ymin)
    elif Y > Kh:
        WCbY = WHCb + 1.0*(Ymax - Y)*(WCb - WHCb)/(Ymax - Kh)
        WCrY = WHCr + 1.0*(Ymax - Y)*(WCr - WHCr)/(Ymax - Kh)
    print Y
    # 将上面结果得到如下的非线性分段色彩变换
    if Y < Ki or Y > Kh:
        DotCbY = 1.0*(CbY - MidCbY)*WCb/WCbY + MidCbY
        DotCrY = 1.0*(CrY - MidCrY)*WCr/WCrY + MidCrY
    elif Y>=Ki and Y<=Kh:
        DotCbY = CbY
        DotCrY = CrY
    
    # 用椭圆近似肤色区域
    Cx = 109.38
    Cy = 152.02
    angle = 2.53 #弧度制
    ecx = 1.60
    ecy = 2.41
    a = 25.39
    b = 14.03
    x = cos(angle)*(DotCbY - Cx) + sin(angle)*(DotCrY - Cy)
    y = -sin(angle)*(DotCbY - Cx) + cos(angle)*(DotCrY - Cy)
    # 若t大于1，该区域为非肤色，小于等于1，为肤色
    t = ((x - ecx)**2)/(a**2) + ((y - ecy)**2)/(b**2)
    return t
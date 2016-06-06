# coding: utf-8


class SwithTool(object):

    #提供标识当前应该显示哪条曲线的静态变量值, 默认为1,即显示眼睛高度
    eyesHeight = 1
    perclos = 2
    mouthArea = 3
    curShow = 1

    def switch(self):
        if self.curShow==3:
            self.curShow = 1
        else:
            self.curShow += 1

    def getCurShow(self):
        return self.curShow

    def showEyesHeight(self):
        return self.eyesHeight

    def showPerclos(self):
        return self.perclos

    def showMouthArea(self):
        return self.mouthArea
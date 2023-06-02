# Grant He
# Date: 2023/5/22
import sys
import time

import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import QThread, pyqtSignal, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QDialog
#from aip import AipBodyAnalysis
from threading import Thread
import random
from qtpy import uic



hand = {'One': '1', 'Five': '5', 'Fist': '拳头', 'Ok': 'OK',
        'Prayer': '祈祷', 'Congratulation': '作揖', 'Honour': '作别',
        'Heart_single': '比心心', 'Thumb_up': '点赞', 'Thumb_down': 'Diss',
        'ILY': '我爱你', 'Palm_up': '掌心向上', 'Heart_1': '双手比心1',
        'Heart_2': '双手比心2', 'Heart_3': '双手比心3', 'Two': '2',
        'Three': '3', 'Four': '4', 'Six': '6', 'Seven': '7',
        'Eight': '8', 'Nine': '9', 'Rock': 'Rock', 'Insult': '竖中指', 'Face': '脸'}

# 手势识别
#gesture_client = AipBodyAnalysis(APP_ID, API_KEY, SECRET_KEY)

# 一些识别用的参数

game_test = [1, 2, 3, 4, 5]
Matched_index = 0
Matched = [0, 0, 0, 0, 0]  # 1代表正确  -1代表错误 0代表miss
fail_type = [0, 0, 0, 0, 0]  # 这里用于防止失误检测
game_level = [1, 12, 14]  # 游戏关卡 写死了


# 对话框
class ScoreDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("score_dialog.ui", self)  # load UI to self

    def set_score(self, score):
        self.scorelabel.setText(str(score))  # use self instead of self.ui


def game_over(score):
    dialog = ScoreDialog()
    dialog.set_score(score)
    dialog.exec_()


class Recog_Thread(QThread):
    trigger = pyqtSignal(str)
    judge = True
    capture = None  # 0为默认摄像头

    def __init__(self):
        super().__init__()

    def run(self):
        self.judge = True
        self.capture = cv2.VideoCapture(0)  # 0为默认摄像头
        while self.judge:
            try:
                ret, frame = self.capture.read()
                # 显示图片
                # cv2.imshow('frame', frame)
                # 图片格式转换
                image = cv2.imencode('.jpg', frame)[1]
                gesture = gesture_client.gesture(image)  # AipBodyAnalysis内部函数
                # print(gesture)
                words = gesture['result'][0]['classname']
                # print(hand[words])
                if hand[words] == "脸":
                    continue
                self.trigger.emit(hand[words])
                print(Matched)
            except:
                print('×', end="")
            if cv2.waitKey(1) == ord('q'):
                self.stop()
                break

    def stop(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        self.judge = False


# 进度条信息
class Progress(QThread):
    progress_updated = pyqtSignal(int)  # 进度更新信号
    finished = pyqtSignal()  # 完成信号

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.progress = 0
        self.active = True

    def invalidate(self):
        self.active = False

    def run(self):
        if not self.active:
            return
        while self.progress < self.duration:
            time.sleep(0.07)  # delay for 1 second
            self.progress += 1
            self.progress_updated.emit(int((self.progress / self.duration) * 100))
        self.finished.emit()


# 用于产生新的手势序列
def produce_sequence(maxgesture):
    global game_test
    for i in range(len(game_test)):
        if i == 0:
            game_test[i] = random.randint(1, maxgesture)  # 随机选择1-max的数字
        else:
            # 如果新选择的数字与前一个数字相同，我们将继续选择，直到找到一个不同的数字。
            while True:
                new_num = random.randint(1, maxgesture)
                if new_num != game_test[i - 1]:
                    game_test[i] = new_num
                    break


class gameWindow(QWidget):
    close_camera_signal = pyqtSignal()
    progress_signal = pyqtSignal()
    progress_renew_level = pyqtSignal()
    begin_progress = True

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi("gameWindow.ui")
        self.ui.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        # 分数显示的label
        self.scores = self.ui.scores
        # 显示图片的label 有五个图框
        self.image_index = 0
        self.image_labels = [self.ui.img_label_1, self.ui.img_label_2, self.ui.img_label_3, self.ui.img_label_4,
                             self.ui.img_label_5]
        # 显示进度的label
        self.signals = [self.ui.label_1, self.ui.label_2, self.ui.label_3, self.ui.label_4, self.ui.label_5]
        # 退出按钮
        self.btn_quit = self.ui.pushButton
        self.btn_quit.clicked.connect(self.emit_close_camera_signal)
        self.progress_bar = self.ui.progressBar
        self.progress_bar.setRange(0, 100)  # 设置进度条的起点和终点
        self.progress = Progress(100)  # 设定进度条时长为100秒
        self.progress.progress_updated.connect(self.update_progress_bar)
        self.progress.finished.connect(self.reset_finished)
        self.sub_init_1()

    def sub_init_1(self):
        self.update_images()
        # 还没做好

    def sub_init_2(self):
        pass

    def sub_init_3(self):
        pass

    # 进度条的函数
    def start_progress(self):
        self.progress.start()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def reset_finished(self, mode=0):
        if self.begin_progress:
            if mode != 2:
                self.progress.invalidate()  # 使旧的 progress 无效
                self.progress_bar.reset()  # 重置进度条
                self.progress = Progress(100)  # 重新创建 Progress 对象
                self.progress.progress_updated.connect(self.update_progress_bar)
                self.progress.finished.connect(self.reset_finished)
                self.progress_signal.emit()  # 进度条结束，发出更新信号
            if mode == 0:
                self.progress_renew_level.emit()  # 进度条自己满了，要对参数进行更新

    def show_signals(self):
        for i in range(0, 5):
            if Matched[i] == 0:
                self.signals[i].setText("")
            elif Matched[i] == 1:
                self.signals[i].setText("√")
            elif Matched[i] == -1:
                self.signals[i].setText("×")
            elif Matched[i] == -2:
                self.signals[i].setText("miss")

    def show_result(self, score):
        self.scores.setText(str(score))

    def update_images(self):
        time.sleep(0.5)
        try:
            for i in range(5):
                self.image_labels[i].setScaledContents(True)
                pixmap = QPixmap("./img/" + f"{game_test[i]}.png")
                self.image_labels[i].setPixmap(pixmap.scaled(100, 100))  # 假设图片需要缩放为 100x100 大小
        except Exception as e:
            print("Error occurred:", e)

    def emit_close_camera_signal(self):
        print("emit_close_camera_signal is called")
        self.ui.close()
        self.close_camera_signal.emit()  # 当点击按钮时，发出关闭摄像头的信号


class MyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.ui = uic.loadUi("mainWindow.ui")
        self.btn_1 = self.ui.pushButton_1  # 按下按钮后 出现识别界面 （可以考虑将本界面隐藏？？）
        self.btn_1.clicked.connect(self.clicked_1)
        self.btn_2 = self.ui.pushButton_2  # 按下按钮后 出现识别界面 （可以考虑将本界面隐藏？？）
        self.btn_2.clicked.connect(self.clicked_2)
        self.btn_3 = self.ui.pushButton_3  # 按下按钮后 出现识别界面 （可以考虑将本界面隐藏？？）
        self.btn_3.clicked.connect(self.clicked_3)
        self.MyThread = Recog_Thread()  # 用于识别手势的线程
        self.MyThread.trigger.connect(self.Match)
        # self.camera = use_camera()      # 打开摄像头的线程
        self.gameWindow = gameWindow()  # 创建gameWindow实例
        # 关闭subWindow时同时把摄像头关闭
        self.gameWindow.close_camera_signal.connect(self.MyThread.stop)  # 连接关闭摄像头的信号到Camera类的关闭摄像头的方法
        # self.gameWindow.close_camera_signal.connect(self.reset_show)
        # 进度更新的时候
        self.gameWindow.progress_signal.connect(self.reset_show)
        self.gameWindow.progress_renew_level.connect(self.process_level)
        # 记录游戏过程的分数
        self.scores = 0
        # 这里的level用于选择游戏手势条的更新次数 因为做三个关卡，所以三个按钮  btn1 btn2 btn3 点击不同的按钮，level会进行不同的更新
        self.level = 0
        self.maxgesture = 0

    def clicked_1(self):  # 开始检测
        global Matched_index
        global Matched
        global fail_type
        self.maxgesture = 5
        self.scores = 0
        self.level = game_level[0]
        self.gameWindow.ui.show()  # 创建gameWindow实例
        self.gameWindow.begin_progress = True
        Matched_index = 0
        self.MyThread.start()
        self.gameWindow.start_progress()
        # 游戏初始化
        Matched_index = 0
        Matched = [0, 0, 0, 0, 0]  # 1代表正确  -1代表错误 0代表miss
        fail_type = [0, 0, 0, 0, 0]  # 这里用于防止失误检测

    def clicked_2(self):
        global Matched_index
        global Matched
        global fail_type
        self.maxgesture = 7
        self.scores = 0
        self.level = game_level[1]
        self.gameWindow.ui.show()  # 创建gameWindow实例
        self.gameWindow.begin_progress = True
        Matched_index = 0
        self.MyThread.start()
        self.gameWindow.start_progress()
        # 游戏初始化
        Matched_index = 0
        Matched = [0, 0, 0, 0, 0]  # 1代表正确  -1代表错误 0代表miss
        fail_type = [0, 0, 0, 0, 0]  # 这里用于防止失误检测

    def clicked_3(self):
        global Matched_index
        global Matched
        global fail_type
        self.maxgesture = 9
        self.scores = 0
        self.level = game_level[2]
        self.gameWindow.ui.show()  # 创建gameWindow实例
        self.gameWindow.begin_progress = True
        Matched_index = 0
        self.MyThread.start()
        self.gameWindow.start_progress()
        # 游戏初始化
        Matched_index = 0
        Matched = [0, 0, 0, 0, 0]  # 1代表正确  -1代表错误 0代表miss
        fail_type = [0, 0, 0, 0, 0]  # 这里用于防止失误检测

    def reset_show(self, mode=0):
        global Matched_index
        global Matched
        global fail_type
        if self.level == 0:
            return
        if mode == 0:
            produce_sequence(self.maxgesture)
            self.gameWindow.update_images()
            # 识别完一次就初始化
            Matched_index = 0
            Matched = [0, 0, 0, 0, 0]  # 1代表正确  -1代表错误 0代表miss
            fail_type = [0, 0, 0, 0, 0]  # 这里用于防止失误检测
            # 更新提示的signals 清空
            self.gameWindow.show_signals()
        else:
            return

    def process_level(self):
        print("成功：" + str(Matched.count(1)) + "次； 错过：" + str(Matched.count(-2)) + "次； 错误：" + str(
            Matched.count(-1)) + "次")
        # 更新游戏进度
        self.level -= 1
        if self.level == 0:
            self.MyThread.stop()
            print("over at 2")
            self.gameWindow.begin_progress = False
            self.gameWindow.show_result(self.scores)
            self.gameWindow.ui.close()
            game_over(self.scores)

            # self.reset_show(1)
            return
        self.gameWindow.start_progress()

    def Match(self, strs):
        global Matched_index
        global Matched
        global fail_type

        print(strs)

        temp = 0
        if strs == "1":
            temp = 1
        elif strs == "2":
            temp = 2
        elif strs == "5":
            temp = 3
        elif strs == "Diss":
            temp = 4
        elif strs == "点赞":
            temp = 5
        elif strs == "Rock":
            temp = 6
        elif strs == "8":
            temp = 7
        elif strs == "双手比心3":
            temp = 8
        elif strs == "我爱你":
            temp = 9
        elif strs == "脸":
            return
        else:
            temp = -1
        # 逻辑判断
        if Matched_index == len(Matched):
            try:
                # 判断是否结束，是否关闭摄像头并显示结果
                if self.level == 0:
                    print("over at 1")
                    self.MyThread.stop()
                    self.gameWindow.begin_progress = False
                    self.gameWindow.show_result(self.scores)
                    self.gameWindow.ui.close()
                    game_over(self.scores)
                    # self.reset_show(1)
                    return
                # 完成之后更新图片
                # self.reset_show()
                # 如果还有，需要重启进度条
                self.gameWindow.reset_finished(1)
                self.gameWindow.start_progress()
                # 如果该串识别完毕就关闭摄像头（之后可以改成 下一串 或者 直接用一大串？？）
            except Exception as e:
                print("Error occurred:", e)

        if Matched_index < len(Matched):
            if temp == game_test[Matched_index]:  # 当前匹配成功
                Matched[Matched_index] = 1
                Matched_index += 1
                # 更新提示的signals
                self.gameWindow.show_signals()
                return
            elif Matched_index == 0:  # 当前匹配没成功 且匹配的第一个。则第一个出现一个fail
                fail_type[0] += 1
                # todo 第一个的判断
            elif Matched_index != 0:  # 当前没匹配成功 且不处于第一个
                if temp == game_test[Matched_index - 1]:  # 1 重复识别
                    return
                elif temp != game_test[Matched_index - 1]:  # 2 错误手势
                    if Matched_index == len(Matched) - 1:  # 最后一个的情况 单独处理
                        if fail_type[Matched_index] == 0:  # 第一次fail
                            fail_type[Matched_index] += 1
                        else:  # 第二次fail直接退出
                            Matched_index += 1
                            Matched[Matched_index] = -1
                            # 更新提示的signals
                            self.gameWindow.show_signals()
                            return
                    else:
                        if temp == game_test[Matched_index + 1]:  # 当次,却识别到后面一个，错过了当次
                            Matched[Matched_index] = -2
                            Matched[Matched_index + 1] = 1
                            Matched_index += 2
                            # 更新提示的signals
                            self.gameWindow.show_signals()
                        else:
                            if fail_type[Matched_index] == 1:
                                Matched[Matched_index] = -1  # 两次识别错误，该项错误
                                Matched_index += 1
                                # 更新提示的signals
                                self.gameWindow.show_signals()
                            else:
                                fail_type[Matched_index] += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyPage()
    w.ui.show()
    app.exec_()

import sys
import os
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.Qt as Qt
import PyQt5.QtCore as QtCore
from PIL import Image
from mongo_client import MongoDriver
import utils
import _thread as thread


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        print('start GUI')
        self.driver=MongoDriver('121.48.165.6',11118)
        self.data=[]
        self.index=0
        self.size=0
        self.checked=0
        self.getting=False

        self.get_next_batch_data()
        data=self.data[self.index]
        self.setFixedSize(1600,900)
        self.GUI()
        self.set_info(data)

    def button(self):
        prev_icon=QtGui.QIcon('./GUI_src/prev.png')
        next_icon=QtGui.QIcon('./GUI_src/next.png')
        check_icon=QtGui.QIcon('./GUI_src/check.png')
        restore_icon=QtGui.QIcon('./GUI_src/restore.png')

        self.prev_button=QtWidgets.QPushButton()
        self.next_button=QtWidgets.QPushButton()
        self.check_button=QtWidgets.QPushButton()
        self.restore_button=QtWidgets.QPushButton()

        self.prev_button.setIcon(prev_icon)
        self.next_button.setIcon(next_icon)
        self.check_button.setIcon(check_icon)
        self.restore_button.setIcon(restore_icon)

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.check_button.clicked.connect(self.check)
        self.restore_button.clicked.connect(self.restore)

    def name_label(self):
        self.name_label=QtWidgets.QLabel('UUID:')
        self.uuid_label=QtWidgets.QLabel()
        self.checked_label=QtWidgets.QLabel(str(self.checked))

        self.name_label.setFont(self.font)
        self.uuid_label.setFont(self.font)
        self.checked_label.setFont(self.font)
    
    def image_box(self):
        self.display_area=QtWidgets.QScrollArea()
        self.image=QtWidgets.QLabel()
        self.display_area.setWidgetResizable(True)
        self.display_area.setWidget(self.image)
        self.display_area.resize(1200,900)

    def GUI(self):
        self.font=QtGui.QFont('Microsoft YaHei',12,75)
        self.button()
        self.image_box()
        self.name_label()
        self.text_box=QtWidgets.QTextEdit()
        self.text_box.setFont(self.font)

        name_box=QtWidgets.QHBoxLayout()
        name_box.addWidget(self.name_label)
        name_box.addWidget(self.uuid_label)
        grid=QtWidgets.QGridLayout()
        grid.addLayout(name_box,0,0,2,18,QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        grid.addWidget(self.checked_label,0,18,2,2,QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        grid.addWidget(self.prev_button,2,0,8,2,QtCore.Qt.AlignVCenter)
        grid.addWidget(self.display_area,2,2,8,16)#,QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        grid.addWidget(self.next_button,2,18,8,2,QtCore.Qt.AlignVCenter)
        grid.addWidget(self.text_box,10,0,8,20)
        grid.addWidget(self.restore_button,18,0,2,2)
        grid.addWidget(self.check_button,18,18,2,2)
        self.setLayout(grid)

    def set_image(self,path):
        image_pixmap=QtGui.QPixmap(path)
        self.image.setPixmap(image_pixmap)

    def get_next_batch_data(self):
        if self.getting==False:
            self.getting=True
            data=self.driver.load_unchecked_img(10,self.size-self.checked)
            count=0
            for d in data:
                count=count+1
                img_path=utils.image_transform(utils.url_img_download(d['src']))
                d['local_path']=img_path
                if 'plain_text' not in d.keys():
                    d['plain_text']=''
                self.data.append(d)
            self.size=self.size+count
            self.getting=False

    def set_info(self,data):
        self.uuid_label.setText(data['uuid'])
        if os.path.exists(data['local_path'])==True:
            img_path=data['local_path']
        else:
            img_path=utils.image_transform(utils.url_img_download(data['src']))
        self.set_image(img_path)
        if data['resolved']==True:
            self.text_box.setText(data['plain_text'])
        else:
            self.text_box.setText('')

    def prev_page(self):
        if self.index>0:
            self.index=self.index-1;
            data=self.data[self.index]
            self.set_info(data)

    def next_page(self):
        if self.index+6>=self.size:
            try:
                thread.start_new_thread(self.get_next_batch_data,())
            except Exception as e:
                print(e)
                exit()
        print(self.size,self.index)
        if self.index+1!=self.size:
            self.index=self.index+1
            data=self.data[self.index]
            self.set_info(data)

    def check(self):
        data=self.data[self.index]
        data['plain_text']=self.text_box.toPlainText()
        flag1= True if data['checked']==False else False
        data['resolved']=True
        data['checked']=True
        flag2=self.driver.update_img_check_info(data)
        if flag1==True and flag2==True:
            self.checked=self.checked+1
            self.checked_label.setText(str(self.checked))

    def restore(self):
        data=self.data[self.index]
        self.text_box.setText(data['plain_text'])

if __name__=='__main__':
    app=QtWidgets.QApplication(sys.argv)
    w=MainWindow()
    w.show()

    sys.exit(app.exec_())

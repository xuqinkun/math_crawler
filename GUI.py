from threading import Thread
import os
import sys

from PyQt5.QtCore import Qt, QMetaObject, pyqtSlot
import PyQt5.QtGui as QtGui
from PyQt5.QtWidgets import *

import utils
from mongo_client import MongoDriver


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        print('start GUI')
        self.driver = MongoDriver('121.48.165.6', 11118)
        self.data = []
        self.index = 0
        self.size = 0
        self.checked = 0
        self.getting = False

        self.get_next_batch_data()
        data = self.data[self.index]
        self.resize(1600, 900)

        self.font = QtGui.QFont('Microsoft YaHei', 12, 75)
        self.text_box = QTextEdit()
        self.text_box.setFont(self.font)
        self.text_box.setObjectName("edit")

        self.info_label = QLabel("Unsaved!")
        self.auto_save = QCheckBox("Autosave")
        self.auto_save.setObjectName("auto_save")
        self.auto_save.setChecked(True)
        self.GUI()
        self.set_info(data)
        QMetaObject.connectSlotsByName(self)

    def closeEvent(self, event):
        print('Closing...')
        for data in self.data:
            if not data['checked']:
                doc = {}
                filter_ = {'_id': data['_id']}
                update_ = {'$set': {'checking': False}}
                doc['filter'] = filter_
                doc['update'] = update_
                self.driver.update_one('image', doc)
        print('Done')
        event.accept()

    def button(self):
        prev_icon = QtGui.QIcon('./GUI_src/prev.png')
        next_icon = QtGui.QIcon('./GUI_src/next.png')
        check_icon = QtGui.QIcon('./GUI_src/check.png')
        restore_icon = QtGui.QIcon('./GUI_src/restore.png')

        self.prev_button = QPushButton()
        self.next_button = QPushButton()
        self.save_button = QPushButton()
        self.restore_button = QPushButton()

        self.prev_button.setIcon(prev_icon)
        self.next_button.setIcon(next_icon)
        self.save_button.setIcon(check_icon)
        self.restore_button.setIcon(restore_icon)

        self.prev_button.resize(100,400)

        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.save_button.clicked.connect(self.save)
        self.restore_button.clicked.connect(self.restore)

    def name_label(self):
        self.name_label = QLabel('UUID:')
        self.uuid_label = QLabel()
        self.checked_label = QLabel(str(self.checked))

        self.name_label.setFont(self.font)
        self.uuid_label.setFont(self.font)
        self.checked_label.setFont(self.font)

    def image_box(self):
        self.display_area = QScrollArea()
        self.image = QLabel()
        self.display_area.setWidgetResizable(True)
        self.display_area.setWidget(self.image)
        self.display_area.resize(1200, 900)

    @pyqtSlot()
    def on_edit_textChanged(self):
        self.save_button.setDisabled(False)
        self.info_label.setText("Unsaved!")

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.next_page()

    @pyqtSlot()
    def on_copy_button_clicked(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.uuid_label.text())
        self.copy_info.setText("Copied to clipboard!")

    @pyqtSlot()
    def on_mark_button_clicked(self):
        reply = QMessageBox.question(self, 'Warning', 'Mark this picture as GRAPH?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.text_box.setText("GRAPH")

    def GUI(self):
        self.button()
        self.image_box()
        self.name_label()

        name_box = QHBoxLayout()
        name_box.addWidget(self.name_label)
        name_box.addWidget(self.uuid_label)
        copy_button = QPushButton("Copy")
        copy_button.setObjectName("copy_button")
        self.copy_info = QLabel()

        name_box.addWidget(copy_button)
        name_box.addWidget(self.copy_info)
        name_box.addWidget(self.info_label)

        mark_button = QPushButton("GRAPH")
        mark_button.setObjectName("mark_button")

        grid = QGridLayout()
        grid.addLayout(name_box, 0, 0, 2, 18, Qt.AlignHCenter | Qt.AlignVCenter)
        grid.addWidget(self.checked_label, 0, 18, 2, 2, Qt.AlignHCenter | Qt.AlignVCenter)
        grid.addWidget(self.prev_button, 2, 0, 12, 1)#, Qt.AlignVCenter)
        grid.addWidget(self.display_area, 2, 1, 12, 18)  # ,QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        grid.addWidget(self.next_button, 2, 19, 12, 1)#, Qt.AlignVCenter)
        grid.addWidget(self.text_box, 14, 0, 4, 20)
        grid.addWidget(self.restore_button, 18, 0, 2, 2)
        self.save_info = QLabel()
        grid.addWidget(self.save_info, 18, 6, 2, 2)
        grid.addWidget(self.auto_save, 18, 14, 2, 2)
        grid.addWidget(mark_button, 18, 16, 2, 2)
        grid.addWidget(self.save_button, 18, 18, 2, 2)
        self.setLayout(grid)

    def set_image(self, path):
        image_pixmap = QtGui.QPixmap(path)
        self.image.setPixmap(image_pixmap)

    def get_next_batch_data(self):
        if self.getting == False:
            self.getting = True
            data = self.driver.load_unchecked_img(10, self.size - self.checked)
            count = 0
            for d in data:
                count = count + 1
                img_path = utils.image_transform(utils.url_img_download(d['src']))
                d['local_path'] = img_path
                if 'plain_text' not in d.keys():
                    d['plain_text'] = ''
                self.data.append(d)
            self.size = self.size + count
            self.getting = False

    def set_info(self, data):
        self.uuid_label.setText(data['uuid'])
        if os.path.exists(data['local_path']):
            img_path = data['local_path']
        else:
            img_path = utils.image_transform(utils.url_img_download(data['src']))
        self.set_image(img_path)
        if data['resolved']:
            self.text_box.setText(data['plain_text'])
        else:
            self.text_box.setText('')
        self.text_box.setFocus()

    def prev_page(self):
        skip = False
        auto_save_model = self.auto_save.isChecked()
        # Text is unsaved, pop a message box
        if not auto_save_model and self.info_label.text().find("Unsave") != -1:
            reply = QMessageBox.question(self, 'Warning', 'Unsaved!Are you sure to leave?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                skip = True
        else:
            skip = True
        if auto_save_model:
            self.save()
        if skip and self.index > 0:
            self.index = self.index - 1
            data = self.data[self.index]
            self.set_info(data)
            self.copy_info.setText("")

    def next_page(self):
        skip = False
        auto_save_model = self.auto_save.isChecked()
        if not auto_save_model and self.info_label.text().find("Unsave") != -1:
            reply = QMessageBox.question(self, 'Warning', 'Unsaved!Are you sure to leave?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                skip = True
        else:
            skip = True
        if self.index + 6 >= self.size:
            try:
                Thread(target=self.get_next_batch_data).start()
            except Exception as e:
                print(e)
                exit()
        print(self.size, self.index)
        if auto_save_model:
            self.save()
        if skip and self.index + 1 != self.size:
            self.index += 1
            data = self.data[self.index]
            self.set_info(data)
            self.copy_info.setText("")

    def save(self):
        data = self.data[self.index]
        data['plain_text'] = self.text_box.toPlainText().strip()
        flag1 = not data['checked']
        data['resolved'] = True
        data['checked'] = True
        data['checking'] = False
        flag2 = self.driver.update_img_check_info(data)
        if flag1 and flag2:
            self.checked = self.checked + 1
            self.checked_label.setText(str(self.checked))
        self.save_button.setDisabled(True)
        self.info_label.setText("Saved!")
        self.save_info.setText(data['uuid'] + ' saved!')

    def restore(self):
        data = self.data[self.index]
        self.text_box.setText(data['plain_text'])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()

    sys.exit(app.exec_())

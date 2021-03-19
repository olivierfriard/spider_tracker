#!/usr/bin/env python3
"""
record click positions for images from a directory
"""

CHOOSE_REFERENTIAL = False

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import glob
import json
import pathlib
import shutil

__version__ = "2020.01.31"

IMAGE_HEIGHT = 720
IMAGE_EXTENSION = "jpg"


class ImageViewer(QWidget):

    def __init__(self):
        super().__init__()

        if len(sys.argv) == 1:
            img_dir = QFileDialog(self).getExistingDirectory(self, "Choose a directory of images",
                                                             "", options=QFileDialog.ShowDirsOnly)
            if not img_dir:
                sys.exit()
        else:
            img_dir = sys.argv[1]

        self.glb = sorted(glob.glob(img_dir + "/*." + IMAGE_EXTENSION))

        if not len(self.glb):
            QMessageBox.warning(self, "", "No images found", QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)
            sys.exit()

        self.idx = 0
        self.mem = {}
        self.ref = []

        # check if a file of results already exists
        filename_results = pathlib.Path(self.glb[self.idx]).parent.with_suffix(".txt")
        if filename_results.exists():
            print("reload results")
            for row in open(filename_results).readlines():
                try:
                    img, x, y = row.strip().split("\t")
                    self.mem[img] = (int(x), int(y))
                except Exception:
                    print(row.strip().split("\t"))

        self.mem_pos_xy = []


        vbox = QVBoxLayout()
        self.image = QLabel()

        vbox.addWidget(self.image)

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vbox.addItem(verticalSpacer)

        self.image.mousePressEvent = self.getPos
        self.setMouseTracking(True)

        self.hboxlayout = QHBoxLayout()

        '''
        self.cb_ref = QCheckBox("Def ref")
        self.hboxlayout.addWidget(self.cb_ref)
        '''

        '''
        self.n_objects = QLineEdit()
        self.hboxlayout.addWidget(self.n_objects)
        self.n_objects.setText("1")
        '''

        self.file_name = QLineEdit()
        self.file_name.setReadOnly(True)
        self.hboxlayout.addWidget(self.file_name)

        self.stat = QLineEdit()
        self.stat.setReadOnly(True)
        self.hboxlayout.addWidget(self.stat)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        self.hboxlayout.addWidget(self.clear_button)


        self.goto_button = QPushButton("go to")
        self.goto_button.clicked.connect(self.goto)
        self.hboxlayout.addWidget(self.goto_button)

        self.next_empty_button = QPushButton("Next img w/o positions")
        self.next_empty_button.clicked.connect(self.next_empty)
        self.hboxlayout.addWidget(self.next_empty_button)


        self.positions = QLineEdit()
        self.hboxlayout.addWidget(self.positions)

        self.save_data_button = QPushButton("save data to disk")
        self.save_data_button.clicked.connect(self.save_data)
        self.hboxlayout.addWidget(self.save_data_button)

        '''
        self.reset_button = QPushButton("delete positions")
        self.reset_button.clicked.connect(self.reset)
        self.hboxlayout.addWidget(self.reset_button)
        '''

        self.previous_button = QPushButton("previous")
        self.previous_button.clicked.connect(self.previous_image)
        self.hboxlayout.addWidget(self.previous_button)

        self.next_button = QPushButton("next")
        self.next_button.clicked.connect(lambda: self.next_image(False))
        self.hboxlayout.addWidget(self.next_button)

        self.next10_button = QPushButton("validate next 10")
        self.next10_button.clicked.connect(self.next10)
        self.hboxlayout.addWidget(self.next10_button)


        '''
        self.bt_skip = QPushButton("Skip")
        self.bt_skip.clicked.connect(self.skip)
        self.hboxlayout.addWidget(self.bt_skip)
        '''


        '''
        self.save_next_button = QPushButton("accept and next")
        self.save_next_button.clicked.connect(self.save_next_image)
        self.hboxlayout.addWidget(self.save_next_button)
        '''

        vbox.addLayout(self.hboxlayout)

        self.setLayout(vbox)

        self.file_name.setText(os.path.basename(self.glb[self.idx]))
        self.stat.setText("{} / {}".format(self.idx + 1, len(self.glb)))

        self.show()
        # self.showFullScreen()
        #self.showMaximized()

        self.load_image(self.glb[self.idx])

        if CHOOSE_REFERENTIAL and not self.ref:
            self.cb_ref.setChecked(True)
            QMessageBox.information(self, "Definition of the referential", "Click in this order the (0,0) point, the Xmax and the Ymax points",
                                    QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)

    def closeEvent(self, event):
        print("close")
        result = QMessageBox.question(self, "Info", "Do you want to save the results?", QMessageBox.Cancel | QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if result == QMessageBox.Yes:
            self.save_data()

        if result == QMessageBox.Cancel:
            event.ignore()

    def clear(self):
        """clear position on current image"""
        bn = os.path.basename(self.glb[self.idx])

        if bn in self.mem:
            self.mem[bn] = ()
            self.positions.setText("")
            self.mem_pos_xy = []

        self.mem_pos_xy = ()
        self.load_image(self.glb[self.idx])




    def next_empty(self):
        """
        go to the first image of list with empty positions
        """
        while True:
            self.idx += 1
            if self.idx >= len(self.glb):
                QMessageBox.information(self, "info", "All images have positions",
                                    QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)
                break

            if os.path.basename(self.glb[self.idx]) not in self.mem:
                self.idx -= 1

                self.mem_pos_xy = []

                self.next_image()
                break


    def goto(self):
        """
        go to an arbitrary image
        """
        i, okPressed = QInputDialog.getInt(self, "Go to an image index", "index:", 1, 0, 10000, 1)
        if okPressed:
            self.idx = i - 1
            print("go to ", self.idx)

            self.mem_pos_xy = []

            self.next_image()


    def skip(self):
        """
        skip image
        """
        self.reset()

        butta_dir = str(pathlib.Path(self.glb[self.idx]).parent) + "_BUTTA"
        if not os.path.isdir(butta_dir):
            os.mkdir(butta_dir)
        shutil.move(self.glb[self.idx], butta_dir)

        self.next_image()


    def save_data(self):
        """
        save data in json and TSV
        """

        filename_txt = pathlib.Path(self.glb[self.idx]).parent.with_suffix(".txt")
        print(filename_txt)
        # filename, _ = QFileDialog(self).getSaveFileName(self, "Save data", "", "All files (*)")
        out = ""
        '''
        # referential
        if "REF" in self.mem:
            out += "REF"
            for pos in self.mem["REF"]:
                out += "\t{}\t{}".format(pos[0],pos[1])
        out = out + "\n"
        '''

        for k in sorted(list(self.mem.keys())):
            if k == "REF":
                continue
            out += k + "\t"
            '''
            for i in range(int(self.n_objects.text())):
            '''
            out += "{}\t{}\t".format(self.mem[k][0], self.mem[k][1])
            out = out[:-1] + "\n"

        with open(filename_txt, "w") as f_out:
            f_out.write(out)

        '''
        filename_json = pathlib.Path(self.glb[self.idx]).parent.with_suffix(".json")
        data = json.dumps(self.mem)
        with open(filename_json, "w") as f_out:
            f_out.write(data)
        '''

        QMessageBox.information(self, "info", "Positions saved", QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)


    def reset(self):
        bn = os.path.basename(self.glb[self.idx])
        if bn in self.mem:
            del self.mem[bn]
        self.positions.setText("")
        self.mem_pos_xy = []

        self.load_image(self.glb[self.idx])


    def previous_image(self):
        """
        previous image without saving positions
        """

        if self.idx > 0:
            self.idx -= 1
            self.load_image(self.glb[self.idx])

            bn = os.path.basename(self.glb[self.idx])
            if bn in self.mem:
                self.positions.setText(str(self.mem[bn]))

                print("position already saved")

                painter = QPainter()
                painter.begin(self.image.pixmap())
                painter.setPen(QColor("red"))
                painter.drawEllipse(QPoint(self.mem[bn][0], self.mem[bn][1]), 3, 3)

                '''
                for i in range(int(self.n_objects.text())):
                    painter.drawEllipse(QPoint(self.objects_position[i][0], self.objects_position[i][1]), 3, 3)
                    painter.drawText(QPoint(self.objects_position[i][0] + 3, self.objects_position[i][1] + 3), str(i+1))
                '''
                painter.end()
                self.image.update()



            else:
                self.positions.setText("")
            self.file_name.setText(bn)
            self.stat.setText("{} / {}".format(self.idx + 1, len(self.glb)))

        else:
            QMessageBox.warning(self, "", "First image of directory", QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)


    def load_image(self, file_name):
        """
        load image in label
        scaled in height
        """
        pixmap = QPixmap()
        pixmap.load(file_name)
        pixmap = pixmap.scaledToHeight(IMAGE_HEIGHT)

        self.image.setPixmap(pixmap)


    def next10(self):
        bn = os.path.basename(self.glb[self.idx])
        if bn in self.mem:
            mem = self.mem[bn]
            for i in range(10):
                self.idx += 1
                bn = os.path.basename(self.glb[self.idx])
                self.mem[bn] = mem
                self.positions.setText(str(self.mem[bn]))
            self.idx -= 1
            self.next_image()


    def next_image(self, show_last=True):
        """
        next image
        """

        if self.idx < len(self.glb) - 1:
            self.idx += 1

            self.load_image(self.glb[self.idx])

            # bn_previous = os.path.basename(self.glb[self.idx - 1])

            bn = os.path.basename(self.glb[self.idx])

            if show_last:
                if bn not in self.mem and self.mem_pos_xy:
                    painter = QPainter()
                    painter.begin(self.image.pixmap())
                    painter.setPen(QColor("lime"))
                    painter.drawEllipse(QPoint(self.mem_pos_xy[0], self.mem_pos_xy[1]), 3, 3)
                    '''
                    for i in range(int(self.n_objects.text())):
                        painter.drawEllipse(QPoint(self.mem_pos_xy[i][0], self.mem_pos_xy[i][1]), 3, 3)
                        painter.drawText(QPoint(self.mem_pos_xy[i][0] + 3, self.mem_pos_xy[i][1] + 3), str(i+1))
                    '''

                    painter.end()
                    self.image.update()


            if bn in self.mem:
                print("position already saved")
                self.positions.setText(str(self.mem[bn]))

                painter = QPainter()
                painter.begin(self.image.pixmap())
                painter.setPen(QColor("red"))

                print(self.mem[bn][0], self.mem[bn][1])
                painter.drawEllipse(QPoint(self.mem[bn][0], self.mem[bn][1]), 3, 3)
                self.mem_pos_xy = self.mem[bn]
                '''
                for i in range(int(self.n_objects.text())):
                    painter.drawEllipse(QPoint(self.objects_position[i][0], self.objects_position[i][1]), 3, 3)
                    painter.drawText(QPoint(self.objects_position[i][0] + 3, self.objects_position[i][1] + 3), str(i+1))
                '''

                painter.end()
                self.image.update()

            else:
                self.positions.setText("")
            self.file_name.setText(bn)

            self.stat.setText("{} / {}".format(self.idx + 1, len(self.glb)))

        else:
            QMessageBox.warning(self, "", "Last image of directory", QMessageBox.Ok | QMessageBox.Default, QMessageBox.NoButton)


    def keyPressEvent(self, event):
        #print(event.key())

        bn = os.path.basename(self.glb[self.idx])

        if event.key() == Qt.Key_Z:
            self.previous_image()


        if event.key() == Qt.Key_X:
            self.next_image(False)



    def getPos(self, event):

        x = event.pos().x()
        y = event.pos().y()
        print(x, y)

        bn = os.path.basename(self.glb[self.idx])

        # positions
        if event.button() == Qt.LeftButton:

            self.load_image(self.glb[self.idx])
            painter = QPainter()
            painter.begin(self.image.pixmap())
            painter.setPen(QColor("red"))
            painter.drawEllipse(QPoint(x, y), 3, 3)
            painter.end()
            self.image.update()

            self.mem[bn] = (x, y)
            self.mem_pos_xy = (x,y)
            self.positions.setText(str(self.mem[bn]))
            self.next_image()

        # load next image
        if event.button() == Qt.RightButton:
            if bn not in self.mem:
                self.mem[bn] = self.mem_pos_xy
            self.positions.setText(str(self.mem[bn]))
            self.next_image()

        # validate previous positions
        if event.button() == Qt.MiddleButton:
            self.clear()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Click position - v. {}".format(__version__))
    ex = ImageViewer()
    sys.exit(app.exec_())

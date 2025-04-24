from qfluentwidgets import *
from PySide6.QtWidgets import *
import sys
from Widget_used import Banner
from PySide6.QtCore import *


class MainWindow(MSFluentWindow):
    def __init__(self):
        super().__init__()
        
        # 创建子界面
        
        self.homeInterface = QWidget()
        self.homeInterface.setObjectName("home")  # 必须设置唯一标识
        self.switch_theme()
        self.settingsInterface = QWidget()
        self.settingsInterface.setObjectName("settings")
        
        class Home(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("hometest")

                self.banner = Banner()
                self.banner_text = TextBrowser()



                widget = QWidget()
                Layout = QVBoxLayout(self)

                Layout.addWidget(self.banner)
                Layout.addWidget(self.banner_text)
                Layout.setStretch(0, 2)
                Layout.setStretch(1, 3)

                v_layout = QVBoxLayout(self.banner)

                # 空白占位符
                v_layout.addItem(
                    QSpacerItem(10, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )

                # 顶部部分 (按钮组)
                h1_layout = QHBoxLayout()
                h1_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

                # 左边留白区域
                h1_layout.addStretch()

                # 空白占位符
                h1_layout.addItem(
                    QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )

                # 将顶部水平布局添加到垂直布局
                v_layout.addLayout(h1_layout)

                # 中间留白区域
                v_layout.addItem(
                    QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )
                v_layout.addStretch()

                # 中间留白区域
                v_layout.addItem(
                    QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )
                v_layout.addStretch()

                # 底部部分 (图片切换按钮)
                h2_layout = QHBoxLayout()
                h2_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

                # 左边留白区域
                h2_layout.addItem(
                    QSpacerItem(20, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )

                # # 公告卡片
                # noticeCard = NoticeCard()
                # h2_layout.addWidget(noticeCard)

                h2_layout.addStretch()

                # 自定义图像按钮布局
                self.imageButton = PrimaryToolButton(FluentIcon.IMAGE_EXPORT)
                self.imageButton.setFixedSize(56, 56)
                self.imageButton.setIconSize(QSize(32, 32))


                v1_layout = QVBoxLayout()
                v1_layout.addWidget(self.imageButton, alignment=Qt.AlignmentFlag.AlignBottom)

                h2_layout.addLayout(v1_layout)

                # 空白占位符
                h2_layout.addItem(
                    QSpacerItem(25, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
                )

                # 将底部水平布局添加到垂直布局
                v_layout.addLayout(h2_layout)

                layout = QVBoxLayout()
                scrollArea = ScrollArea()
                scrollArea.setWidgetResizable(True)
                scrollArea.setWidget(widget)
                layout.addWidget(scrollArea)
                self.setLayout(layout)




        self.hometest = Home(self)

        
        # 添加子界面到导航栏
        self.addSubInterface(
            interface=self.hometest,
            icon=FluentIcon.HOME,
            text="主页",
            selectedIcon=FluentIcon.HOME,
            position=NavigationItemPosition.TOP,
        )

        self.addSubInterface(
            interface=self.homeInterface,
            icon=FluentIcon.HOME,
            text="主页",
            selectedIcon=FluentIcon.HOME_FILL,  # 选中时图标
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            interface=self.settingsInterface,
            icon=FluentIcon.SETTING,
            text="设置",
            position=NavigationItemPosition.BOTTOM  # 放在导航栏底部
        )



        # 显示窗口
        self.show()

    def switch_theme(self) -> None:
        """切换主题"""

        setTheme(
            Theme(darkdetect.theme()) if darkdetect.theme() else Theme.LIGHT, lazy=True
        )
        # QTimer.singleShot(300, lambda: setTheme(Theme.AUTO, lazy=True))



application = QApplication(sys.argv)
a = MainWindow()
a.switch_theme
sys.exit(application.exec())
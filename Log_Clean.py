'''
Gnay 26.11.2024 Kazakhstan
'''

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox,
    QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt
import os
import zipfile
import time
import logging
import sys

# 配置日志
logging.basicConfig(
    filename="cleanup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 软件根目录下的归档文件夹
ARCHIVE_ROOT_DIR = os.path.join(os.getcwd(), "file")
os.makedirs(ARCHIVE_ROOT_DIR, exist_ok=True)  # 如果不存在，则创建


class DirectoryItem(QWidget):
    """表示一个清理目录及相关设置的组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)

        # 日志目录
        self.dir_label = QLabel("日志目录:")
        layout.addWidget(self.dir_label, 0, 0)
        self.dir_input = QLineEdit()
        layout.addWidget(self.dir_input, 0, 1)
        self.select_dir_button = QPushButton("选择目录")
        layout.addWidget(self.select_dir_button, 0, 2)
        self.select_dir_button.clicked.connect(self.select_directory)

        # 删除天数
        self.days_label = QLabel("删除天数:")
        layout.addWidget(self.days_label, 1, 0)
        self.days_input = QLineEdit()
        self.days_input.setPlaceholderText("天数(默认30)")
        layout.addWidget(self.days_input, 1, 1, 1, 2)

        # 文件大小阈值
        self.size_label = QLabel("文件大小:")
        layout.addWidget(self.size_label, 2, 0)
        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("大小MB(默认100)")
        layout.addWidget(self.size_input, 2, 1, 1, 2)

    def select_directory(self):
        """选择日志目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择日志目录")
        if directory:
            self.dir_input.setText(directory)


class LogCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日志清理工具")
        self.setGeometry(100, 100, 900, 600)

        # 中央窗口和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

        # 添加初始目录条目
        self.dir_items = []
        self.add_directory_item()

        # 操作按钮区域
        self.buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton("添加清理目录")
        self.buttons_layout.addWidget(self.add_item_button)
        self.add_item_button.clicked.connect(self.add_directory_item)

        self.run_button = QPushButton("执行清理")
        self.buttons_layout.addWidget(self.run_button)
        self.run_button.clicked.connect(self.cleanup_logs)

        self.main_layout.addLayout(self.buttons_layout)

        # 日志输出区域
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.main_layout.addWidget(self.log_output)

    def add_directory_item(self):
        """添加一个清理目录条目"""
        group_box = QGroupBox(f"清理目录 {len(self.dir_items) + 1}")
        item = DirectoryItem(self)
        layout = QVBoxLayout(group_box)
        layout.addWidget(item)
        self.scroll_layout.addWidget(group_box)
        self.dir_items.append(item)

    def cleanup_logs(self):
        """执行清理任务"""
        self.log_output.append("开始清理多个目录...")

        for item in self.dir_items:
            cleanup_dir = item.dir_input.text().strip()
            days = item.days_input.text().strip()
            size = item.size_input.text().strip()

            if not cleanup_dir:
                self.log_output.append("跳过未配置的条目")
                continue

            try:
                max_days = int(days) if days else 30
                max_size_mb = int(size) if size else 100
            except ValueError:
                self.log_output.append(f"跳过无效设置的目录：{cleanup_dir}")
                continue

            self.process_directory(cleanup_dir, max_days, max_size_mb)

        self.log_output.append("清理任务完成！")
        QMessageBox.information(self, "完成", "所有目录清理任务已完成！")

    def process_directory(self, cleanup_dir, max_days, max_size_mb):
        """处理单个目录"""
        now = time.time()
        threshold_date = now - max_days * 86400
        max_size_bytes = max_size_mb * 1024 * 1024

        # 每个清理目录对应一个压缩文件
        archive_zip_path = os.path.join(ARCHIVE_ROOT_DIR, f"{os.path.basename(cleanup_dir)}_archived_logs.zip")
        with zipfile.ZipFile(archive_zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(cleanup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_stat = os.stat(file_path)
                        last_modified = file_stat.st_mtime
                        file_size = file_stat.st_size

                        # 归档所有文件
                        if last_modified < threshold_date or file_size > max_size_bytes:
                            zipf.write(file_path, os.path.relpath(file_path, cleanup_dir))
                            os.remove(file_path)
                            log_msg = f"归档文件: {file_path} 到 {archive_zip_path}"
                            logging.info(log_msg)
                            self.log_output.append(log_msg)

                    except Exception as e:
                        log_msg = f"无法处理文件 {file_path}: {e}"
                        logging.error(log_msg)
                        self.log_output.append(log_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogCleanerApp()
    window.show()
    sys.exit(app.exec())

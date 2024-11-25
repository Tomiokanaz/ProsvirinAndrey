import sys
import sqlite3
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QFormLayout, QDialog, QDialogButtonBox, QMessageBox, QProgressBar, QStatusBar
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

# Подключение к базе данных SQLite
def connect_db():
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("posts.db")
    if not db.open():
        print("Cannot establish a database connection")
        return False
    return True

# Сигнальный класс для обновления GUI
class SignalManager(QObject):
    data_loaded = pyqtSignal()  # Сигнал для обновления данных
    progress_updated = pyqtSignal(int)  # Сигнал для обновления прогресса

signal_manager = SignalManager()

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQLite Database Viewer with Async")
        self.setGeometry(100, 100, 800, 600)

        # Интерфейсные элементы
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by title...")
        self.search_field.textChanged.connect(self.search)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.load_data)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_record)

        self.load_button = QPushButton("Load Data")
        self.load_button.clicked.connect(self.load_data_from_server)

        self.progress_bar = QProgressBar()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Таблица для отображения данных
        self.table_view = QTableView()
        self.model = QSqlTableModel()
        self.model.setTable("posts")
        self.model.select()
        self.table_view.setModel(self.model)

        # Размещение элементов
        layout = QVBoxLayout()
        layout.addWidget(self.search_field)
        layout.addWidget(self.table_view)
        layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.load_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Соединяем сигналы
        signal_manager.data_loaded.connect(self.load_data)
        signal_manager.progress_updated.connect(self.update_progress_bar)

        # Таймер для периодического обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data_from_server)
        self.timer.start(10000)  # 10 секунд

    def search(self):
        search_text = self.search_field.text()
        filter_text = f"title LIKE '%{search_text}%'"
        self.model.setFilter(filter_text)
        self.model.select()

    def load_data(self):
        self.model.select()

    def open_add_dialog(self):
        dialog = AddRecordDialog(self)
        dialog.exec()

    def delete_record(self):
        selected_row = self.table_view.currentIndex().row()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a record to delete.")
            return

        confirm = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete this record?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.model.removeRow(selected_row)
            self.model.submitAll()
            self.load_data()

    def load_data_from_server(self):
        threading.Thread(target=self.fetch_and_save_data).start()

    def fetch_and_save_data(self):
        try:
            self.status_bar.showMessage("Loading data from server...")
            response = requests.get('https://jsonplaceholder.typicode.com/posts')
            response.raise_for_status()
            posts_data = response.json()

            # Сохраняем в базу данных в фоне
            with ThreadPoolExecutor() as executor:
                executor.submit(self.save_data_to_db, posts_data)

        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
        finally:
            self.status_bar.clearMessage()

    def save_data_to_db(self, posts):
        db = sqlite3.connect("posts.db")
        cursor = db.cursor()

        for i, post in enumerate(posts):
            cursor.execute('''
                INSERT OR IGNORE INTO posts (id, user_id, title, body)
                VALUES (?, ?, ?, ?)
            ''', (post['id'], post['userId'], post['title'], post['body']))

            # Обновляем прогресс
            signal_manager.progress_updated.emit(int((i + 1) / len(posts) * 100))
        db.commit()
        db.close()

        # Сообщаем о завершении
        signal_manager.data_loaded.emit()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

# Диалог для добавления записи
class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add New Record")
        self.setGeometry(100, 100, 400, 200)

        self.user_id_field = QLineEdit()
        self.title_field = QLineEdit()
        self.body_field = QLineEdit()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add_record)
        buttons.rejected.connect(self.reject)

        form_layout = QFormLayout()
        form_layout.addRow("User ID:", self.user_id_field)
        form_layout.addRow("Title:", self.title_field)
        form_layout.addRow("Body:", self.body_field)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def add_record(self):
        user_id = self.user_id_field.text()
        title = self.title_field.text()
        body = self.body_field.text()

        if not user_id or not title or not body:
            QMessageBox.warning(self, "Warning", "All fields are required.")
            return

        query = f"INSERT INTO posts (user_id, title, body) VALUES ({user_id}, '{title}', '{body}')"
        db = QSqlDatabase.database()
        if db.open():
            db.exec(query)
            self.accept()
            self.parent().load_data()

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not connect_db():
        sys.exit(1)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

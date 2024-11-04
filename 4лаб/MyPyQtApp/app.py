import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QLineEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QFormLayout, QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

# Подключение к базе данных SQLite
def connect_db():
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("posts.db")
    if not db.open():
        print("Cannot establish a database connection")
        return False
    return True

# Класс основного окна приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQLite Database Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Создаем интерфейсные элементы
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by title...")
        self.search_field.textChanged.connect(self.search)

        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.load_data)

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.open_add_dialog)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_record)

        # Создаем таблицу для отображения данных
        self.table_view = QTableView()
        self.model = QSqlTableModel()
        self.model.setTable("posts")
        self.model.select()
        self.table_view.setModel(self.model)

        # Размещение виджетов
        layout = QVBoxLayout()
        layout.addWidget(self.search_field)
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # Функция поиска по полю заголовка
    def search(self):
        search_text = self.search_field.text()
        filter_text = f"title LIKE '%{search_text}%'"
        self.model.setFilter(filter_text)
        self.model.select()

    # Функция загрузки данных в таблицу
    def load_data(self):
        self.model.select()

    # Открытие диалога для добавления записи
    def open_add_dialog(self):
        dialog = AddRecordDialog(self)
        dialog.exec()

    # Удаление выбранной записи
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

# Диалог для добавления новой записи
class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Add New Record")
        self.setGeometry(100, 100, 400, 200)

        # Поля ввода для новой записи
        self.user_id_field = QLineEdit()
        self.title_field = QLineEdit()
        self.body_field = QLineEdit()

        # Кнопки диалога
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add_record)
        buttons.rejected.connect(self.reject)

        # Размещение виджетов в форме
        form_layout = QFormLayout()
        form_layout.addRow("User ID:", self.user_id_field)
        form_layout.addRow("Title:", self.title_field)
        form_layout.addRow("Body:", self.body_field)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    # Добавление новой записи в базу данных
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

# Основной запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not connect_db():
        sys.exit(1)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

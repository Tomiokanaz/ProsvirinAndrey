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
    """
    Устанавливает соединение с базой данных SQLite.
    Если соединение не удалось, возвращает False.
    """
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName("posts.db")  # Указываем имя файла базы данных
    if not db.open():
        print("Cannot establish a database connection")  # Выводим ошибку в случае сбоя
        return False
    return True

# Сигнальный класс для обновления GUI
class SignalManager(QObject):
    """
    Класс для управления пользовательскими сигналами.
    Используется для передачи событий между потоками и интерфейсом.
    """
    data_loaded = pyqtSignal()  # Сигнал для обновления данных
    progress_updated = pyqtSignal(int)  # Сигнал для обновления прогресса

# Создаем объект сигналов
signal_manager = SignalManager()

# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        """
        Инициализация главного окна приложения.
        Создает все элементы интерфейса и настраивает взаимодействие между ними.
        """
        super().__init__()

        # Настройки окна
        self.setWindowTitle("SQLite Database Viewer with Async")
        self.setGeometry(100, 100, 800, 600)

        # Создаем поле для поиска
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search by title...")  # Текст внутри поля
        self.search_field.textChanged.connect(self.search)  # Подключение к функции поиска

        # Создаем кнопки управления
        self.update_button = QPushButton("Update")
        self.update_button.clicked.connect(self.load_data)  # Обновление данных

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self.open_add_dialog)  # Добавление записи

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_record)  # Удаление записи

        self.load_button = QPushButton("Load Data")
        self.load_button.clicked.connect(self.load_data_from_server)  # Загрузка данных с сервера

        # Создаем прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)  # Начальное значение прогресса

        # Создаем статус-бар для отображения сообщений
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Создаем таблицу для отображения данных из базы
        self.table_view = QTableView()
        self.model = QSqlTableModel()
        self.model.setTable("posts")  # Указываем таблицу
        self.model.select()  # Загружаем данные
        self.table_view.setModel(self.model)  # Привязываем модель к таблице

        # Компонуем элементы интерфейса
        layout = QVBoxLayout()
        layout.addWidget(self.search_field)
        layout.addWidget(self.table_view)
        layout.addWidget(self.progress_bar)

        # Располагаем кнопки горизонтально
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.load_button)

        layout.addLayout(button_layout)

        # Устанавливаем общий контейнер для интерфейса
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Соединяем сигналы с функциями обновления
        signal_manager.data_loaded.connect(self.load_data)  # Сигнал для обновления данных
        signal_manager.progress_updated.connect(self.update_progress_bar)  # Сигнал для обновления прогресса

        # Создаем таймер для периодического обновления данных
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data_from_server)  # Каждое срабатывание вызывает загрузку данных
        self.timer.start(10000)  # Запуск таймера с интервалом 10 секунд

    def search(self):
        """
        Фильтрует данные в таблице на основе введенного текста.
        """
        search_text = self.search_field.text()  # Получаем текст из поля поиска
        filter_text = f"title LIKE '%{search_text}%'"  # Формируем SQL-фильтр
        self.model.setFilter(filter_text)  # Устанавливаем фильтр для модели
        self.model.select()  # Применяем изменения

    def load_data(self):
        """
        Перезагружает данные из базы в таблицу.
        """
        self.model.select()

    def open_add_dialog(self):
        """
        Открывает диалог для добавления новой записи.
        """
        dialog = AddRecordDialog(self)
        dialog.exec()

    def delete_record(self):
        """
        Удаляет выбранную запись из таблицы.
        """
        selected_row = self.table_view.currentIndex().row()  # Получаем индекс выбранной строки
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a record to delete.")  # Если строка не выбрана
            return

        # Диалог подтверждения
        confirm = QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete this record?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.model.removeRow(selected_row)  # Удаляем строку
            self.model.submitAll()  # Подтверждаем изменения
            self.load_data()  # Обновляем данные

    def load_data_from_server(self):
        """
        Загружает данные с сервера в фоновом потоке.
        """
        threading.Thread(target=self.fetch_and_save_data).start()

    def fetch_and_save_data(self):
        """
        Выполняет HTTP-запрос к серверу и сохраняет данные в базу.
        """
        try:
            self.status_bar.showMessage("Loading data from server...")  # Уведомляем пользователя
            response = requests.get('https://jsonplaceholder.typicode.com/posts')  # Запрос к серверу
            response.raise_for_status()
            posts_data = response.json()

            # Сохраняем данные в базе через пул потоков
            with ThreadPoolExecutor() as executor:
                executor.submit(self.save_data_to_db, posts_data)

        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")  # Сообщаем об ошибке
        finally:
            self.status_bar.clearMessage()  # Очищаем статус-бар

    def save_data_to_db(self, posts):
        """
        Сохраняет данные в базу SQLite с обновлением прогресса.
        """
        db = sqlite3.connect("posts.db")
        cursor = db.cursor()

        for i, post in enumerate(posts):
            # Вставляем данные в таблицу, избегая дублирования
            cursor.execute('''
                INSERT OR IGNORE INTO posts (id, user_id, title, body)
                VALUES (?, ?, ?, ?)
            ''', (post['id'], post['userId'], post['title'], post['body']))

            # Обновляем прогресс-бар через сигнал
            signal_manager.progress_updated.emit(int((i + 1) / len(posts) * 100))
        db.commit()
        db.close()

        # Сигнализируем о завершении загрузки данных
        signal_manager.data_loaded.emit()

    def update_progress_bar(self, value):
        """
        Обновляет значение прогресс-бара.
        """
        self.progress_bar.setValue(value)

# Диалог для добавления записи
class AddRecordDialog(QDialog):
    def __init__(self, parent=None):
        """
        Инициализация диалога добавления записи.
        """
        super().__init__(parent)

        self.setWindowTitle("Add New Record")
        self.setGeometry(100, 100, 400, 200)

        # Поля для ввода данных
        self.user_id_field = QLineEdit()
        self.title_field = QLineEdit()
        self.body_field = QLineEdit()

        # Кнопки OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add_record)
        buttons.rejected.connect(self.reject)

        # Компоновка виджетов
        form_layout = QFormLayout()
        form_layout.addRow("User ID:", self.user_id_field)
        form_layout.addRow("Title:", self.title_field)
        form_layout.addRow("Body:", self.body_field)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def add_record(self):
        """
        Добавляет новую запись в базу данных.
        """
        user_id = self.user_id_field.text()
        title = self.title_field.text()
        body = self.body_field.text()

        if not user_id or not title or not body:  # Проверка на заполненность всех полей
            QMessageBox.warning(self, "Warning", "All fields are required.")
            return

        # Формируем SQL-запрос
        query = f"INSERT INTO posts (user_id, title, body) VALUES ({user_id}, '{title}', '{body}')"
        db = QSqlDatabase.database()  # Получаем активное соединение
        if db.open():
            db.exec(query)  # Выполняем запрос
            self.accept()  # Закрываем диалог
            self.parent().load_data()  # Обновляем таблицу

# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not connect_db():  # Проверка соединения с базой
        sys.exit(1)

    window = MainWindow()  # Создаем главное окно
    window.show()  # Показываем окно

    sys.exit(app.exec_())  # Запускаем основной цикл приложения

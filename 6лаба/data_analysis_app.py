import sys
import pandas as pd  # Библиотека для работы с табличными данными (CSV, DataFrame)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QFileDialog, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QTextEdit
)  # Модули PyQt5 для создания интерфейса
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure  # Модули Matplotlib для построения графиков


class DataAnalysisApp(QMainWindow):
    """
    Основной класс приложения для анализа и визуализации данных.
    Наследует QMainWindow для реализации главного окна приложения.
    """
    def __init__(self):
        super().__init__()  # Инициализация родительского класса QMainWindow

        # Устанавливаем название окна и его размеры
        self.setWindowTitle("Анализ данных и визуализация")
        self.setGeometry(100, 100, 800, 600)

        # Создаем центральный виджет, куда будут добавляться все элементы интерфейса
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Основной вертикальный макет для всех элементов интерфейса
        self.layout = QVBoxLayout(self.central_widget)

        # Кнопка для загрузки данных из CSV-файла
        self.load_button = QPushButton("Загрузить CSV файл")  # Создаем кнопку
        self.load_button.clicked.connect(self.load_data)  # Привязываем метод load_data к нажатию кнопки
        self.layout.addWidget(self.load_button)  # Добавляем кнопку в общий макет

        # Поле для отображения общей статистики (кол-во строк и столбцов)
        self.stats_label = QLabel("Здесь будет отображена статистика")  # Создаем текстовое поле
        self.layout.addWidget(self.stats_label)  # Добавляем его в макет

        # Поле для отображения детальной статистики (минимумы, максимумы, средние значения)
        self.stats_text = QTextEdit()  # Создаем текстовое поле многострочного формата
        self.stats_text.setReadOnly(True)  # Делаем его доступным только для чтения
        self.layout.addWidget(self.stats_text)  # Добавляем его в макет

        # Выпадающий список для выбора типа графика (линейный, гистограмма, круговая диаграмма)
        self.chart_type = QComboBox()  # Создаем выпадающий список
        self.chart_type.addItems(["Линейный график", "Гистограмма", "Круговая диаграмма"])  # Добавляем варианты
        self.chart_type.currentIndexChanged.connect(self.update_chart)  # Привязываем метод обновления графика
        self.layout.addWidget(self.chart_type)  # Добавляем список в макет

        # Поле для отображения графиков
        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))  # Создаем область для графиков
        self.layout.addWidget(self.canvas)  # Добавляем в макет

        # Поле для ручного добавления данных
        self.add_data_layout = QHBoxLayout()  # Создаем горизонтальный макет для поля ввода и кнопки
        self.value_input = QLineEdit()  # Поле ввода текста
        self.value_input.setPlaceholderText("Введите новое значение (через запятую)")  # Подсказка для пользователя
        self.add_data_button = QPushButton("Добавить")  # Кнопка для добавления данных
        self.add_data_button.clicked.connect(self.add_value)  # Привязываем метод добавления данных
        self.add_data_layout.addWidget(self.value_input)  # Добавляем поле ввода в макет
        self.add_data_layout.addWidget(self.add_data_button)  # Добавляем кнопку в макет
        self.layout.addLayout(self.add_data_layout)  # Добавляем горизонтальный макет в общий макет

        # Таблица для отображения загруженных данных
        self.data_table = QTableWidget()  # Создаем таблицу
        self.layout.addWidget(self.data_table)  # Добавляем таблицу в макет

        # Переменная для хранения данных в виде DataFrame (из библиотеки pandas)
        self.data = None  # Изначально данных нет

    def load_data(self):
        """
        Метод для загрузки данных из CSV файла.
        Выполняет обработку данных и отображает их в таблице.
        """
        # Открываем диалог для выбора файла, поддерживаются только файлы с расширением .csv
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV файл", "", "CSV Files (*.csv)")
        if file_path:  # Проверяем, выбран ли файл
            try:
                self.data = pd.read_csv(file_path)  # Загружаем данные в DataFrame

                # Преобразуем столбец 'Date' в формат даты, если он существует
                if 'Date' in self.data.columns:
                    self.data['Date'] = pd.to_datetime(self.data['Date'], errors='coerce')

                # Преобразуем числовые столбцы, чтобы они имели тип float или int
                numeric_columns = ['Value1', 'Value2']
                for column in numeric_columns:
                    if column in self.data.columns:
                        self.data[column] = pd.to_numeric(self.data[column], errors='coerce')

                # Удаляем строки с некорректными или пропущенными значениями
                self.data = self.data.dropna()

                # Обновляем интерфейс: статистика, таблица, график
                self.update_stats()
                self.update_table()
                self.update_chart()
            except Exception as e:
                # Если произошла ошибка, выводим её в поле статистики
                self.stats_label.setText(f"Ошибка при загрузке данных: {e}")

    def update_stats(self):
        """
        Обновляет основную и детальную статистику загруженных данных.
        """
        if self.data is not None and not self.data.empty:  # Проверяем, что данные не пусты
            try:
                numeric_data = self.data.select_dtypes(include=['number'])  # Берем только числовые столбцы

                # Отображаем основную статистику (строки и столбцы)
                stats = f"""
                Количество строк: {len(self.data)}
                Количество столбцов: {len(self.data.columns)}
                """
                self.stats_label.setText(stats)

                # Формируем детальную статистику для числовых данных
                if not numeric_data.empty:
                    detailed_stats = f"""
                    Минимальные значения:\n{numeric_data.min()}
                    Максимальные значения:\n{numeric_data.max()}
                    Средние значения:\n{numeric_data.mean()}
                    """
                    self.stats_text.setText(detailed_stats)
                else:
                    self.stats_text.setText("Нет числовых данных для расчета статистики.")
            except Exception as e:
                self.stats_label.setText(f"Ошибка при вычислении статистики: {e}")
        else:
            # Если данные отсутствуют, отображаем сообщение
            self.stats_label.setText("Данные не загружены или таблица пуста.")
            self.stats_text.setText("Пожалуйста, загрузите данные.")

    def update_table(self):
        """
        Отображает данные в виде таблицы.
        """
        if self.data is not None:  # Если данные существуют
            self.data_table.setRowCount(len(self.data))  # Устанавливаем количество строк
            self.data_table.setColumnCount(len(self.data.columns))  # Устанавливаем количество столбцов
            self.data_table.setHorizontalHeaderLabels(self.data.columns)  # Устанавливаем заголовки столбцов
            # Заполняем таблицу данными из DataFrame
            for i in range(len(self.data)):
                for j in range(len(self.data.columns)):
                    self.data_table.setItem(i, j, QTableWidgetItem(str(self.data.iloc[i, j])))

    def update_chart(self):
        """
        Отображает график на основе данных и выбранного типа графика.
        """
        if self.data is not None:
            chart_type = self.chart_type.currentText()  # Получаем выбранный тип графика

            # Очищаем предыдущий график
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)

            if chart_type == "Линейный график":
                if 'Date' in self.data.columns and 'Value1' in self.data.columns:
                    ax.plot(self.data['Date'], self.data['Value1'], label='Value1')
                    ax.set_title("Линейный график")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Value1")
                else:
                    ax.text(0.5, 0.5, "Отсутствуют нужные данные", ha='center')

            elif chart_type == "Гистограмма":
                if 'Date' in self.data.columns and 'Value2' in self.data.columns:
                    ax.bar(self.data['Date'], self.data['Value2'], label='Value2')
                    ax.set_title("Гистограмма")
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Value2")
                else:
                    ax.text(0.5, 0.5, "Отсутствуют нужные данные", ha='center')

            elif chart_type == "Круговая диаграмма":
                if 'Category' in self.data.columns:
                    self.data['Category'].value_counts().plot.pie(ax=ax, autopct='%1.1f%%')
                    ax.set_title("Круговая диаграмма")
                else:
                    ax.text(0.5, 0.5, "Отсутствуют нужные данные", ha='center')

            ax.legend()  # Добавляем легенду
            self.canvas.draw()  # Отображаем график

    def add_value(self):
        """
        Добавляет новую строку данных, введенную вручную.
        """
        new_value = self.value_input.text()  # Получаем данные из поля ввода
        if self.data is not None and new_value:  # Проверяем, что данные существуют и ввод не пуст
            try:
                new_values = new_value.split(',')  # Разделяем данные по запятой
                if len(new_values) != len(self.data.columns):  # Проверяем, что количество данных совпадает с столбцами
                    raise ValueError("Число введённых значений не соответствует числу столбцов!")

                # Создаем новую строку как DataFrame
                new_row = pd.DataFrame([new_values], columns=self.data.columns)

                # Преобразуем числовые столбцы
                numeric_columns = ['Value1', 'Value2']  # Преобразуем числовые столбцы
                numeric_columns = ['Value1', 'Value2']  # Определяем числовые столбцы
                for column in numeric_columns:
                    if column in new_row.columns:  # Проверяем, что столбец существует в новой строке
                        new_row[column] = pd.to_numeric(new_row[column], errors='coerce')  # Преобразуем данные в числа

                # Добавляем новую строку в основной DataFrame
                self.data = pd.concat([self.data, new_row], ignore_index=True)  # Добавляем строку в конец данных

                # Обновляем интерфейс после добавления данных
                self.update_stats()  # Обновляем статистику
                self.update_table()  # Обновляем таблицу
                self.update_chart()  # Перестраиваем график
            except Exception as e:
                # Если возникает ошибка, выводим её в поле статистики
                self.stats_label.setText(f"Ошибка: {e}")


if __name__ == "__main__":
    # Создаем приложение
    app = QApplication(sys.argv)

    # Создаем и показываем главное окно приложения
    window = DataAnalysisApp()
    window.show()

    # Запускаем основной цикл приложения
    sys.exit(app.exec())


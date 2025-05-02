import sys, os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QDoubleSpinBox,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QLabel, QDialog
)

from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from Core import Specimen
import seaborn as sns

class MatplotlibCanvas(FigureCanvas):
    """Canvas для отображения графика Matplotlib"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

        self.ax2 = None

class SettingsDialog(QDialog):
    """Диалоговое окно для загрузки и редактирования параметров установки"""
    def __init__(self, settings_data):
        super().__init__()
        self.setWindowTitle("Параметры установки")
        self.setGeometry(200, 200, 300, 400)

        self.settings_data = settings_data

        self.layout = QVBoxLayout()

        self.load_json_button = QPushButton("Загрузить параметры из JSON")
        self.load_json_button.clicked.connect(self.load_json)
        self.layout.addWidget(self.load_json_button)

        self.save_button = QPushButton("Сохранить параметры")
        self.save_button.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_button)

        self.param_list = QTableWidget()
        self.layout.addWidget(QLabel("Загруженные параметры:"))
        self.layout.addWidget(self.param_list)

        self.setLayout(self.layout)
        self.review_list()

    def review_list(self):
        """Заполняем таблицу параметров"""
        self.param_list.clear()
        self.param_list.setColumnCount(2)
        self.param_list.setHorizontalHeaderLabels(["Параметр", "Значение"])

        # Заполняем таблицу значениями из settings_data
        for i, (key, value) in enumerate(self.settings_data.items()):
            self.param_list.insertRow(i)
            self.param_list.setItem(i, 0, QTableWidgetItem(key))
            self.param_list.setItem(i, 1, QTableWidgetItem(str(value)))

    def load_json(self):
        """Загружаем параметры из JSON файла"""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите JSON файл", "", "JSON files (*.json)")
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.settings_data.update(data)
                self.review_list()
                self.accept()
            except Exception as e:
                print(f"Ошибка загрузки JSON: {e}")

    def save_changes(self):
        """Сохраняем изменения из таблицы обратно в settings_data."""
        for row in range(self.param_list.rowCount()):
            key_item = self.param_list.item(row, 0)
            value_item = self.param_list.item(row, 1)
            
            # Получаем ключ и значение
            if key_item and value_item:
                key = key_item.text()
                try:
                    value = int(value_item.text())
                except ValueError:
                    # Если не int, пробуем float
                    try:
                        value = float(value_item.text())
                    except ValueError:
                        # Если вообще не число, оставляем как есть (строка)
                        value = value_item.text()

                # Обновляем словарь settings_data с новыми значениями
                self.settings_data[key] = value

        print("Изменения сохранены:", self.settings_data)

class SHPB_GUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SHPB GUI")
        self.setGeometry(100, 100, 1000, 600)

        self.settings_data = {}  # Сюда будут загружаться параметры установки
        self.active_specimens = []  # Список для хранения активных образцов
        self.specimens = [] # Список образцов

        self.init_ui()

    def init_ui(self):
        # Основной layout
        main_layout = QHBoxLayout()

        # Левая панель для кнопки и таблицы
        left_panel = QVBoxLayout()

        # Кнопка для загрузки параметров установки
        self.settings_button = QPushButton("Загрузить параметры из JSON")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        left_panel.addWidget(self.settings_button)

        # Кнопка для загрузки файла .xlsx
        self.load_journal_button = QPushButton("Загрузить журнал испытаний (xlsx)")
        self.load_journal_button.clicked.connect(self.load_journal)
        left_panel.addWidget(self.load_journal_button)

        # Таблица для отображения образцов
        self.specimen_table = QTableWidget()
        self.specimen_table.setColumnCount(2)
        self.specimen_table.setHorizontalHeaderLabels(["Номер образца", "StrainRate"])
        self.specimen_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.specimen_table.setSelectionMode(QTableWidget.MultiSelection)
        self.specimen_table.itemSelectionChanged.connect(self.update_active_specimens)
        left_panel.addWidget(QLabel("Список образцов:"))
        left_panel.addWidget(self.specimen_table)

        # Кнопка для обновления всех образцов с новыми параметрами
        self.update_specimens_button = QPushButton("Обновить препроцессинг")
        self.update_specimens_button.clicked.connect(self.update_all_specimens)
        left_panel.addWidget(self.update_specimens_button)

        self.plot_raw_button = QPushButton("Построить весь сигнал")
        self.plot_raw_button.clicked.connect(self.plot_raw)
        left_panel.addWidget(self.plot_raw_button)

        self.plot_balance_button = QPushButton("Построить баланс")
        self.plot_balance_button.clicked.connect(self.plot_balance)
        left_panel.addWidget(self.plot_balance_button)

        self.plot_diagram_button = QPushButton("Построить диаграмму")
        self.plot_diagram_button.clicked.connect(self.plot_diagram)
        left_panel.addWidget(self.plot_diagram_button)

        self.plot_strain_button = QPushButton("Построить деформации")
        self.plot_strain_button.clicked.connect(self.plot_strain)
        left_panel.addWidget(self.plot_strain_button)

        self.smoothing_layout = QHBoxLayout()
        self.smoothing_label = QLabel("Количество точек для скользящего среднего:")
        self.smoothing_spinbox = QSpinBox()
        self.smoothing_spinbox.setMinimum(1)
        self.smoothing_spinbox.setMaximum(1000)
        self.smoothing_spinbox.setValue(50)  # Значение по умолчанию

        self.smoothing_layout.addWidget(self.smoothing_label)
        self.smoothing_layout.addWidget(self.smoothing_spinbox)
        left_panel.addLayout(self.smoothing_layout)

        self.trig_start_layout = QHBoxLayout()
        self.trig_start_label = QLabel("Общая часть нулевого уровня (мкс):")
        self.trig_start_spinbox = QSpinBox()
        self.trig_start_spinbox.setMinimum(1)
        self.trig_start_spinbox.setMaximum(1000)
        self.trig_start_spinbox.setValue(50)  # Значение по умолчанию

        self.trig_start_layout.addWidget(self.trig_start_label)
        self.trig_start_layout.addWidget(self.trig_start_spinbox)
        left_panel.addLayout(self.trig_start_layout)

        self.zeroCoef_spinbox_layout = QHBoxLayout()
        self.zeroCoef_spinbox_label = QLabel("Триггер нулевого уровня (часть от K):")
        self.zeroCoef_spinbox = QDoubleSpinBox()
        self.zeroCoef_spinbox.setDecimals(2)  # например, 2 знака после запятой
        self.zeroCoef_spinbox.setSingleStep(0.1)  # шаг изменения при клике
        self.zeroCoef_spinbox.setRange(0.0, 10.0)  # например, задаем долю от 0 до 10
        self.zeroCoef_spinbox.setValue(1.0)  # значение по умолчанию

        self.zeroCoef_spinbox_layout.addWidget(self.zeroCoef_spinbox_label)
        self.zeroCoef_spinbox_layout.addWidget(self.zeroCoef_spinbox)
        left_panel.addLayout(self.zeroCoef_spinbox_layout)

        # Правая панель для графика
        right_panel = QVBoxLayout()
        self.canvas = MatplotlibCanvas(self, width=6, height=5, dpi=100)
        right_panel.addWidget(self.canvas)


        # Добавляем обе панели в главный layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)

        self.setLayout(main_layout)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings_data)
        dialog.exec_()

    def create_specimens_from_dataframe(self, df):
        """Создает Specimen-объекты из DataFrame и сохраняет их в self.specimens."""
        for _, row in df.iterrows():
            GUI_parameters = {
                'rm_window':self.smoothing_spinbox.value(),
                'trig_start':self.trig_start_spinbox.value(),
                'zeroCoef':self.zeroCoef_spinbox.value()
            }
            specimen = Specimen(**GUI_parameters, **row.to_dict(), **self.settings_data)
            self.specimens.append(specimen)

    def refresh_specimen_table(self):
        """Обновляет таблицу specimen_table на основе списка self.specimens."""
        self.specimen_table.setRowCount(0)  # Очищаем таблицу

        for idx, specimen in enumerate(self.specimens):
            self.specimen_table.insertRow(idx)
            self.specimen_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.specimen_table.setItem(idx, 1, QTableWidgetItem(str(specimen.strainRate)))


    def load_journal(self):
        """Загружаем журнал испытаний из файла .xlsx и создаем Specimen объекты."""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл журнала", "", "Excel files (*.xlsx)")
        if filename:
            try:
                df = pd.read_excel(filename)  # Чтение данных из файла .xlsx
                df['filename'] = os.path.dirname(filename)+r'/'+df['filename']
                # Для каждой строки в таблице данных создаем новый Specimen
                self.create_specimens_from_dataframe(df)
                self.refresh_specimen_table()

            except Exception as e:
                print(f"Ошибка загрузки файла: {e}")

    def update_active_specimens(self):
        """Обновляем список активных образцов в зависимости от выбора в таблице."""
        selected_rows = self.specimen_table.selectionModel().selectedRows()
        self.active_specimens.clear()  # Очищаем текущий список активных образцов
        
        # Добавляем активные образцы из выбранных строк
        for selected in selected_rows:
            row = selected.row()
            specimen = self.specimens[row]
            specimen_number = self.specimen_table.item(row, 0).text()  # берем номер из первой колонки
            self.active_specimens.append((specimen_number, specimen))

    def update_all_specimens(self):
        print('Препроцессинг запущен.')
        for specimen in self.specimens:
            record = specimen.record
            record.update(self.settings_data)
            GUI_parameters = {
                'rm_window':self.smoothing_spinbox.value(),
                'trig_start':self.trig_start_spinbox.value(),
                'zeroCoef':self.zeroCoef_spinbox.value()
            }
            record.update(GUI_parameters)
            specimen(**record)
        self.refresh_specimen_table()


    def plot_diagram(self):
        if not self.active_specimens:
            print("Нет активных образцов для построения.")
            return

        if self.canvas.ax2:
            self.canvas.ax2.remove()
            self.canvas.ax2 = None
        self.canvas.axes.clear()

        for number, specimen in self.active_specimens:
            sns.lineplot(
                data=specimen.dfP,
                x='StrainTrue',
                y='StressTrue/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number}"
            )
        self.canvas.axes.legend()  # показываем легенду с номерами образцов
        self.canvas.axes.set_title("Графики активных образцов")
        self.canvas.axes.set_xlabel("Истинная деформация")
        self.canvas.axes.set_ylabel("Истинное напряжение (МПа)")
        self.canvas.draw()

    def plot_balance(self):
        if not self.active_specimens:
            print("Нет активных образцов для построения.")
            return

        if self.canvas.ax2:
            self.canvas.ax2.remove()
            self.canvas.ax2 = None
        self.canvas.axes.clear()

        for number, specimen in self.active_specimens:
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='I/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} I"
            )
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='T/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} T"
            )
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='R/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} R"
            )
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='I+R/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} I+R"
            )
        self.canvas.axes.legend()  # показываем легенду с номерами образцов
        self.canvas.axes.set_title("Графики активных образцов")
        self.canvas.axes.set_xlabel("Время (мкс)")
        self.canvas.axes.set_ylabel("Напряжение (МПа)")
        self.canvas.draw()

    def plot_raw(self):
        if not self.active_specimens:
            print("Нет активных образцов для построения.")
            return

        if self.canvas.ax2:
            self.canvas.ax2.remove()
            self.canvas.ax2 = None
        self.canvas.axes.clear()

        for number, specimen in self.active_specimens:
            sns.lineplot(
                data=specimen.df,
                x='Time/mus',
                y='CH1/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} CH1"
            )
            sns.lineplot(
                data=specimen.df,
                x='Time/mus',
                y='CH2/MPa',
                ax=self.canvas.axes,
                label=f"Specimen {number} CH2"
            )
        
        self.canvas.axes.legend()  # показываем легенду с номерами образцов
        self.canvas.axes.set_title("Графики активных образцов")
        self.canvas.axes.set_xlabel("Время (мкс)")
        self.canvas.axes.set_ylabel("Напряжение (МПа)")
        self.canvas.draw()

    def plot_strain(self):
        if not self.active_specimens:
            print("Нет активных образцов для построения.")
            return

        if self.canvas.ax2:
            self.canvas.ax2.remove()
            self.canvas.ax2 = None
        self.canvas.axes.clear()

        self.canvas.ax2=self.canvas.axes.twinx()

        for number, specimen in self.active_specimens:
            
            # Левый график: strain
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='Strain',
                ax=self.canvas.axes,
                label=f"Specimen {number} strain"
            )
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='StrainTrue',
                ax=self.canvas.axes,
                label=f"Specimen {number} true strain"
            )
            
            # Правый график: strainRate
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='dotStrain',
                ax=self.canvas.ax2,
                label=f"Specimen {number} dot strain"
            )
            sns.lineplot(
                data=specimen.dfP,
                x='Time/mus',
                y='dotStrainTrue',
                ax=self.canvas.ax2,
                label=f"Specimen {number} dot true strain"
            )

        self.canvas.axes.set_xlabel("Время (мкс)")
        self.canvas.axes.set_ylabel("Strain Rate")
        self.canvas.ax2.set_ylabel("Strain")

        # Чтобы легенда работала корректно
        self.canvas.axes.legend()

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SHPB_GUI()
    window.show()
    sys.exit(app.exec_())

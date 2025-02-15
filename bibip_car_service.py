import json
from typing import List, Dict
from pathlib import Path
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale
from decimal import Decimal
from datetime import datetime

class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = Path(root_directory_path)
        self.cars_file = self.root_directory_path / "cars.txt"
        self.cars_index_file = self.root_directory_path / "cars_index.txt"
        self.models_file = self.root_directory_path / "models.txt"
        self.models_index_file = self.root_directory_path / "models_index.txt"

        # Инициализация файлов, если они не существуют
        for file in [self.cars_file, self.cars_index_file, self.models_file, self.models_index_file]:
            file.touch(exist_ok=True)

    def _read_index(self, index_file: Path) -> List[Dict]:
        if not index_file.exists():
            return []
        with open(index_file, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f.readlines()]

    def _write_index(self, index_file: Path, index_data: List[Dict]) -> None:
        with open(index_file, "w", encoding="utf-8") as f:
            for entry in index_data:
                f.write(json.dumps(entry) + "\n")

    def _add_to_file(self, data_file: Path, index_file: Path, data: Dict, key: str) -> None:
        index_data = self._read_index(index_file)
        data_str = json.dumps(data, default=str)  # Преобразование всех объектов в строки
        with open(data_file, "a", encoding="utf-8") as f:
            f.write(data_str.ljust(500) + "\n")
        index_data.append({key: len(index_data)})
        self._write_index(index_file, index_data)

    def add_model(self, model: Model) -> Model:
        # Преобразуем модель в словарь
        model_data = model.dict()

        # Открываем файл models.txt для добавления данных
        with open(self.models_file, "a", encoding="utf-8") as f:
            # Записываем данные модели в формате JSON, дополняя строку до 500 символов
            f.write(json.dumps(model_data, default=str).ljust(500) + "\n")

        # Читаем текущий индекс
        index_data = self._read_index(self.models_index_file)

        # Добавляем новую запись в индекс
        index_data.append({"id": str(model.id), "position": len(index_data)})

        # Записываем обновленный индекс в файл
        self._write_index(self.models_index_file, index_data)

        return model

    def add_car(self, car: Car) -> Car:
        # Преобразуем объект Car в словарь
        car_data = car.dict()

        # Добавляем данные автомобиля в файл cars.txt
        with open(self.cars_file, "a", encoding="utf-8") as f:
            # Записываем JSON-представление данных автомобиля, дополняя строку до 500 символов
            f.write(json.dumps(car_data, default=str).ljust(500) + "\n")

        # Читаем текущие данные индекса из файла индекса
        index_data = self._read_index(self.cars_index_file)

        # Добавляем новую запись в индекс для этого автомобиля
        index_entry = {"vin": car.vin, "position": len(index_data)}
        index_data.append(index_entry)

        # Записываем обновленный индекс обратно в файл индекса
        self._write_index(self.cars_index_file, index_data)

        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        raise NotImplementedError

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        raise NotImplementedError

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        raise NotImplementedError

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        raise NotImplemented
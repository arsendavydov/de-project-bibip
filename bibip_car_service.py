import os
from datetime import datetime
from decimal import Decimal
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale

class CarService:
    def __init__(self, root_directory_path: str) -> None:
        """
        Инициализирует CarService с указанным корневым путем.
        Создает необходимые файлы, если они не существуют.
        """
        self.root_directory_path = root_directory_path
        self.files = {
            "cars": "cars.txt",
            "cars_index": "cars_index.txt",
            "models": "models.txt",
            "models_index": "models_index.txt",
            "sales": "sales.txt",
            "sales_index": "sales_index.txt"
        }

        # Создаем файлы, если они не существуют
        for file in self.files.values():
            open(os.path.join(root_directory_path, file), "a").close()

    def add_model(self, model: Model) -> Model:
        """
        Добавляет модель автомобиля в файл и обновляет индекс.
        Возвращает добавленную модель.
        """
        model_line = f"{model.id};{model.name};{model.brand}".ljust(500) + "\n"
        self._write_line("models", model_line)

        index_line = f"{model.id};{self._get_last_line_number('models')}".ljust(500) + "\n"
        self._write_line("models_index", index_line)

        return model

    def add_car(self, car: Car) -> Car:
        """
        Добавляет автомобиль в файл и обновляет индекс.
        Возвращает добавленный автомобиль.
        """
        car_line = (f"{car.vin};{car.model};{car.price};"
                    f"{car.date_start.strftime('%Y-%m-%d')};{car.status}").ljust(500) + "\n"
        self._write_line("cars", car_line)

        index_line = f"{car.vin};{self._get_last_line_number('cars')}".ljust(500) + "\n"
        self._write_line("cars_index", index_line)

        return car

    def sell_car(self, sale: Sale) -> Car:
        """
        Продает автомобиль, обновляет файл продаж и индекс.
        Возвращает обновленный объект Car.
        """
        sale_line = (f"{sale.sales_number};{sale.car_vin};{sale.cost};"
                     f"{sale.sales_date.strftime('%Y-%m-%d')}").ljust(500) + "\n"
        self._write_line("sales", sale_line)

        index_line = f"{sale.sales_number};{self._get_last_line_number('sales')}".ljust(500) + "\n"
        self._write_line("sales_index", index_line)

        car_position = self._get_car_position(sale.car_vin)
        if car_position is None:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} не найден.")

        car_data = self._read_car_data(car_position)
        car_data[-1] = CarStatus.sold.value  # type: ignore
        updated_car_line = ";".join(car_data).ljust(500) + "\n"
        self._update_line("cars", car_position, updated_car_line)

        return Car(
            vin=car_data[0],
            model=int(car_data[1]),
            price=Decimal(car_data[2]),
            date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
            status=CarStatus(car_data[4]),
        )

    def get_cars(self, status: CarStatus) -> list[Car]:
        """
        Возвращает список автомобилей с указанным статусом.
        """
        cars = []
        with open(self._get_file_path("cars"), "r") as f:
            for line in f:
                car_data = line.strip().split(";")
                if len(car_data) == 5 and CarStatus(car_data[4]) == status:
                    cars.append(Car(
                        vin=car_data[0],
                        model=int(car_data[1]),
                        price=Decimal(car_data[2]),
                        date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
                        status=CarStatus(car_data[4]),
                    ))
        return cars

    def get_car_info(self, vin: str) -> CarFullInfo | None:
        """
        Возвращает полную информацию об автомобиле по его VIN.
        """
        car_position = self._get_car_position(vin)
        if car_position is None:
            return None

        car_data = self._read_car_data(car_position)
        car = Car(
            vin=car_data[0],
            model=int(car_data[1]),
            price=Decimal(car_data[2]),
            date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
            status=CarStatus(car_data[4]),
        )

        model = self._get_model_by_id(car.model)
        if model is None:
            return None

        sales_date, sales_cost = self._get_sales_info(vin)

        return CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sales_date,
            sales_cost=sales_cost,
        )

    def update_vin(self, vin: str, new_vin: str) -> Car:
        """
        Обновляет VIN автомобиля и перестраивает индекс.
        Возвращает обновленный объект Car.
        """
        car_position = self._get_car_position(vin)
        if car_position is None:
            raise ValueError(f"Автомобиль с VIN {vin} не найден.")

        car_data = self._read_car_data(car_position)
        car_data[0] = new_vin
        updated_car_line = ";".join(car_data).ljust(500) + "\n"
        self._update_line("cars", car_position, updated_car_line)

        self._update_index("cars_index", vin, new_vin)

        return Car(
            vin=new_vin,
            model=int(car_data[1]),
            price=Decimal(car_data[2]),
            date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
            status=CarStatus(car_data[4]),
        )

    def revert_sale(self, sales_number: str) -> Car:
        """
        Отменяет продажу, добавляя флаг is_deleted и возвращая автомобиль
        в статус "available". Возвращает обновленный объект Car.
        """
        sales_data = self._read_sales_data()
        sale_found = False
        car_vin = None

        for i, sale in enumerate(sales_data):
            if sale[0] == sales_number:
                sale_found = True
                car_vin = sale[1]
                if len(sale) < 5:
                    sales_data[i].append("is_deleted")
                break

        if not sale_found:
            raise ValueError(f"Продажа с номером {sales_number} не найдена.")

        self._write_sales_data(sales_data)

        if car_vin:
            car_position = self._get_car_position(car_vin)
            if car_position is None:
                raise ValueError(f"Автомобиль с VIN {car_vin} не найден.")

            car_data = self._read_car_data(car_position)
            car_data[-1] = CarStatus.available.value  # type: ignore
            updated_car_line = ";".join(car_data).ljust(500) + "\n"
            self._update_line("cars", car_position, updated_car_line)

            return Car(
                vin=car_data[0],
                model=int(car_data[1]),
                price=Decimal(car_data[2]),
                date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
                status=CarStatus(car_data[4]),
            )
        else:
            raise ValueError("Не удалось определить VIN автомобиля для отмены продажи.")

    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """
        Возвращает топ-3 модели по количеству продаж.
        Если количество продаж одинаковое, сортирует по средней цене (по убыванию).
        """
        sales_data_by_model = {}

        with open(self._get_file_path("sales"), "r") as f:
            for line in f:
                sale_data = line.strip().split(";")
                if len(sale_data) < 4 or (len(sale_data) >= 5 and sale_data[4] == "is_deleted"):
                    continue

                car_vin = sale_data[1]
                car_position = self._get_car_position(car_vin)
                if car_position is None:
                    continue

                car_data = self._read_car_data(car_position)
                if len(car_data) < 3:
                    continue

                model_id = int(car_data[1])
                price = Decimal(car_data[2])

                if model_id in sales_data_by_model:
                    sales_data_by_model[model_id]["sales_count"] += 1
                    sales_data_by_model[model_id]["total_price"] += price
                else:
                    sales_data_by_model[model_id] = {
                        "sales_count": 1,
                        "total_price": price,
                    }

        if not sales_data_by_model:
            return []

        sorted_models = sorted(
            sales_data_by_model.items(),
            key=lambda x: (-x[1]["sales_count"], -(x[1]["total_price"] / x[1]["sales_count"]))
        )

        top_3_models = sorted_models[:3]
        result = []

        for model_id, data in top_3_models:
            model = self._get_model_by_id(model_id)
            if model:
                result.append(ModelSaleStats(
                    car_model_name=model.name,
                    brand=model.brand,
                    sales_number=data["sales_count"],
                ))

        return result

    # Вспомогательные методы

    def _get_file_path(self, file_key: str) -> str:
        """
        Возвращает полный путь для файла по ключу.
        """
        return os.path.join(self.root_directory_path, self.files[file_key])

    def _get_last_line_number(self, file_key: str) -> int:
        """
        Возвращает номер последней строки в файле.
        """
        file_path = self._get_file_path(file_key)
        if os.path.getsize(file_path) == 0:
            return 0
        with open(file_path, "r") as f:
            return sum(1 for _ in f) - 1

    def _read_index(self, file_key: str) -> list:
        """
        Читает индексный файл и возвращает его содержимое в виде списка.
        """
        index_file = self._get_file_path(file_key)
        if not os.path.exists(index_file):
            return []
        with open(index_file, "r") as f:
            return [{"vin": parts[0], "position": int(parts[1])}
                    for line in f if (parts := line.strip().split(";")) and len(parts) == 2]

    def _write_line(self, file_key: str, line: str):
        """
        Записывает строку в указанный файл.
        """
        with open(self._get_file_path(file_key), "a") as f:
            f.write(line)

    def _update_line(self, file_key: str, position: int, line: str):
        """
        Обновляет конкретную строку в файле.
        """
        file_path = self._get_file_path(file_key)
        with open(file_path, "r+") as f:
            f.seek(position * 501)
            f.write(line)

    def _get_car_position(self, vin: str) -> int | None:
        """
        Возвращает позицию автомобиля в файле по его VIN.
        """
        cars_index_data = self._read_index("cars_index")
        for entry in cars_index_data:
            if entry["vin"] == vin:
                return entry["position"]
        return None

    def _read_car_data(self, position: int) -> list[str]:
        """
        Читает данные автомобиля из файла по указанной позиции.
        """
        with open(self._get_file_path("cars"), "r") as f:
            f.seek(position * 501)
            return f.read(500).strip().split(";")

    def _get_model_by_id(self, model_id: int) -> Model | None:
        """
        Возвращает модель по её ID.
        """
        models_index_data = self._read_index("models_index")
        for entry in models_index_data:
            if entry["vin"] == str(model_id):
                model_position = entry["position"]
                with open(self._get_file_path("models"), "r") as f:
                    f.seek(model_position * 501)
                    model_data = f.read(500).strip().split(";")
                    if len(model_data) == 3:
                        return Model(
                            id=int(model_data[0]),
                            name=model_data[1],
                            brand=model_data[2],
                        )
        return None

    def _get_sales_info(self, vin: str) -> tuple[datetime | None, Decimal | None]:
        """
        Возвращает дату и стоимость продажи автомобиля по его VIN.
        """
        with open(self._get_file_path("sales"), "r") as f:
            for line in f:
                sale_data = line.strip().split(";")
                if sale_data[1] == vin:
                    return (
                        datetime.strptime(sale_data[3], "%Y-%m-%d"),
                        Decimal(sale_data[2])
                    )
        return None, None

    def _read_sales_data(self) -> list[list[str]]:
        """
        Читает все данные о продажах из файла.
        """
        with open(self._get_file_path("sales"), "r") as f:
            return [line.strip().split(";") for line in f if line.strip()]

    def _write_sales_data(self, sales_data: list[list[str]]):
        """
        Записывает все данные о продажах в файл.
        """
        with open(self._get_file_path("sales"), "w") as f:
            for sale in sales_data:
                f.write(";".join(sale).ljust(500) + "\n")

    def _update_index(self, file_key: str, old_vin: str, new_vin: str):
        """
        Обновляет индексный файл с новым VIN.
        """
        index_data = self._read_index(file_key)
        updated_index_data = [
            {"vin": new_vin, "position": entry["position"]}
            if entry["vin"] == old_vin else entry
            for entry in index_data
        ]
        updated_index_data.sort(key=lambda x: x["vin"])

        with open(self._get_file_path(file_key), "w") as f:
            for entry in updated_index_data:
                f.write(f"{entry['vin']};{entry['position']}".ljust(500) + "\n")

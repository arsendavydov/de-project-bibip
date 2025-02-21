import os
from datetime import datetime
from decimal import Decimal
from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        """
        Инициализировать CarService с указанным корневым путем.
        Создать необходимые файлы, если они не существуют.
        """
        self.root_directory_path = root_directory_path
        self.cars_file = os.path.join(
            root_directory_path,
            "cars.txt"
        )
        self.cars_index_file = os.path.join(
            root_directory_path,
            "cars_index.txt"
        )
        self.models_file = os.path.join(
            root_directory_path,
            "models.txt"
        )
        self.models_index_file = os.path.join(
            root_directory_path,
            "models_index.txt"
        )
        self.sales_file = os.path.join(
            root_directory_path,
            "sales.txt"
        )
        self.sales_index_file = os.path.join(
            root_directory_path,
            "sales_index.txt"
        )

        # Создать файлы, если они не существуют
        open(self.cars_file, "a").close()
        open(self.cars_index_file, "a").close()
        open(self.models_file, "a").close()
        open(self.models_index_file, "a").close()
        open(self.sales_file, "a").close()
        open(self.sales_index_file, "a").close()

    def add_model(self, model: Model) -> Model:
        """
        Добавить модель автомобиля в файл и обновить индекс.
        Вернуть добавленную модель.
        """
        # Сформировать строку для записи модели в файл
        model_line = (
            f"{model.id};{model.name};{model.brand}".ljust(500) + "\n"
        )
        # Записать модель в файл
        with open(self.models_file, "a") as f:
            f.write(model_line)

        # Сформировать строку для записи в индексный файл
        index_line = (
            f"{model.id};"
            f"{self._get_last_line_number(self.models_file)}".ljust(500)
            + "\n"
        )
        # Записать индекс в индексный файл
        with open(self.models_index_file, "a") as f:
            f.write(index_line)

        return model

    def add_car(self, car: Car) -> Car:
        """
        Добавить автомобиль в файл и обновить индекс.
        Вернуть добавленный автомобиль.
        """
        # Отформатировать дату начала эксплуатации
        formatted_date = car.date_start.strftime("%Y-%m-%d")
        # Сформировать строку для записи автомобиля в файл
        car_line = (
            f"{car.vin};{car.model};{car.price};"
            f"{formatted_date};{car.status}".ljust(500) + "\n"
        )
        # Записать автомобиль в файл
        with open(self.cars_file, "a") as f:
            f.write(car_line)

        # Сформировать строку для записи в индексный файл
        index_line = (
            f"{car.vin};"
            f"{self._get_last_line_number(self.cars_file)}".ljust(500) + "\n"
        )
        # Записать индекс в индексный файл
        with open(self.cars_index_file, "a") as f:
            f.write(index_line)

        return car

    def sell_car(self, sale: Sale) -> Car:
        """
        Продать автомобиль, обновить файл продаж и индекс.
        Вернуть обновленный объект Car.
        """
        # Отформатировать дату продажи
        formatted_sales_date = sale.sales_date.strftime("%Y-%m-%d")
        # Сформировать строку для записи продажи в файл
        sale_line = (
            f"{sale.sales_number};{sale.car_vin};{sale.cost};"
            f"{formatted_sales_date}".ljust(500) + "\n"
        )
        # Записать продажу в файл
        with open(self.sales_file, "a") as f:
            f.write(sale_line)

        # Сформировать строку для записи в индексный файл
        index_line = (
            f"{sale.sales_number};"
            f"{self._get_last_line_number(self.sales_file)}".ljust(500) + "\n"
        )
        # Записать индекс в индексный файл
        with open(self.sales_index_file, "a") as f:
            f.write(index_line)

        # Найти позицию автомобиля в файле по его VIN
        cars_index_data = self._read_index(self.cars_index_file)
        car_position = None

        for entry in cars_index_data:
            if entry.get("vin") == sale.car_vin:
                car_position = entry.get("position")
                break

        if car_position is None:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} не найден.")

        # Обновить статус автомобиля на "продан"
        with open(self.cars_file, "r+") as f:
            f.seek(car_position * 501)
            car_data_str = f.read(500).strip()
            car_data = car_data_str.split(";")
            car_data[-1] = CarStatus.sold.value  # type: ignore
            updated_car_line = ";".join(car_data).ljust(500) + "\n"
            f.seek(car_position * 501)
            f.write(updated_car_line)

        # Вернуть обновленный объект Car
        updated_car = Car(
            vin=car_data[0],
            model=int(car_data[1]),
            price=Decimal(car_data[2]),
            date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
            status=CarStatus(car_data[4]),
        )
        return updated_car

    def get_cars(self, status: CarStatus) -> list[Car]:
        """
        Вернуть список автомобилей с указанным статусом.
        """
        cars = []
        with open(self.cars_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                car_data = line.split(";")
                if len(car_data) != 5:
                    continue
                if CarStatus(car_data[4]) == status:
                    car = Car(
                        vin=car_data[0],
                        model=int(car_data[1]),
                        price=Decimal(car_data[2]),
                        date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
                        status=CarStatus(car_data[4]),
                    )
                    cars.append(car)
        return cars

    def get_car_info(self, vin: str) -> CarFullInfo | None:  # type: ignore
        """
        Вернуть полную информацию об автомобиле по его VIN.
        """
        # Найти позицию автомобиля в файле по его VIN
        cars_index_data = self._read_index(self.cars_index_file)
        car_position = None

        for entry in cars_index_data:
            if entry.get("vin") == vin:
                car_position = entry.get("position")
                break

        if car_position is None:
            return None

        # Прочитать данные автомобиля
        with open(self.cars_file, "r") as f:
            f.seek(car_position * 501)
            car_data_str = f.read(500).strip()
            car_data = car_data_str.split(";")
            car = Car(
                vin=car_data[0],
                model=int(car_data[1]),
                price=Decimal(car_data[2]),
                date_start=datetime.strptime(car_data[3], "%Y-%m-%d"),
                status=CarStatus(car_data[4]),
            )

        # Найти позицию модели в файле
        models_index_data = self._read_index(self.models_index_file)
        model_position = None

        for entry in models_index_data:
            if entry.get("vin") == str(car.model):
                model_position = entry.get("position")
                break

        if model_position is None:
            return None

        # Прочитать данные модели
        with open(self.models_file, "r") as f:
            f.seek(model_position * 501)
            model_data_str = f.read(500).strip()
            model_data = model_data_str.split(";")
            model = Model(
                id=int(model_data[0]),
                name=model_data[1],
                brand=model_data[2],
            )

        # Получить данные о продаже, если автомобиль продан
        sales_date = None
        sales_cost = None

        if car.status == CarStatus.sold:
            with open(self.sales_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    sale_data = line.split(";")
                    if sale_data[1] == vin:
                        sales_date = datetime.strptime(
                            sale_data[3],
                            "%Y-%m-%d"
                            )
                        sales_cost = Decimal(sale_data[2])
                        break

        # Вернуть полную информацию об автомобиле
        car_full_info = CarFullInfo(
            vin=car.vin,
            car_model_name=model.name,
            car_model_brand=model.brand,
            price=car.price,
            date_start=car.date_start,
            status=car.status,
            sales_date=sales_date,
            sales_cost=sales_cost,
        )

        return car_full_info

    def update_vin(self, vin: str, new_vin: str) -> Car:
        """
        Обновить VIN-код автомобиля и перестроить индекс.
        Вернуть обновленный объект Car.
        """
        # Найти позицию автомобиля в файле по его VIN
        cars_index_data = self._read_index(self.cars_index_file)
        car_position = None

        for entry in cars_index_data:
            if entry.get("vin") == vin:
                car_position = entry.get("position")
                break

        if car_position is None:
            raise ValueError(f"Автомобиль с VIN {vin} не найден.")

        # Обновить VIN в файле автомобилей
        with open(self.cars_file, "r+") as f:
            f.seek(car_position * 501)
            car_data_str = f.read(500).strip()
            car_data = car_data_str.split(";")
            car_data[0] = new_vin
            updated_car_line = ";".join(car_data).ljust(500) + "\n"
            f.seek(car_position * 501)
            f.write(updated_car_line)

        # Обновить индексный файл
        updated_index_data = []
        for entry in cars_index_data:
            if entry.get("vin") == vin:
                updated_index_data.append(
                    {"vin": new_vin, "position": entry.get("position")}
                )
            else:
                updated_index_data.append(entry)

        updated_index_data.sort(key=lambda x: x["vin"])

        with open(self.cars_index_file, "w") as f:
            for entry in updated_index_data:
                index_line = (
                    f"{entry['vin']};"
                    f"{entry['position']}".ljust(500) + "\n"
                )
                f.write(index_line)

        # Вернуть обновленный объект Car
        updated_car = Car(
            vin=new_vin,
            model=int(car_data[1]),
            price=Decimal(car_data[2]),
            date_start=datetime.fromisoformat(car_data[3]),
            status=CarStatus(car_data[4]),
        )
        return updated_car

    def revert_sale(self, sales_number: str) -> Car:
        """
        Отменить продажу, добавив флаг is_deleted и вернув автомобиль
        в статус "available". Вернуть обновленный объект Car.
        """
        # Прочитать данные о продажах
        sales_data = []
        with open(self.sales_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                sale_data = line.split(";")
                sales_data.append(sale_data)

        # Найти продажу по номеру и добавить флаг is_deleted
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

        # Записать обновленные данные о продажах
        with open(self.sales_file, "w") as f:
            for sale in sales_data:
                sale_line = ";".join(sale).ljust(500) + "\n"
                f.write(sale_line)

        if car_vin:
            # Найти позицию автомобиля в файле по его VIN
            cars_index_data = self._read_index(self.cars_index_file)
            car_position = None

            for entry in cars_index_data:
                if entry.get("vin") == car_vin:
                    car_position = entry.get("position")
                    break

            if car_position is None:
                raise ValueError(f"Автомобиль с VIN {car_vin} не найден.")

            # Обновить статус автомобиля на "available"
            with open(self.cars_file, "r+") as f:
                f.seek(car_position * 501)
                car_data_str = f.read(500).strip()
                car_data = car_data_str.split(";")
                car_data[-1] = CarStatus.available.value   # type: ignore
                updated_car_line = ";".join(car_data).ljust(500) + "\n"
                f.seek(car_position * 501)
                f.write(updated_car_line)

            # Вернуть обновленный объект Car
            updated_car = Car(
                vin=car_data[0],
                model=int(car_data[1]),
                price=Decimal(car_data[2]),
                date_start=datetime.fromisoformat(car_data[3]),
                status=CarStatus(car_data[4]),
            )
            return updated_car
        else:
            raise ValueError(
                "Не удалось определить VIN автомобиля для отмены продажи."
                )

    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """
        Вернуть топ-3 модели по количеству продаж.
        Если количество продаж одинаковое, отсортировать
        по средней цене (по убыванию).
        """
        # Собрать данные о продажах по моделям
        sales_data_by_model = {}  # type: ignore

        with open(self.sales_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                sale_data = line.split(";")
                if len(sale_data) < 4:
                    continue
                if len(sale_data) >= 5 and sale_data[4] == "is_deleted":
                    continue

                car_vin = sale_data[1]
                cars_index_data = self._read_index(self.cars_index_file)
                car_position = None
                for entry in cars_index_data:
                    if entry.get("vin") == car_vin:
                        car_position = entry.get("position")
                        break

                if car_position is None:
                    continue

                with open(self.cars_file, "r") as cars_f:
                    cars_f.seek(car_position * 501)
                    car_data_str = cars_f.read(500).strip()
                    car_data = car_data_str.split(";")

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

        # Отсортировать модели по количеству продаж и средней цене
        sorted_models = sorted(
            sales_data_by_model.items(),
            key=lambda x: (
                -x[1]["sales_count"],  # type: ignore
                -(x[1]["total_price"] / x[1]["sales_count"]),  # type: ignore
            ),
        )

        # Выбрать топ-3 модели
        top_3_models = sorted_models[:3]
        result = []

        for model_id, data in top_3_models:
            # Найти данные о модели
            models_index_data = self._read_index(self.models_index_file)
            model_position = None
            for entry in models_index_data:
                if entry.get("vin") == str(model_id):
                    model_position = entry.get("position")
                    break

            if model_position is None:
                continue

            with open(self.models_file, "r") as models_f:
                models_f.seek(model_position * 501)
                model_data_str = models_f.read(500).strip()
                model_data = model_data_str.split(";")

                if len(model_data) < 3:
                    continue

                # Сформировать объект ModelSaleStats
                model_sale_stats = ModelSaleStats(
                    car_model_name=model_data[1],
                    brand=model_data[2],
                    sales_number=data["sales_count"],
                )
                result.append(model_sale_stats)

        return result

    def _get_last_line_number(self, file_path: str) -> int:
        """
        Вернуть номер последней строки в файле.
        """
        if os.path.getsize(file_path) == 0:
            return 0
        with open(file_path, "r") as f:
            return sum(1 for _ in f) - 1

    def _read_index(self, index_file: str) -> list:
        """
        Прочитать индексный файл и вернуть его содержимое в виде списка.
        """
        if not os.path.exists(index_file):
            return []
        with open(index_file, "r") as f:
            index_data = []
            for line in f:
                parts = line.strip().split(";")
                if len(parts) == 2:
                    index_data.append({
                        "vin": parts[0],
                        "position": int(parts[1])
                        })
            return index_data
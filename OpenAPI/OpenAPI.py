import requests
import json
import os
from copy import deepcopy

# Список URL для получения OpenAPI спецификаций от каждого сервиса
services = {
    "api_gateway": "http://localhost:8000/openapi.json",
    "auth_service": "http://localhost:8001/openapi.json",
    "deal_service": "http://localhost:8002/openapi.json",
    "rating_service": "http://localhost:8003/openapi.json",
    "account_service": "http://localhost:8004/openapi.json",
}

# Базовая структура объединённой спецификации
combined_spec = {
    "openapi": "3.1.0",
    "info": {
        "title": "YAMS API",
        "description": "Объединённое API для проекта YAMS с микросервисами",
        "version": "1.0.0"
    },
    "paths": {},
    "components": {
        "schemas": {}
    }
}

# Создаем папку templates, если её нет
os.makedirs("services", exist_ok=True)


# Функция для добавления префикса к путям
def add_prefix_to_paths(paths, prefix):
    new_paths = {}
    for path, path_data in paths.items():
        new_path = f"/{prefix}{path}" if path != "/" else f"/{prefix}"
        new_paths[new_path] = path_data
    return new_paths


# Функция для обновления ссылок $ref
def update_refs(data, old_name, new_name):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "$ref" and value == f"#/components/schemas/{old_name}":
                data[key] = f"#/components/schemas/{new_name}"
            else:
                update_refs(value, old_name, new_name)
    elif isinstance(data, list):
        for item in data:
            update_refs(item, old_name, new_name)


# Функция для поиска всех $ref в словаре
def find_refs(data, refs=None):
    if refs is None:
        refs = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "$ref" and isinstance(value, str):
                refs.add(value)
            else:
                find_refs(value, refs)
    elif isinstance(data, list):
        for item in data:
            find_refs(item, refs)
    return refs


# Собираем и сохраняем спецификации
for service_name, url in services.items():
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Ошибка при получении спецификации для {service_name}: {response.status_code}")
            continue

        # Получаем исходную спецификацию
        spec = response.json()

        # Сохраняем индивидуальную спецификацию для сервиса
        individual_file = f"services/{service_name}_openapi.json"
        with open(individual_file, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
        print(f"Индивидуальная спецификация для {service_name} сохранена в {individual_file}")

        # Создаем копию для объединенной спецификации
        spec_copy = deepcopy(spec)

        # Добавляем префикс к путям для объединенной спецификации
        prefixed_paths = add_prefix_to_paths(spec_copy.get("paths", {}), service_name)

        # Объединяем схемы (components.schemas) с префиксом
        if "components" in spec_copy and "schemas" in spec_copy["components"]:
            schemas = spec_copy["components"]["schemas"]
            for schema_name, schema_data in schemas.items():
                new_schema_name = f"{service_name}_{schema_name}"
                if new_schema_name in combined_spec["components"]["schemas"]:
                    print(
                        f"Конфликт: схема {new_schema_name} уже существует. Переименуйте схему в сервисе {service_name}.")
                    continue
                # Обновляем ссылки $ref в данных схемы
                update_refs(schema_data, schema_name, new_schema_name)
                # Обновляем ссылки $ref для всех других схем
                for other_schema_name, other_schema_data in schemas.items():
                    if other_schema_name != schema_name:
                        update_refs(other_schema_data, schema_name, new_schema_name)
                combined_spec["components"]["schemas"][new_schema_name] = schema_data
                print(f"Добавлена схема: {new_schema_name} из сервиса {service_name}")

                # Обновляем ссылки $ref в путях
                update_refs(prefixed_paths, schema_name, new_schema_name)

        combined_spec["paths"].update(prefixed_paths)
        print(f"Спецификация для {service_name} успешно добавлена в объединённую спецификацию")

    except Exception as e:
        print(f"Ошибка при обработке {service_name}: {e}")

# Проверяем, все ли $ref ссылаются на существующие схемы в объединённой спецификации
all_refs = find_refs(combined_spec)
for ref in all_refs:
    schema_name = ref.split("/")[-1]
    if schema_name not in combined_spec["components"]["schemas"]:
        print(f"Ошибка: схема {schema_name} (ссылка {ref}) не найдена в components.schemas")

# Сохраняем объединённую спецификацию
with open("combined_openapi.json", "w", encoding="utf-8") as f:
    json.dump(combined_spec, f, indent=2, ensure_ascii=False)

print("Объединённая спецификация сохранена в combined_openapi.json")
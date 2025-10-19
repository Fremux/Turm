#!/bin/bash

API_BASE="http://localhost:8000/api/v1/admin"

# Get category IDs first
echo "Getting category IDs..."
CATEGORIES=$(curl -s "${API_BASE}/categories")

HR_ID=$(echo $CATEGORIES | grep -o '"id":[0-9]*,"name":"hr"' | grep -o '[0-9]*' | head -1)
IT_ID=$(echo $CATEGORIES | grep -o '"id":[0-9]*,"name":"it"' | grep -o '[0-9]*' | head -1)
FINANCE_ID=$(echo $CATEGORIES | grep -o '"id":[0-9]*,"name":"finance"' | grep -o '[0-9]*' | head -1)
OFFICE_ID=$(echo $CATEGORIES | grep -o '"id":[0-9]*,"name":"office"' | grep -o '[0-9]*' | head -1)

echo "HR ID: $HR_ID"
echo "IT ID: $IT_ID"
echo "Finance ID: $FINANCE_ID"
echo "Office ID: $OFFICE_ID"

echo -e "\nUpdating HR category..."
curl -X PATCH "${API_BASE}/categories/${HR_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "HR (Кадры)",
    "description": "Кадры, зарплата, льготы, ЛК сотрудника, обучение",
    "about_text": "трудовые отношения и персонал — оформление/изменение условий, отпуска/командировки, справки для сотрудника, ЛК, обучение/LMS, льготы/ДМС, индексация/оклад.",
    "common_intents": "согласовать/оформить/изменить; предоставить справку; открыть доступ к ЛК; записать на обучение; исправить начисление.",
    "key_markers": "«отпуск», «приказ/допсоглашение», «ЛК сотрудника», «ДМС/льготы», «2-НДФЛ/182н», «обучение/LMS», «оклад/индексация», «справка для сотрудника», «командировка», «график работы».",
    "example_queries": "оформить отпуск, справка 2-НДФЛ, доступ к ЛК сотрудника, запись на обучение, изменить график работы, льготы/ДМС.",
    "border_cases": "Справка для сотрудника (2-НДФЛ, стаж) → hr; финансовые справки по контрагентам → finance",
    "embedding_model": "qwen-4b",
    "embedding_dimension": 2048,
    "color": "#a855f7",
    "icon": "users"
  }'

echo -e "\n\nUpdating IT category..."
curl -X PATCH "${API_BASE}/categories/${IT_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "IT (Технологии)",
    "description": "Доступы, ПО, сеть, почта, DevOps, инфраструктура",
    "about_text": "учётные записи и права (AD/VPN/SSO/MFA), рабочее ПО и установка, сеть/VPN/Wi-Fi/почта, Exchange/M365, Dev/CI/CD/K8s, бэкапы, мониторинг/логи, VDI/RDP, файлы/хранилища.",
    "common_intents": "создать/восстановить доступ; выдать права/AD; установить ПО; починить сеть/VPN/почту; настроить оборудование (драйвер/принтер); восстановить из бэкапа; устранить инциденты CI/CD/K8s.",
    "key_markers": "«AD/группа/SSO/VPN/MFA», «Teams/Outlook/SharePoint», «почта не приходит», «GitLab/Jenkins/K8s/Helm», «Prometheus/Grafana/Splunk», «RDP/VDI», «принтер не печатает (драйвер/доступ)», «установить ПО», «настроить», «не работает (про ПО/сеть)».",
    "example_queries": "создать учётку AD, установить ПО, проблема с почтой, настроить VPN, восстановить доступ, проблемы с Teams/Outlook, CI/CD pipeline не работает.",
    "border_cases": "Доступ к системам/установка ПО/почта → it; отпуск/ЛК сотрудника → hr. Принтер не печатает (драйвер/права) → it; переставить принтер → office. Outlook не синхронизирует календарь → it; забронировать переговорную → office.",
    "embedding_model": "qwen-4b",
    "embedding_dimension": 2048,
    "color": "#3b82f6",
    "icon": "cpu"
  }'

echo -e "\n\nUpdating Finance category..."
curl -X PATCH "${API_BASE}/categories/${FINANCE_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Finance (Финансы)",
    "description": "Бухгалтерия, налоги, платежи, ЭДО",
    "about_text": "бухучёт/ЗУП (в части бухгалтерии), налоги (НДС, 6-НДФЛ, книга покупок/продаж), отчётность/декларации, платежи/реестры/банки, ЭДО/ЭП, ERP (1С/SAP/Oracle EBS).",
    "common_intents": "проверить/исправить алгоритм (проводки/начисления); сформировать/выгрузить отчёт/декларацию; настроить налоговые коды/толеранс; оформить платёж/реестр; выдать справки (фин.); настроить ЭП/ЭДО.",
    "key_markers": "«проводки/сверка/реестр», «НДС/6-НДФЛ/книга покупок», «выгрузка отчёта/декларации», «платёж/банк-клиент», «ЭП/Крипто-провайдер», «Диадок/СБИС/Контур», «1С/SAP/Oracle», «бухгалтерия», «налог».",
    "example_queries": "проверить проводки, сформировать декларацию, оформить платёж, настроить ЭДО, выгрузка отчёта, книга покупок/продаж.",
    "border_cases": "Проблемы входа в банк-клиент (ПО/токен) → it; операция платежа → finance",
    "embedding_model": "bge-m3",
    "embedding_dimension": 1024,
    "color": "#10b981",
    "icon": "dollar-sign"
  }'

echo -e "\n\nUpdating Office category..."
curl -X PATCH "${API_BASE}/categories/${OFFICE_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Office (Офис)",
    "description": "Пропуска, парковка, переговорные, рабочие места",
    "about_text": "физический офис и сервисы — пропуска/парковка/турникеты, переговорные (бронирование/настройка AV), организация/перенос рабочих мест, ремонт/замена офисного оборудования, гостевой Wi-Fi, телефония, ресепшен.",
    "common_intents": "пропуск оформить/заменить/продлить; парковку добавить/продлить; доступ к турникетам/этажам; переговорные забронировать/настроить; организовать/перенести рабочее место; ремонт/замена офисного оборудования; гостевые сервисы; телефония.",
    "key_markers": "«пропуск/парковка/турникет», «переговорная/проектор/AV», «перенос рабочего места/монтаж», «ресепшен/очередь», «гостевой Wi-Fi», «внутренняя телефония/ATS», «забронировать», «организовать место».",
    "example_queries": "оформить пропуск, продлить парковку, забронировать переговорную, перенести рабочее место, гостевой Wi-Fi, настроить проектор, телефония.",
    "embedding_model": "qwen-0.6b",
    "embedding_dimension": 768,
    "color": "#f59e0b",
    "icon": "building"
  }'

echo -e "\n\nDone! All categories updated with full prompt data."


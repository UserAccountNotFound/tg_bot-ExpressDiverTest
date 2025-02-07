# Telegram Bot - ExpressDiverTest

![Python Version](https://img.shields.io/badge/python-3.11.2-blue.svg)

Попытка реализации единой точки входа в программы тестирования по курсам OWD и AOWD с последующей возможностью просмотра исторических данных, а также попытка шаблонизировать вывод результатов тестирования

## Запуск

* клонируем нужную ветку и переходим в нее
``` bash
git clone --single-branch -b main t https://github.com/UserAccountNotFound/tg_bot-diver-test.git /opt/tg_bot && cd /opt/tg_bot
```

* создаем виртуальное окружение
``` bash
python3 -m venv .venv
```

* переходим в него
``` bash
source .venv/bin/activate
```

* устанавливаем требуемые зависимости
``` bash
pip install -r requirements.txt
```

* Создаем бота с помощью @BotFather и получаем его токен

* создаем .env файл и копируем в него токен и ID группы доступа
``` bash
echo "TELEGRAM_BOT_TOKEN=*токен_телеграм_бота*" > .env
```
* GROUP_ID всегда отрицательное число!!!!!!
``` bash
echo "GROUP_ID=*ID_группы_пользователей*" > .env
```


``` bash
python3 ./bot.py
```

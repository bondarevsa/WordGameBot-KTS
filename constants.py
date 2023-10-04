import json

start_keyboard = json.dumps({
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "Правила",
                            "payload": json.dumps({"button": "1"})
                        },
                        "color": "secondary"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "Начать игру",
                            "payload": json.dumps({"button": "2"})
                        },
                        "color": "positive"
                    }
                ]
            ]
        })

collect_players_keyboard = json.dumps({
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "Буду играть!",
                            "payload": json.dumps({"button": "3"})
                        },
                        "color": "positive"
                    }
                ]
            ]
        })

voting_keyboard = json.dumps({
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "Да",
                            "payload": json.dumps({"button": "4"})
                        },
                        "color": "positive"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "Нет",
                            "payload": json.dumps({"button": "5"})
                        },
                        "color": "negative"
                    }
                ]
            ]
        })

init_words = ['Корова', 'Собака', 'Дом', 'Арбуз', 'Персик', 'Ананас', 'Квартира', 'Компьютер', 'Змея', 'Иголка',
              'Валюта', 'Телефон', 'Лекарство', 'Окно', 'Гора', 'Парфюм', 'Провод', 'Фен', 'Микрофон', 'Швея',
              'Инструкция', 'Бот', 'Телевизор', 'Грамота', 'Язык', 'Печать', 'Сухарь', 'Креветка', 'Жираф']

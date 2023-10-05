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
init_words2 = []

RULES = '''Правила игры: игроки по очереди называют слово, начинающееся на последнюю букву слова предыдущего 
            игрока (если оно было правильное). Далее проводится голосование между игроками: существует ли названное 
            слово. Если да, игрок получает балл и игра продолжается, в противном случае игрок выбывает. На ход даётся 30 
            секунд. Если слово заканчивается на буквы "ь", "ъ", "ы", то нужно назвать слово на букву, идущую до них. 
            Игра продолжается, пока не останется один игрок. Первое слово пишу я.'''
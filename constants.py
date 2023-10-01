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

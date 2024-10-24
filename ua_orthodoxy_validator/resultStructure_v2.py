result_v2 = [
    {
        'type' : 'container',
        'item_name' : "Загальні помилки",
        'subitems' : [
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка наявності обов’язкових шарів",
                'item_name' : "Відсутній шар 'Імя шару', що вимагається структурою",
                'criticity' : 1,
                'help_url' : "https://e-construction.gov.ua/laws_detail/3260441209981634046?doc_type=2"
            },
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка наявності обов’язкових шарів",
                'item_name' : "Відсутній шар 'Імя шару 2', що вимагається структурою",
                'criticity' : 1,
                'help_url' : "https://e-construction.gov.ua/laws_detail/3260441209981634046?doc_type=2"
            },
            { #а можна отак, тоді вони просто як підпункти виведуться, але це тіки при умові, шо нас влаштовує, що меню правої кнопки буде вести на один і той самий URL
                'type' : 'inspection',
                'inspection_category' : 'general',
                'inspetcion_type_name' : "Перевірка наявності обов’язкових шарів",
                'item_name' : [
                    "Відсутній шар 'Імя шару 1', що вимагається структурою",
                    "Відсутній шар 'Імя шару 2', що вимагається структурою",
                    "Відсутній шар 'Імя шару 3', що вимагається структурою",
                    "Відсутній шар 'Імя шару 4', що вимагається структурою"
                ],
                'criticity' : 1,
                'help_url' : "https://e-construction.gov.ua/laws_detail/3260441209981634046?doc_type=2"
            }
        ]
    },
    {
        'type' : 'file',
        'item_name' : "Файл 'блаблабла'",
        'related_file_path' : r"C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\Для тестування\EDRA від Богдана\buildings.geojson",
        'subitems' : [
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка формату геоданих",
                'item_name' : "Формат файлу 'GeoJson' відповідає структурі",
                'criticity' : 0
            },
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка на наявність даних",
                'item_name' : "У файлі 'Імя файлу' відсутні дані",
                'criticity' : 1,
                'help_url' : "https://genius.com/Nirvana-smells-like-teen-spirit-lyrics"
            },

        ]
    },
    {
        'type' : 'file',
        'item_name' : "Файл 'Імя файлу'",
        'related_file_path' : r"C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\Для тестування\EDRA від Богдана\streets.geojson",
        'subitems' : [                
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка формату геоданих",
                'item_name' : "Формат файлу 'GDB' не відповідає вимогам, вимагається 'GEOJSON' або 'SHP'",
                'criticity' : 1,
                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
            },
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка кодування файлу",
                'item_name' : "Кодування файлу 'WINDOWS-1251' не відповідає вимогам, вимагається 'UTF-8'",
                'criticity' : 1,
                'help_url' : "https://genius.com/Nirvana-rape-me-lyrics"
            },
            {
                'type' : 'inspection',
                'inspetcion_type_name' : "Перевірка на наявність даних",
                'item_name' : "У файлі 'Імя файлу' наявні дані",
                'criticity' : 0
            },
            {
                'type' : 'layer',
                'item_name' : "Шар 'Імя шару'",
                'real_layer_name' : "steets",
                'visible_layer_name' : "АТАТАТА",
                'related_layer_id' : 'dpt_area_002dcb97_0478_48d5_9667_367208a83219', #layer.id()
                'subitems' : [
                    {
                        'type' : 'inspection',
                        'inspetcion_type_name' : "Перевірка на тип геометрії",
                        'item_name' : "Тип геометрії шару 'Point' не відповідає структурі, вимагається 'LineString'",
                        'criticity' : 1,
                        'help_url' : "https://genius.com/Rammstein-du-hast-lyrics"
                    },
                    {
                        'type' : 'inspection',
                        'inspetcion_type_name' : "Перевірка на систему координат шару",
                        'item_tooltip' : "А шо тии думав, шо тут буде підказка?",
                        'item_name' : "Система координат шару 'EPSG:9999' не відповідає структурі, вимагається 'EPSG:4326'",
                        'criticity' : 1,
                        'help_url' : "https://genius.com/Nirvana-rape-me-lyrics"
                    },
                    {
                        'type' : 'inspection',
                        'inspetcion_type_name' : "Перевірка на відсутність полів",
                        'item_name' : "В шарі відсутнє поле атрибуту 'Імя поля', що вимагається по структурі",
                        'criticity' : 1,
                        'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                    },
                    {
                        'type' : 'inspection',
                        'inspetcion_type_name' : "Перевірка на відсутність полів",
                        'item_name' : "В шарі відсутнє поле атрибуту 'Імя 2 поля', що вимагається по структурі",
                        'criticity' : 1,
                        'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                    },
                    {
                        'type' : 'feature',
                        'item_name' : "Об'єкт 'id об'єкту'",
                        'related_feature_id' : '1',
                        'subitems' : [
                            {
                                'type' : 'container',
                                'item_name' : "Помилки атрибутів",
                                'subitems' : [
                                    {
                                        'type' : 'inspection',
                                        'inspetcion_type_name' : "Перевірка наявності атрибутів",
                                        'item_name' : "В об'єкті не заповнений атрибут 'number', що вимагається по структурі",
                                        'criticity' : 1,
                                        'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                                    },
                                    {
                                        'type' : 'inspection',
                                        'inspetcion_type_name' : "Перевірка наявності атрибутів",
                                        'item_name' : "В об'єкті не заповнений атрибут 'street', що вимагається по структурі",
                                        'criticity' : 1,
                                        'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                                    },
                                    {
                                        'type' : 'inspection',
                                        'inspetcion_type_name' : "Перевірка наявності атрибутів",
                                        'item_name' : "В об'єкті не заповнений атрибут 'street', що вимагається по структурі",
                                        'criticity' : 1,
                                        'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                                    }
                                ]
                            },                            
                            {
                                'type' : 'inspection',
                                'inspetcion_type_name' : "Перевірка типу геометрії об’єкта",
                                'item_name' :  "Тип геометрії об'єкту 'Point' не відповідає структурі, вимагається 'LineString'",
                                'criticity' : 1,
                                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                            },
                            {
                                'type' : 'inspection',
                                'inspetcion_type_name' : "Перевірка на наявність об’єктів в шарі",
                                'item_name' :  "В шарі відсутні об’єкти, що вимагається по структурі",
                                'criticity' : 1,
                                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                            },
                            {
                                'type' : 'inspection',
                                'inspetcion_type_name' : "Перевірка дублювання GUID (унікального атрибуту)",
                                'item_name' :  "GUID не унікальний в межах шарів що валідуються",
                                'corresponding_objects' : [
                                    {
                                        'corrsesponding_layer_id' : 'dpt_area_002dcb97_0478_48d5_9667_367208a83219',
                                        'corrsesponding_feature_id' : '1',
                                        'related_object_visible_name' : 'Імя об’єкту'
                                    }
                                ],
                                'criticity' : 1,
                                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                            },
                            {
                                'type' : 'inspection',
                                'inspetcion_type_name' : "Перевірка чи значення атрибуту є в переліку доменів",
                                'item_name' :  "Значення атрибуту 'Імя' не відповідає класифікатору, що вимагається по структурі",
                                'criticity' : 1,
                                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                            },
                            {
                                'type' : 'inspection',
                                'inspetcion_type_name' : "Перевірка чи значення атрибуту є в переліку доменів",
                                'item_name' :  "Значення атрибуту 'Імя' не відповідає класифікатору, що вимагається по структурі",
                                'criticity' : 1,
                                'help_url' : "https://genius.com/Evanescence-lithium-lyrics"
                            }
                        ]
                    }
                ]
                
            }
        ]
    }

]



from osgeo import ogr
from qgis.core import QgsTask

from .benchmark import Benchmark

# Можливі помилки
# Об'єкт з id "0" має помилку: "segments 142 and 229 of line 0 intersect at 33.5424, 48.2325"
# value is not unique'


class EDRA_validator:
    
    def __init__(self, layer, layer_exchange_name, structure_json, domains_json, driver_name):

        """
        Конструктор класу EDRA_validator.
        
        :param layer: ogr.Layer об'єкт, який представляє шар геоданих
        :type layer: ogr.Layer
        :param layer_exchange_name: назву шару за якою будемо збирати дані з структури json
        :type layer_exchange_name: str
        :param structure_json: структуру geojson файлу в якому записані дані про шарі
        :type structure_json: dict
        :param domains_json: дані про домені значень полів шарів
        :type domains_json: dict
        """


        # super().__init__()
        self.id_field_layer_dict = {'settlement': 'katottg', 'buildings_polygon': 'build_code', 'streets': 'str_id'}
        
        if layer is not None:
            self.layer = layer
            self.layerDefinition = self.layer.GetLayerDefn()
            self.layer_field_names = [self.layerDefinition.GetFieldDefn(i).GetName() for i in range(self.layerDefinition.GetFieldCount())]
        else:
            self.layer = None
            self.layerDefinition = None
            self.layer_field_names = None


        self.layer_exchange_name = layer_exchange_name
        self.structure_json = structure_json
        self.domains_json = domains_json
        self.driver_name = driver_name
        if layer_exchange_name in structure_json.keys():
            self.structure_field_names = structure_json[layer_exchange_name]['attributes'].keys()
            self.fields_structure_json = structure_json[layer_exchange_name]['attributes']
            # print(structure_json[layer_exchange_name]['geometry_type'])
            if structure_json[layer_exchange_name]['geometry_type'] == ['None']:
                self.required_geometry_type = None
            else:
                self.required_geometry_type = structure_json[layer_exchange_name]['geometry_type']
            # self.qt_and_ogr_data_types = {'integer': {'ogr_code': 0, 'qt_code': 2}, 'boolean': {'ogr_code': 0, 'qt_code': 1},
            #                         'double': {'ogr_code': 2, 'qt_code': 6}, 'text': {'ogr_code': 4, 'qt_code': 10}, 
            #                         'Date': {'ogr_code': 9, 'qt_code': 14}, 'Time': {'ogr_code': 10, 'qt_code': 15}, 
            #                         'DateTime': {'ogr_code': 11, 'qt_code': 16}, 'Binary': {'ogr_code': 15, 'qt_code': None}, 
            #                         'IntegerList': {'ogr_code': 16, 'qt_code': None}, 'RealList': {'ogr_code': 17, 'qt_code': None}, 
            #                         'StringList': {'ogr_code': 18, 'qt_code': 0}}
            
            self.qt_and_ogr_data_types = {
                'integer': {'ogr_codes': [0, 12], 'qt_codes': [2]},  # OFTInteger, OFTInteger64
                'boolean': {'ogr_codes': [0], 'qt_codes': [1]},    # OFTInteger (немає окремого типу для булевих)
                'double': {'ogr_codes': [2], 'qt_codes': [6]},     # OFTReal
                'text': {'ogr_codes': [4], 'qt_codes': [10]},      # OFTString
                'Date': {'ogr_codes': [9], 'qt_codes': [14]},      # OFTDate
                'Time': {'ogr_codes': [10], 'qt_codes': [15]},      # OFTTime
                'DateTime': {'ogr_codes': [11], 'qt_codes': [16]}, # OFTDateTime
                'Binary': {'ogr_codes': [8], 'qt_codes': [None]},  # OFTBinary
                'IntegerList': {'ogr_codes': [1, 13], 'qt_codes': [None]}, # OFTIntegerList, OFTInteger64List
                'RealList': {'ogr_codes': [3], 'qt_codes': [None]},        # OFTRealList
                'StringList': {'ogr_codes': [5], 'qt_codes': [0]}          # OFTStringList
            }
            for x in structure_json[layer_exchange_name]['attributes']:
                
                if structure_json[layer_exchange_name]['attributes'][x]['attribute_is_id'] == 'True':
                    self.id_field = x
                else: pass
                
            self.nameError = False
        else:
            self.structure_field_names = None
            self.fields_structure_json = None
            self.required_geometry_type = None
            self.structure_field_meta_types = None
            self.id_field = None
            self.nameError = True

    def str_contains_cyrillic(self, text):
        cyrillic_to_latin_map = {
            'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I', 'Ј': 'J', 'К': 'K',
            'М': 'M', 'О': 'O', 'Р': 'P', 'Ѕ': 'S', 'Т': 'T', 'Х': 'X', 'У': 'Y', 'а': 'a',
            'с': 'c', 'е': 'e', 'і': 'i', 'ј': 'j', 'о': 'o', 'р': 'p', 'ѕ': 's', 'х': 'x',
            'у': 'y'
        }
        return any(char in cyrillic_to_latin_map.keys() for char in text)
    
    def convert_cyrillic_to_latin_text(self, text):
        cyrillic_to_latin_map = {
            'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H', 'І': 'I', 'Ј': 'J', 'К': 'K',
            'М': 'M', 'О': 'O', 'Р': 'P', 'Ѕ': 'S', 'Т': 'T', 'Х': 'X', 'У': 'Y', 'а': 'a',
            'с': 'c', 'е': 'e', 'і': 'i', 'ј': 'j', 'о': 'o', 'р': 'p', 'ѕ': 's', 'х': 'x',
            'у': 'y'
        }
        
        return ''.join(cyrillic_to_latin_map.get(char, char) for char in text)

    def str_contains_uppercase(self, text):
        return any(char.isupper() for char in text)
    
    def str_contains_spaces(self, text):
        return ' ' in text
    
    def is_integer(self, string):
    # Перевіряємо, чи є рядок мінусовим числом
        if string:
            if isinstance(string, int):
                return True
            if string.startswith('-'):
                return string[1:].isdigit() and len(string) > 1
            return string.isdigit()
        else: return False
    
    def check_object_name(self, current_text, required_text, alias):
        
        error_dict = {}
        if type(current_text) == str and type(required_text) == str and type(alias) == str:

            if len(error_dict.keys()) == 0 and not self.str_contains_uppercase(required_text) and not self.str_contains_cyrillic(required_text) and not self.str_contains_spaces(required_text):
                current_text_not_changed = None
                
                current_text_not_changed = current_text
                current_text = current_text.lower()
                # print(current_text == required_text)
                current_text = self.convert_cyrillic_to_latin_text(current_text)
                # print(current_text == required_text)
                current_text = current_text.replace(' ', '')
                # print(f'current_text {current_text}')
                
                if current_text == required_text:
                    # print(f'current_text == required_text is TRUE')
                    if self.str_contains_uppercase(current_text_not_changed):
                        # print('capit')
                        error_dict['capital_leters'] = True
                    if self.str_contains_cyrillic(current_text_not_changed):
                        # print('cyr')
                        error_dict['used_cyrillic'] = True
                    if self.str_contains_spaces(current_text_not_changed):
                        # print('space')
                        error_dict['spaces_used'] = True
                elif current_text == alias:
                    error_dict['used_alias'] = required_text
                
        else:
            raise TypeError
        
        return error_dict
    
    
    def check_text_in_objects_list(self, current_text, type):
        #type = layer OR field
        
        if type == 'layer': 
            object_alias_key = 'layer_name_ua'
            object_json = self.structure_json
            
        if type == 'field':    
            object_alias_key = 'attribute_name_ua'
            object_json = self.fields_structure_json
            
        all_errors_dict = {}
        
        for required_text in object_json.keys():
            if current_text == required_text:
                return {'any_similar_name': True, "result_dict": {}}
            alias = object_json[required_text][object_alias_key]
            
            error_dict = self.check_object_name(current_text, required_text, alias)
            # print(f'Errors:\r\n{error_dict}')
            if len(error_dict.keys()) == 0:
                all_errors_dict[required_text] = {"general": True}
            else:    
                error_dict['valid_name'] = required_text
                # print(error_dict)
                all_errors_dict[required_text] = error_dict
        
        
        for x in all_errors_dict:
            if any(elem in all_errors_dict[x].keys() for elem in ['used_alias', 'used_cyrillic', 'spaces_used', 'capital_leters']):
                return {'any_similar_name': True, "result_dict": all_errors_dict[x]}
            else:
                continue    
        
        # print(f'ПЕРЕВІРКА НАШОГО ТЕКСТУ {current_text} {all_errors_dict}')
        if type == 'layer':     
            return {'any_similar_name': False, "result_dict": {"general": True}}
        if type == 'field':
            return {'any_similar_name': False, "result_dict": {"general": True}}
            

    def get_required_fields_names(self):
        required_field_names_list = []
        for x in self.structure_field_names:
            if self.fields_structure_json[x]['attribute_required'] == 'True':
                required_field_names_list.append(x)
            else: pass
        return required_field_names_list
    
    def check_feature_geometry_is_empty(self, feature):
        if self.check_feature_geometry_is_null(feature) == False:
            if feature.geometry().IsEmpty():
                return True
            else:
                return False
        else:
            return False
    
    def check_feature_geometry_is_null(self, feature):
        if self.required_geometry_type != None and feature.GetGeometryRef() == None:
            return True
        elif self.required_geometry_type == None and feature.GetGeometryRef() == None:
            return False
        elif self.required_geometry_type != None and feature.GetGeometryRef() != None:
            return False
        else:
            return False
    
    def get_is_layer_empty(self):
        if self.layer.GetFeatureCount() == 0:
            return True
        else:
            return False
        
    def compare_crs(self, required_crs_list, layer_crs):
        
        if layer_crs in required_crs_list:
            return True
        else:
            return False
    
    def get_unique_fields_names(self):
        unique_field_names_list = []
        for x in self.structure_field_names:
            if self.fields_structure_json[x]['attribute_unique'] == 'True':
                unique_field_names_list.append(x)
            else: pass
        return unique_field_names_list
                
                
    def compare_object_geometry_type(self, checking_object_geometry_type, required_geometry_type):
        try:
            if checking_object_geometry_type in required_geometry_type:
                return True
            else:
                return False
        except Exception as e:
            # print(f'В функції check_object_geometry_type виникла помилка: "{e}"')
            return False
    
    def check_fields_names(self):
        field_name_errors = {}
        for field_name in self.layer_field_names:
            field_name_errors_check_result = None
            field_name_errors_check_result = self.check_text_in_objects_list(field_name, 'field')
            # print(f'field_name_errors_check_result {field_name_errors_check_result}')
            # if field_name_errors_check_result['any_similar_name']:
            field_name_errors[field_name] = field_name_errors_check_result['result_dict']
                
        return field_name_errors
            

    def check_missing_fields(self):
        missing_field_names_list = []
        
        for field_name in self.structure_field_names:
            if field_name not in self.layer_field_names:
                missing_field_names_list.append(field_name)
            else: pass
        return missing_field_names_list
    
    
    def check_missing_required_fields(self):
        missing_required_field_names_list = []

        for field_name in self.get_required_fields_names():
            if field_name not in self.layer_field_names:
                missing_required_field_names_list.append(field_name)
            else: pass
        return missing_required_field_names_list
    
    
    def check_missing_unique_fields(self):
        missing_unique_field_names_list = []
        
        for field_name in self.get_unique_fields_names():
            if field_name not in self.layer_field_names:
                missing_unique_field_names_list.append(field_name)
            else: pass
        return missing_unique_field_names_list


    def check_extra_fields(self):
        extra_field_names_list = []
        
        for field_name in self.layer_field_names:
            if field_name not in self.structure_field_names:
                extra_field_names_list.append(field_name)
            else: pass
        return extra_field_names_list
    

    def check_fields_type_and_names(self, checker_object):
        list_check_fields: list[dict] = []
        
        for i in range(checker_object.GetFieldCount()):
            current_field_name = self.layerDefinition.GetFieldDefn(i).GetName()
            current_field_type_name = self.layerDefinition.GetFieldDefn(i).GetTypeName()
            
            
            if current_field_name in self.structure_field_names:
                required_field_type_name = self.fields_structure_json[current_field_name]['attribute_type']
                required_field_type_number_list = self.qt_and_ogr_data_types[required_field_type_name]['ogr_codes']
                required_field_type_names_list = [ogr.GetFieldTypeName(ogr_index) for ogr_index in required_field_type_number_list]
                check_field_name_result = current_field_name in self.structure_field_names
                if self.driver_name == 'GeoJSON' and required_field_type_name in ['Time', 'Date', 'DateTime'] and current_field_type_name == 'text':
                    check_field_type_result = True
                else: check_field_type_result = current_field_type_name in required_field_type_names_list
                #print(self.structure_field_meta_types[self.fields_structure_json[field_name]['attribute_type']])
                list_check_fields.append({"current_field_name": current_field_name, "check_field_type_result": check_field_type_result,
                                        "current_field_type": current_field_type_name, "check_field_name_result": check_field_name_result, "required_field_type": required_field_type_name})
            else:
                list_check_fields.append({"current_field_name": current_field_name, "check_field_type_result": False, "current_field_type": current_field_type_name, "check_field_name_result": False, "required_field_type": None})
        
        return list_check_fields


    def set_fields_constraints(self, list_check_fields):
        
        #Ступінь перевірки обмежень
        ConstraintStrengthHard = 1 # дві галочки, повне обмеження
        ConstraintStrengthNotSet = 0 #обмеження не встановлено взагалі
        ConstraintStrengthSoft = 2 #лише одна галочка, обмеження не повне

        # Обмеження
        ConstraintNotNull = 1 #не нульове обмеження
        ConstraintExpression = 4 #вираз
        ConstraintUnique = 2 #унікальне значення
        
        for x in list_check_fields:

            if x['check_field_type_result'] and x['check_field_name_result']:
                if self.fields_structure_json[x['current_field_name']]['attribute_required'] == 'required':
                    self.layer.setFieldConstraint(self.layer.fields().indexOf(x['current_field_name']), ConstraintNotNull, ConstraintStrengthHard)
                if self.fields_structure_json[x['current_field_name']]['attribute_unique'] == 'unique':
                    self.layer.setFieldConstraint(self.layer.fields().indexOf(x['current_field_name']), ConstraintUnique, ConstraintStrengthHard)


    # def check_feature_geometry(self, feature):
        
    #     feature_geometry = feature.geometry()
    #     geometry_type_check_result = self.check_object_geometry_type(feature_geometry, self.required_geometry_type)
        
    #     return {"geometry_type_check_result": {"current_type": QgsWkbTypes().displayString(feature_geometry.wkbType()), "required_type": self.required_geometry_type, "check_result":geometry_type_check_result}, "isEmpty":feature_geometry.isEmpty(), "isValid":feature_geometry.validateGeometry()}
    
    
    # def check_feature_attributes(self, feature):
        
    #     attr_validate_result_list = []
    #     for field in feature.fields():
    #         attr_validate_result = QgsVectorLayerUtils.validateAttribute(layer, feature, feature.fields().indexOf(field.name()), 1, 0), 
    #         attr_validate_result_list.append({field.name(): attr_validate_result})
            
    #     return attr_validate_result_list
    
    def check_feature_attribute_length_exceed(self, feature):
        #type == 'empty' OR 'null' or 'both'
        attrs_length_is_exceed_dict = {}
        
        for i in range(feature.GetFieldCount()):
            field_name = feature.GetFieldDefnRef(i).GetNameRef()
            # print(field_name)
            # print(self.fields_structure_json.keys())
            # print(field_name in self.fields_structure_json.keys())
            # print(feature[field_name])
            if field_name in self.fields_structure_json.keys() and feature[field_name] != None:
                if self.fields_structure_json[field_name]['attribute_type'] == 'text':
                    attribute_len = self.fields_structure_json[field_name]['attribute_len'].replace(' ', '')
                    if attribute_len == '' or attribute_len == 0:
                        continue
                    elif len(feature[field_name]) > int(attribute_len):
                        attrs_length_is_exceed_dict[field_name] = [len(feature[field_name]) ,attribute_len]

        return attrs_length_is_exceed_dict

    
    
    def check_feature_req_attrs_is_empty_or_null(self, feature, type):
        #type == 'empty' OR 'null' or 'both'
        req_attrs_is_empty_result_dict = {}
        
        for i in range(feature.GetFieldCount()):
            field_name = feature.GetFieldDefnRef(i).GetNameRef()
            if field_name in self.fields_structure_json.keys():
                if self.fields_structure_json[field_name]['attribute_required'] == 'True':
                    if type == 'empty':
                        if feature[field_name] == '':
                            req_attrs_is_empty_result_dict[field_name] = True
                    elif type == 'null':
                        if feature[field_name] == None:
                            req_attrs_is_empty_result_dict[field_name] = True
                    elif type == 'both':
                        if feature[field_name] == '' or feature[field_name] == None:
                            req_attrs_is_empty_result_dict[field_name] = True
                    else:
                        req_attrs_is_empty_result_dict[field_name] = False
                else: pass
                    
        return req_attrs_is_empty_result_dict

    
    def check_feature_unique_attrs_is_unique(self, feature):
        
        check_feature_unique_attrs_is_unique = []
        
        for field in feature.fields():
            if field.name() in self.fields_structure_json.keys():
                if self.fields_structure_json[field.name()]['attribute_unique'] == 'True':
                    if feature[field.name()]:
                        check_feature_unique_attrs_is_unique.append({field.name(): True})
                    else:
                        check_feature_unique_attrs_is_unique.append({field.name(): False})
            else: pass
        
        return check_feature_unique_attrs_is_unique

    def get_list_duplicated_fid(self, feature, layer_id, feature_fids):
            duplicated_id_list = []
            for id, fid in feature_fids.items():
                if fid == feature[self.id_field] and id != feature.GetFID():
                    duplicated_id_list.append([id, layer_id])
            return duplicated_id_list
        
    
    def check_attr_value_in_domain(self, feature, field_name):        
        
        domain_dict = self.domains_json[self.fields_structure_json[field_name]['domain']]['codes']
        domain_codes = []
        for x in domain_dict.keys():
            if self.is_integer(x.replace(' ', '')) and self.fields_structure_json[field_name]['attribute_type'] != 'text':
                domain_codes.append(int(x.replace(' ', '')))
            else: 
                domain_codes.append(x)
        # print(f'DOMAIN {domain_codes} {type()}')
            
        return feature[field_name] in domain_codes
    
    def get_layer_crs(self):
        
        srs = self.layer.GetSpatialRef()
        # print(srs)
        auth_name = None
        auth_code = None
        if srs is not None:
            auth_name = str(srs.GetAuthorityName(None))
            auth_code = str(srs.GetAuthorityCode(None))
            # print(f'{auth_name}:{auth_code}')
            return f'{auth_name}:{auth_code}'
        else:
            return ''
                    
        
    def check_null_attribute(self, attribute_name):
    # Відкриваємо GeoJSON файл
    
        for feature in self.layer:
            # Отримуємо значення атрибуту
            attribute_value = feature.GetField(attribute_name)
            
            # Перевірка на NULL
            if attribute_value is not None:
                return False  # Знайшли об'єкт з ненульовим значенням атрибуту
        
        return True  # Якщо жоден об'єкт не має ненульового значення атрибуту

    


class EDRA_exchange_layer_checker:
    def __init__(self, layer:ogr.Layer, layer_exchange_name:str, structure_json:dict, domains_json:dict, layer_props: dict, layer_id: str, driver_name: str, task: QgsTask = None):

        self.layer_EDRA_valid_class = EDRA_validator(
            layer = layer,
            layer_exchange_name = layer_exchange_name,
            structure_json = structure_json,
            domains_json = domains_json,
            driver_name = driver_name)
        self.layer_props = layer_props
        self.check_result_dict = {}
        self.check_result_legacy = {}
        self.layer_id = layer_id
        self.layer_props['related_layer_id'] = layer_id
        self.Task = task
        self.driver_name = driver_name
        
        self.parse_bench = Benchmark()
        if self.Task is not None:        
            self.Task.setProgress(3)

    def create_inspection_dict(self, inspection_type_name=None, item_name=None, item_tool_tip=None, criticity=None, help_url=None):
        inspection_dict = {
            'type': 'inspection'
        }
        if inspection_type_name:
            inspection_dict['inspetcion_type_name'] = inspection_type_name
        if item_name:
            inspection_dict['item_name'] = item_name
        if criticity is not None:
            inspection_dict['criticity'] = criticity
        if help_url:
            inspection_dict['help_url'] = help_url

        return inspection_dict

    def check_crs_is_equal_required(self):
        layer_crs = self.layer_EDRA_valid_class.get_layer_crs()
        if self.layer_EDRA_valid_class.compare_crs(self.layer_props['required_crs_list'], layer_crs):
            return []
        else:
            return [layer_crs, ', '.join(self.layer_props['required_crs_list'])]

    def check_missing_required_fields(self):
        missing_required_fields_list = self.layer_EDRA_valid_class.check_missing_required_fields()
        return missing_required_fields_list
            # self.check_result_dict['missing required fields'] = self.layer_EDRA_valid_class.check_missing_required_fields()
            
    def check_missing_fields(self):
        missing_fields_list = self.layer_EDRA_valid_class.check_missing_fields()
        return missing_fields_list
        
    def check_wrong_fields_included(self):
        extra_fields_list = self.layer_EDRA_valid_class.check_extra_fields()
        return extra_fields_list
            # self.check_result_dict['missing required fields'] = extra_fields_list
        
    def check_wrong_object_geometry_type(self, checker_object):

        if isinstance(checker_object, ogr.Feature):
            geom_type = checker_object.GetDefnRef().GetGeomType()
        else:
            geom_type = checker_object.GetGeomType()
            
        geometry_type_check_result = self.layer_EDRA_valid_class.compare_object_geometry_type(ogr.GeometryTypeToName(geom_type).replace(' ', ''), self.layer_EDRA_valid_class.required_geometry_type)
        
        if not geometry_type_check_result:
            return [ogr.GeometryTypeToName(geom_type).replace(' ', ''), self.layer_EDRA_valid_class.required_geometry_type]
        else:
            return []
            # self.check_result_dict['missing required fields'] = [QgsWkbTypes().displayString(layer.wkbType(), self.layer_EDRA_valid_class.check_extra_fields())]

    def check_wrong_fields_types(self):
        # {"current_field_name": x.name(), "check_field_type_result": check_field_type_result, "current_field_type": x.type(), "check_field_name_result": check_field_name_result, "required_field_type": self.structure_field_meta_types[self.fields_structure_json[x.name()]['attribute_type']]}
        
        errors_field_type_dict = {}
        for x in self.fields_check_results_list:
            
            if x['check_field_type_result'] == False and x['check_field_name_result'] == True:
                if self.driver_name == "GeoJSON" and x['current_field_type'] in [ogr.GetFieldTypeName(ogr_index) for ogr_index in self.layer_EDRA_valid_class.qt_and_ogr_data_types['text']['ogr_codes']] and x['current_field_name'] not in self.layer_EDRA_valid_class.get_required_fields_names() and self.layer_EDRA_valid_class.check_null_attribute(x['current_field_name']):
                    pass
                else:
                    errors_field_type_dict[x['current_field_name']] = [x['current_field_type'], x['required_field_type']]
            else: pass
        
        return errors_field_type_dict    
                # self.check_result_dict['wrong feild type'] = {}
                # self.check_result_dict['wrong feild type'][x['current_field_name']] = [ x['current_field_type'], x['required_field_type'] ]
            
    def check_required_fields_is_empty_or_null(self, feature, type):
        check_required_fields_is_empty_or_null_result = self.layer_EDRA_valid_class.check_feature_req_attrs_is_empty_or_null(feature, type)
        empty_required_fields_list = []
        if check_required_fields_is_empty_or_null_result:
            for x in check_required_fields_is_empty_or_null_result:
                if check_required_fields_is_empty_or_null_result[x]:
                    empty_required_fields_list.append(x)
                else:
                    continue
        
        return empty_required_fields_list
        
    def check_attr_value_in_domain(self, feature):
        
        result_dict = {}
        
        for i in range(feature.GetFieldCount()):
            field_name = feature.GetFieldDefnRef(i).GetNameRef()
            if field_name in self.layer_EDRA_valid_class.fields_structure_json.keys():
                
                if self.layer_EDRA_valid_class.fields_structure_json[field_name]['domain'] != '' and self.layer_EDRA_valid_class.fields_structure_json[field_name]['domain'] != None:
                    
                    if self.layer_EDRA_valid_class.fields_structure_json[field_name]['attribute_required'] == True or feature[field_name] != None:
                        check_is_value_in_domain = self.layer_EDRA_valid_class.check_attr_value_in_domain(feature, field_name) 
                    
                        if not check_is_value_in_domain:
                            result_dict[field_name] =  [feature[field_name], 'Посилання до домену']
                        else: pass
                    else:
                        pass   
                
                else:
                    continue
            else:
                continue
                
        return result_dict
    
    def write_features_check_result(self):
        # features_dict_legacy = {}
        
        # features_fids = {}
        # if self.layer_EDRA_valid_class.id_field in self.layer_EDRA_valid_class.layer_field_names:
        #     for feature in self.layer_EDRA_valid_class.layer:
        #         features_fids[feature.GetFID()] = feature[self.layer_EDRA_valid_class.id_field]

        self.main_features_check_bench = Benchmark()

        container_features = None
        container_features = {}
        container_features['type'] = 'container'
        container_features['item_name'] = "Об'єкти шару"
        container_features['subitems'] = []
        
        self.main_features_check_bench.start("start_check_all_objects")
        
        self.check_feature_bench = Benchmark()
        
        for feature in self.layer_EDRA_valid_class.layer:
            
            if self.Task is not None:
                if self.Task.isCanceled(): return 
                progress = self.Task.progress()
                if progress < 95:
                    self.Task.setProgress(progress + 0.01)
                else:
                    self.Task.setProgress(3)
            feature_dict_result = None
            
            feature_dict_result = {
                'type' : 'feature',
                'item_name' : f"Об'єкт '{feature.GetFID()}'",
                'related_feature_id' : feature.GetFID(),
                'subitems' : []
            }
            
            container_features_attribute_errors = None
            container_features_attribute_errors = {}
            container_features_attribute_errors['type'] = 'container'
            container_features_attribute_errors['item_name'] = "Перевірка на наявність помилок в атрибутах об'єктів (features) об'єкту"
            container_features_attribute_errors['subitems'] = []

            
            self.check_feature_bench.start('check_required_fields_is_empty')
            
            required_fields_is_empty_list = self.check_required_fields_is_empty_or_null(feature, 'empty')
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('check_required_fields_is_null')
            
            required_fields_is_null_list = self.check_required_fields_is_empty_or_null(feature, 'null')
            
            self.check_feature_bench.stop()
            
            container_required_fields_is_empty_or_null = None
            container_required_fields_is_empty_or_null = {}
            container_required_fields_is_empty_or_null['type'] = 'container'
            container_required_fields_is_empty_or_null['item_name'] = "Перевірка на заповненість обов'язкових (атрибутів) об'єкту"
            container_required_fields_is_empty_or_null['subitems'] = []
            
            self.check_feature_bench.start('write_dict_check_required_fields')
            
            if len(required_fields_is_empty_list) > 0:
                #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
                for empty_field in required_fields_is_empty_list:
                    insception_empty_field_error = None
                    insception_empty_field_error = self.create_inspection_dict(
                        inspection_type_name = "Перевірка на заповненість полів (атрибутів) об'єкту", #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Обов'язковий атрибут «{empty_field}» не заповнений (is empty)", 
                        item_tool_tip = f"Обов'язковий атрибут «{empty_field}» не заповнений (is empty)", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                    )
                    
                    container_required_fields_is_empty_or_null['subitems'].append(insception_empty_field_error)
                    del insception_empty_field_error
                    
                    
            if len(required_fields_is_null_list) > 0:
                #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
                for null_field in required_fields_is_null_list:
                    insception_null_field_error = None
                    insception_null_field_error = self.create_inspection_dict(
                        inspection_type_name = "Перевірка на заповненість полів (атрибутів) об'єкту", #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Обов'язковий атрибут «{null_field}» не заповнений (is null)", 
                        item_tool_tip = f"Обов'язковий атрибут «{null_field}» не заповнений (is null)", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                    )
                    container_required_fields_is_empty_or_null['subitems'].append(insception_null_field_error)
                    del insception_null_field_error
                    
            if len(required_fields_is_empty_list) == 0 and len(required_fields_is_null_list) == 0:
                insception_dict_field_not_emprty_or_null = None
                insception_dict_field_not_emprty_or_null = self.create_inspection_dict(                    
                    inspection_type_name = "Перевірка на заповненість обов'язкових полів (атрибутів) об'єкту", #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Всі обов'язкові поля (атрибути) класу заповнені", 
                    item_tool_tip = f"Всі обов'язкові поля (атрибути) класу заповнені", 
                    criticity = 0, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_required_fields_is_empty_or_null['subitems'].append(insception_dict_field_not_emprty_or_null)
                del insception_dict_field_not_emprty_or_null
                
            container_features_attribute_errors['subitems'].append(container_required_fields_is_empty_or_null)
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('delete_objects_after_created_dict_check_required_fields')
            
            del container_required_fields_is_empty_or_null
            
            del required_fields_is_empty_list
            del required_fields_is_null_list
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('check_attr_value_in_domain')
            
            attribute_values_unclassified_dict = self.check_attr_value_in_domain(feature)
            
            self.check_feature_bench.stop()
            
            container_attributes_values_unclassified = None
            container_attributes_values_unclassified = {}
            container_attributes_values_unclassified['type'] = 'container'
            container_attributes_values_unclassified['item_name'] = "Перевірка на відповідність значень полів (атрибутів) об'єкту доменам"
            container_attributes_values_unclassified['subitems'] = []
            
            self.check_feature_bench.start('wtite_unclassified_dict')
            
            if len(attribute_values_unclassified_dict.keys()) > 0:
                #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
                
                for field_name in attribute_values_unclassified_dict:
                    
                    # if self.layer_EDRA_valid_class.fields_structure_json[field_name]['attribute_required'] == True or attribute_values_unclassified_dict[field_name][0] != None:
                        
                    insception_unclassified_value_error = None
                    insception_unclassified_value_error = self.create_inspection_dict(
                        inspection_type_name = "Перевірка на відповідність значень полів (атрибутів) об'єкту доменам", #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Атрибут: '{field_name}' має значення '{attribute_values_unclassified_dict[field_name][0]}', що не відповідає домену (див. опис поля)", 
                        item_tool_tip = f"Значення атрибуту '{field_name}' не відповідає домену", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                    )
                    container_attributes_values_unclassified['subitems'].append(insception_unclassified_value_error)
                    del insception_unclassified_value_error
                    
            elif len(attribute_values_unclassified_dict.keys()) == 0 :
                insception_classified_value = None
                insception_classified_value = self.create_inspection_dict(                    
                    inspection_type_name = "Перевірка на відповідність значень полів (атрибутів) об'єкту доменам", #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Всі значення полів відповідають доменам", 
                    item_tool_tip = f"Всі значення полів відповідають доменам", 
                    criticity = 0, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_attributes_values_unclassified['subitems'].append(insception_classified_value)
                del insception_classified_value
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('delete_objects_after_created_unclassified_dict')
            
            container_features_attribute_errors['subitems'].append(container_attributes_values_unclassified)
            del container_attributes_values_unclassified
            del attribute_values_unclassified_dict
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('check_attributes_length_exceed')
            
            attributes_length_exceed_dict = self.layer_EDRA_valid_class.check_feature_attribute_length_exceed(feature)
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('wtite_attributes_length_exceed_dict')
            
            container_attributes_values_length = None
            container_attributes_values_length = {}
            container_attributes_values_length['type'] = 'container'
            container_attributes_values_length['item_name'] = "Перевірка на відповідність довжини значення полів (атрибутів) об'єкту"
            container_attributes_values_length['subitems'] = []
            
            if len(attributes_length_exceed_dict.keys()) > 0:
                #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
                for field_name in attributes_length_exceed_dict:
                    insception_attributes_length_value_exceed = None
                    insception_attributes_length_value_exceed = self.create_inspection_dict(
                        inspection_type_name = 'Перевірка на відповідність довжини значення атрибуту', #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Атрибут: '{field_name}' має довжину {attributes_length_exceed_dict[field_name][0]}, а треба не більше {attributes_length_exceed_dict[field_name][1]}", 
                        item_tool_tip = f"Атрибут: '{field_name}' має довжину більше дозволеної структурою", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                    )
                    container_attributes_values_length['subitems'].append(insception_attributes_length_value_exceed)
                    del insception_attributes_length_value_exceed
                    
            elif len(attributes_length_exceed_dict.keys()) == 0 :
                insception_attributes_length_value = None
                insception_attributes_length_value = self.create_inspection_dict(                    
                    inspection_type_name = "Перевірка на відповідність довжини значення атрибуту", #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Всі значення атрибутів не перевищують допустиму довжину", 
                    item_tool_tip = f"Всі значення атрибутів не перевищують допустиму довжину", 
                    criticity = 0, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_attributes_values_length['subitems'].append(insception_attributes_length_value)
                del insception_attributes_length_value
                
            container_features_attribute_errors['subitems'].append(container_attributes_values_length)
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('delete_objects_after_attributes_length_exceed_dict')
            
            del attributes_length_exceed_dict
            del container_attributes_values_length
            
            self.check_feature_bench.stop()
            # duplicated_guid_list = self.layer_EDRA_valid_class.get_list_duplicated_fid(feature, self.layer_props['related_layer_id'], features_fids)
            
            
            # # Розкоментувати код і дописати контейнер для дуплікейтед гуід
            # container_duplicated_guid = None
            # container_duplicated_guid = {}
            # container_duplicated_guid['type'] = 'container'
            # container_duplicated_guid['item_name'] = "Перевірка на унікальність ID"
            # container_duplicated_guid['subitems'] = []
            
            # if len(duplicated_guid_list) > 0:
            #     #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
            #     for duplicate_item in duplicated_guid_list:
                    
            #         insception_feature_id_is_not_unique = None
            #         insception_feature_id_is_not_unique = self.create_inspection_dict(
            #             inspection_type_name = 'Перевірка на унікальність ID', #Підтягувати перевірку з файлу структури з помилками
            #             item_name = f"Об'єкт ({feature.GetFID()}) має не унікальний ідентифікатор. Дублюючий елемент, ID: {[duplicate_item][0]}", 
            #             item_tool_tip = f"Об'єкт має не унікальний ідентифікатор", 
            #             criticity = 2, 
            #             help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
            #         )
            #         container_duplicated_guid['subitems'].append(insception_feature_id_is_not_unique)
                    
            # elif len(duplicated_guid_list) == 0 :
            #     insception_feature_id_is_unique = None
            #     insception_feature_id_is_unique = self.create_inspection_dict(                    
            #         inspection_type_name = "Перевірка на унікальність ID", #Підтягувати перевірку з файлу структури з помилками
            #         item_name = f"Ідентифікатор об'єкта унікальний", 
            #         item_tool_tip = f"Ідентифікатор об'єкта унікальний", 
            #         criticity = 0, 
            #         help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
            #     )
            #     container_duplicated_guid['subitems'].append(insception_feature_id_is_unique)
                
            # container_features_attribute_errors['subitems'].append(container_duplicated_guid)
            
            self.check_feature_bench.start('wtite_container_features_attribute_errors_dict')
            
            feature_dict_result['subitems'].append(container_features_attribute_errors)
            del container_features_attribute_errors
            
            self.check_feature_bench.stop()
            
            self.check_feature_bench.start('wtite_general_feature_dict')
            
            container_features['subitems'].append(feature_dict_result)
            del feature_dict_result
            
            self.check_feature_bench.stop()
            
            # features_dict_legacy[feature.GetFID()] = {
            #     "required_attribute_empty": required_fields_is_empty_list,
            #     "required_attribute_empty": required_fields_is_null_list,
            #     "attribute_value_unclassifyed": attribute_values_unclassified_dict,
            #     # "duplicated_GUID": duplicated_guid_list,
            #     "attribute_length_exceed": attributes_length_exceed_dict,
                
            #     }
            
            # if self.layer_EDRA_valid_class.required_geometry_type != None:
            #     features_dict_legacy[feature.GetFID()]['geometry_errors'] = {
            #         "empty" : self.layer_EDRA_valid_class.check_feature_geometry_is_empty(feature),
            #         "null" : self.layer_EDRA_valid_class.check_feature_geometry_is_null(feature),
            #         "geometry_type_wrong" : self.check_wrong_object_geometry_type(feature)
            #         }
            
        
        #print(features_dict)
        
        
        
        self.main_features_check_bench.stop()
        
        self.main_features_check_bench.join(self.check_feature_bench)
        
        print("Check features..... Done")
        print(self.main_features_check_bench.get_report())
        print("end")
        
        return container_features
            
    def write_result_dict(self):
        
        self.write_result_dict_bench = Benchmark()
        
        if self.layer_EDRA_valid_class.required_geometry_type != None:
            
            self.write_result_dict_bench.start('check_crs_is_equal_required')
            result_check_crs_layer = self.check_crs_is_equal_required()
            # print(result_check_crs_layer)
            inspection_dict_layer_wrong_crs = None
            
            self.write_result_dict_bench.stop()
            
            if result_check_crs_layer != []:
                layer_crs = result_check_crs_layer[0]
                required_crs_str = result_check_crs_layer[1]
                inspection_dict_layer_wrong_crs = self.create_inspection_dict(                    
                    inspection_type_name = 'Перевірка системи координат шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Невідповідна СК шару: «{layer_crs}», очікується: «{required_crs_str}»", 
                    item_tool_tip = f"Невідповідна СК шару", 
                    criticity = 2, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                
            elif result_check_crs_layer == []:
                inspection_dict_layer_wrong_crs = self.create_inspection_dict(                    
                    inspection_type_name = 'Перевірка системи координат шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Система координат шару правильна", 
                    item_tool_tip = f"Невідповідна СК шару", 
                    criticity = 0, 
                    help_url = None
                )

            self.check_result_dict['subitems'].append(inspection_dict_layer_wrong_crs)
            del inspection_dict_layer_wrong_crs
            del result_check_crs_layer
            
            
            
            # self.check_result_legacy[self.layer_props['related_layer_id']]['wrong_layer_CRS'] = result_check_crs_layer
            self.write_result_dict_bench.start('check_wrong_object_geometry_type')
            
            result_check_wrong_layer_geometry_type = self.check_wrong_object_geometry_type(self.layer_EDRA_valid_class.layer)
            
            insception_dict_wrong_layer_geometry_type = None
            
            if result_check_wrong_layer_geometry_type != []:
                current_layer_geometry_type = result_check_wrong_layer_geometry_type[0]
                required_geometry_type = result_check_wrong_layer_geometry_type[1]
                insception_dict_wrong_layer_geometry_type = self.create_inspection_dict(                    
                    inspection_type_name = 'Перевірка типу геометрії шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Невідповідний геометричний тип класу: «{current_layer_geometry_type}», вимагається: «{required_geometry_type}»", 
                    item_tool_tip = f"Невідповідний геометричний тип класу", 
                    criticity = 2, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                
            elif result_check_wrong_layer_geometry_type == []:
                insception_dict_wrong_layer_geometry_type = self.create_inspection_dict(                    
                    inspection_type_name = 'Перевірка типу геометрії шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Геометричний тип класу правильний", 
                    item_tool_tip = f"Геометричний тип класу правильний", 
                    criticity = 0, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
            
            self.check_result_dict['subitems'].append(insception_dict_wrong_layer_geometry_type)
            
            del insception_dict_wrong_layer_geometry_type
            del result_check_wrong_layer_geometry_type
            
            self.write_result_dict_bench.stop()
            # self.check_result_legacy[self.layer_props['related_layer_id']]['wrong_geometry_type'] = result_check_wrong_layer_geometry_type
            
        # if 'layer_name_errors' not in self.check_result_legacy[self.layer_props['related_layer_id']].keys():
        #     self.check_result_legacy[self.layer_props['related_layer_id']]['layer_name_errors'] = {}
        
        self.write_result_dict_bench.start('check_fields_type_and_names')
        
        self.fields_check_results_list = self.layer_EDRA_valid_class.check_fields_type_and_names(self.layer_EDRA_valid_class.layerDefinition)
        
        self.write_result_dict_bench.stop()
        
        container_layer_field_errors = None
        container_layer_field_errors = {}
        container_layer_field_errors['type'] = 'container'
        container_layer_field_errors['item_name'] = "Перевірка на наявність помилок в полях (атрибутах) шару"
        container_layer_field_errors['subitems'] = []
        
        self.write_result_dict_bench.start('check_missing_required_fields')
        
        missing_required_fields_list = self.check_missing_required_fields()
        
        
        
        container_missing_required_fields = None
        container_missing_required_fields = {}
        container_missing_required_fields['type'] = 'container'
        container_missing_required_fields['item_name'] = "Перевірка на наявність обов\'язкових полів (атрибутів) шару"
        container_missing_required_fields['subitems'] = []
        
        if len(missing_required_fields_list) > 0:
            #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
            for missing_required_field in missing_required_fields_list:
                insception_missing_required_field_error = None
                insception_missing_required_field_error = self.create_inspection_dict(
                    inspection_type_name = 'Перевірка на наявність обов\'язкових полів (атрибутів) шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Відсутній обов'язковий атрибут «{missing_required_field}»", 
                    item_tool_tip = f"Відсутній обов'язковий атрибут «{missing_required_field}»", 
                    criticity = 2, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_missing_required_fields['subitems'].append(insception_missing_required_field_error)
                
        elif len(missing_required_fields_list) == 0:
            insception_dict_layer_missing_required_fields = None
            insception_dict_layer_missing_required_fields = self.create_inspection_dict(                    
                inspection_type_name = 'Перевірка на наявність обов\'язкових полів (атрибутів) шару', #Підтягувати перевірку з файлу структури з помилками
                item_name = f"Всі обов'язкові атрибути класу наявні", 
                item_tool_tip = f"Всі обов'язкові атрибути класу наявні", 
                criticity = 0, 
                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
            )
            container_missing_required_fields['subitems'].append(insception_dict_layer_missing_required_fields)
            
        container_layer_field_errors['subitems'].append(container_missing_required_fields)
        
        del missing_required_fields_list
        del container_missing_required_fields
        
        self.write_result_dict_bench.stop()
        
        self.write_result_dict_bench.start('check_missing_fields')
        
        missing_fields_list = self.check_missing_fields()
        
        container_missing_fields = None
        container_missing_fields = {}
        container_missing_fields['type'] = 'container'
        container_missing_fields['item_name'] = "Перевірка на наявність всіх полів (атрибутів) шару"
        container_missing_fields['subitems'] = []
        
        if len(missing_fields_list) > 0:
            #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
            for missing_field in missing_fields_list:
                insception_missing_field_error = None
                insception_missing_field_error = self.create_inspection_dict(
                    inspection_type_name = 'Перевірка на наявність полів (атрибутів) шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Відсутній атрибут «{missing_field}»", 
                    item_tool_tip = f"Відсутній атрибут «{missing_field}»", 
                    criticity = 2, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_missing_fields['subitems'].append(insception_missing_field_error)
                
        elif len(missing_fields_list) == 0:
            insception_dict_layer_missing_fields = None
            insception_dict_layer_missing_fields = self.create_inspection_dict(                    
                inspection_type_name = 'Перевірка на наявність всіх полів (атрибутів) шару', #Підтягувати перевірку з файлу структури з помилками
                item_name = f"Всі поля (атрибути) класу наявні", 
                item_tool_tip = f"Всі поля (атрибути) класу наявні", 
                criticity = 0, 
                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
            )
            container_missing_fields['subitems'].append(insception_dict_layer_missing_fields)
            
        container_layer_field_errors['subitems'].append(container_missing_fields)
        del missing_fields_list
        del container_missing_fields
        
        self.write_result_dict_bench.stop()
        
        self.write_result_dict_bench.start('check_missing_fields')
        
        wrong_fields_types_list = self.check_wrong_fields_types()
        
        container_wrong_fields_types_errors = None
        container_wrong_fields_types_errors = {}
        container_wrong_fields_types_errors['type'] = 'container'
        container_wrong_fields_types_errors['item_name'] = "Перевірка типів даних полів (атрибутів) шару"
        container_wrong_fields_types_errors['subitems'] = []
        
        if len(wrong_fields_types_list.keys()) > 0:
            #ДОПИСАТИ ЕЛЕМЕНТ ПЕРЕВІРКИ І ПЕРЕРОБИТИ ЛОГІКУ ВИВОДУ В КОНТЕЙНЕРИ ІНШИХ ПОМИЛОК АТРИБУТІВ, щоб там кожен
            for error_field in wrong_fields_types_list:
                insception_wrong_field_type_error = None
                insception_wrong_field_type_error = self.create_inspection_dict(
                    inspection_type_name = 'Перевірка типу поля (атрибуту) шару', #Підтягувати перевірку з файлу структури з помилками
                    item_name = f"Атрибут «{error_field}» має тип:«{wrong_fields_types_list[error_field][0]}», вимагається: «{wrong_fields_types_list[error_field][1]}»", 
                    item_tool_tip = f"Атрибут «{error_field}» має некоректний тип даних", 
                    criticity = 2, 
                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
                )
                container_wrong_fields_types_errors['subitems'].append(insception_wrong_field_type_error)
                
        elif len(wrong_fields_types_list) == 0:
            insception_no_wrong_field_type_error = None
            insception_no_wrong_field_type_error = self.create_inspection_dict(
                inspection_type_name = 'Перевірка типів даних полів (атрибутів) шару', #Підтягувати перевірку з файлу структури з помилками
                item_name = f"Всі поля (атрибути) мають коректний тип даних", 
                item_tool_tip = f"Всі поля (атрибути) мають коректний тип даних", 
                criticity = 0, 
                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll)
            )
            container_wrong_fields_types_errors['subitems'].append(insception_no_wrong_field_type_error)
            
        container_layer_field_errors['subitems'].append(container_wrong_fields_types_errors)
        
        del wrong_fields_types_list
        del container_wrong_fields_types_errors
        
        self.write_result_dict_bench.stop()
        
        container_wrong_fields_names_errors = None
        container_wrong_fields_names_errors = {}
        container_wrong_fields_names_errors['type'] = 'container'
        container_wrong_fields_names_errors['item_name'] = "Перевірка назви полів (атрибутів) шару"
        container_wrong_fields_names_errors['subitems'] = []
        
        self.write_result_dict_bench.start('check_fields_names')
        
        wrong_layer_fields_names_list = self.layer_EDRA_valid_class.check_fields_names()
        
        if len(wrong_layer_fields_names_list) > 0:
            # print(wrong_layer_fields_names_list)
            for wrong_field_name in wrong_layer_fields_names_list:
                # print(wrong_field_name)
                container_wrong_field_name_errors = None
                container_wrong_field_name_errors = {}
                container_wrong_field_name_errors['type'] = 'container'
                container_wrong_field_name_errors['item_name'] = f"Перевірка назви поля (атрибута) «{wrong_field_name}»"
                container_wrong_field_name_errors['subitems'] = []
                if len(wrong_layer_fields_names_list[wrong_field_name].keys()) > 0:
                    
                    for x in wrong_layer_fields_names_list[wrong_field_name]:
                        
                        if [x] == "general":
                            insception_dict_field_error_name_general = None
                            insception_dict_field_error_name_general = self.create_inspection_dict(                    
                                inspection_type_name = 'Перевірка назви поля (атрибута)', #Підтягувати перевірку з файлу структури з помилками
                                item_name = f"Назва поля (атрибута) «{wrong_field_name}» не відповідає структурі", 
                                item_tool_tip = f"Назва поля (атрибута) не відповідає структурі", 
                                criticity = 2, 
                                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                            )
                            container_wrong_field_name_errors['subitems'].append(insception_dict_field_error_name_general)
                        
                        if [x] == "used_alias":
                            insception_dict_field_error_name_used_alias = None
                            insception_dict_field_error_name_used_alias = self.create_inspection_dict(                    
                                inspection_type_name = 'Перевірка назви поля (атрибута)', #Підтягувати перевірку з файлу структури з помилками
                                item_name = f"Замість назви поля (атрибута) використано псевдонім «{wrong_field_name}», вимагається «{wrong_layer_fields_names_list[wrong_field_name]['result_dict']['valid_name']}»", 
                                item_tool_tip = f"Замість назви поля (атрибута) використано псевдонім»", 
                                criticity = 2, 
                                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                            )
                            container_wrong_field_name_errors['subitems'].append(insception_dict_field_error_name_used_alias)
                        
                        if [x] == "spaces_used":
                            insception_dict_field_error_name_spaces_used = None
                            insception_dict_field_error_name_spaces_used = self.create_inspection_dict(                    
                                inspection_type_name = 'Перевірка назви поля (атрибута)', #Підтягувати перевірку з файлу структури з помилками
                                item_name = f"В назві поля (атрибута) «{wrong_field_name}» наявні пробіли", 
                                item_tool_tip = f"В назві поля (атрибута) наявні пробіли", 
                                criticity = 2, 
                                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                            )
                            container_wrong_field_name_errors['subitems'].append(insception_dict_field_error_name_spaces_used)
                        
                        if [x] == "used_cyrillic":
                            insception_dict_field_error_name_used_cyrillic = None
                            insception_dict_field_error_name_used_cyrillic = self.create_inspection_dict(                    
                                inspection_type_name = 'Перевірка назви поля (атрибута)', #Підтягувати перевірку з файлу структури з помилками
                                item_name = f"В назві поля (атрибута) «{wrong_field_name}» наявні кириличні літери", 
                                item_tool_tip = f"В назві поля (атрибута) наявні кириличні літери", 
                                criticity = 2, 
                                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                            )
                            container_wrong_field_name_errors['subitems'].append(insception_dict_field_error_name_used_cyrillic)
                            
                    
                elif len(wrong_layer_fields_names_list[wrong_field_name].keys()) == 0:
                    insception_dict_field_no_error_name = None
                    insception_dict_field_no_error_name = self.create_inspection_dict(                    
                        inspection_type_name = 'Перевірка назви поля (атрибута)', #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Поле «{wrong_field_name}» має коректну назву", 
                        item_tool_tip = f"Поле має коректну назву", 
                        criticity = 0, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                    )
                    container_wrong_field_name_errors['subitems'].append(insception_dict_field_no_error_name)
                
                container_wrong_fields_names_errors['subitems'].append(container_wrong_field_name_errors)
                    
        elif len(wrong_layer_fields_names_list) == 0:            
            insception_dict_fields_no_error_name = None
            insception_dict_fields_no_error_name = self.create_inspection_dict(                    
                inspection_type_name = 'Перевірка назви атрибутів', #Підтягувати перевірку з файлу структури з помилками
                item_name = f"У шарі «{self.layer_props['layer_real_name']}» відсутні атрибути", 
                item_tool_tip = f"У шарі  відсутні атрибути", 
                criticity = 2, 
                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
            )
            container_wrong_fields_names_errors['subitems'].append(insception_dict_fields_no_error_name)
            del insception_dict_fields_no_error_name
        
        del wrong_layer_fields_names_list
        
            
        container_layer_field_errors['subitems'].append(container_wrong_fields_names_errors)
        del container_wrong_fields_names_errors
        
        self.check_result_dict['subitems'].append(container_layer_field_errors)
        
        del container_layer_field_errors
        
        self.write_result_dict_bench.stop()
        
        # self.check_result_legacy[self.layer_props['related_layer_id']]['field_errors'] = {}
        # self.check_result_legacy[self.layer_props['related_layer_id']]['field_errors']['missing_required_fields'] = missing_required_fields_list
        # self.check_result_legacy[self.layer_props['related_layer_id']]['field_errors']['missing_fields'] = missing_fields_list
        # self.check_result_legacy[self.layer_props['related_layer_id']]['field_errors']['wrong_field_type'] = wrong_fields_types_list
        
        # self.check_result_legacy[self.layer_props['related_layer_id']]['field_name_errors'] = wrong_layer_fields_names_list
        # 'field_name_errors'
        
        #self.check_result_dict[layer_EDRA_valid_class.layer.name()] ['wrong_layer_CRS'] = []
        
        
        #### НЕ ЗАБУТИ РОЗКОМЕНТУВАТИ
        
        self.write_result_dict_bench.start('write_features_check_result')
        
        features_check_results = self.write_features_check_result() #повертається список, перший об'єкт це легасі словник, другий це контейнер для нової структури
        self.check_result_dict['subitems'].append(features_check_results)
        del features_check_results
        
        self.write_result_dict_bench.stop()
        
        
        if self.main_features_check_bench is not None:
            self.write_result_dict_bench.join(self.main_features_check_bench)
            
        
        print("Check layer..... Done")
        print(self.write_result_dict_bench.get_report())
        print("end")
            
            
            # self.check_result_legacy[self.layer_props['related_layer_id']]['features'] = features_check_results[0]      
    
    def run(self):
        
        self.check_result_dict['item_name'] = f"Шар {self.layer_props['layer_name']}"
        self.check_result_dict['item_tooltip'] = f"Шар {self.layer_props['layer_real_name']}" 
        self.check_result_dict['visible_layer_name'] = self.layer_props['layer_name']
        self.check_result_dict['layer_real_name'] = self.layer_props['layer_real_name']
        self.check_result_dict['related_layer_id'] = self.layer_props['related_layer_id']
        self.check_result_dict['type'] = 'layer'
        self.check_result_dict['subitems'] = []
        
        
        
        if self.layer_EDRA_valid_class.layer is not None:
            
            self.parse_bench.start('check_layer_is_empty')
            
            insception_layer_is_empty = None
            layer_is_empty =self.layer_EDRA_valid_class.get_is_layer_empty()
            if layer_is_empty:    
                insception_layer_is_empty = self.create_inspection_dict(                    
                        inspection_type_name = 'Перевірка на наявність об’єктів в шарі', #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"В шарі {self.layer_props['layer_name']} відсутні об\'єкти", 
                        item_tool_tip = f"В шарі {self.layer_props['layer_real_name']} відсутні об\'єкти", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                    )
            else:
                insception_layer_is_empty = self.create_inspection_dict(                    
                        inspection_type_name = 'Перевірка на наявність об’єктів в шарі', #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"В шарі {self.layer_props['layer_name']} наявні об\'єкти", 
                        item_tool_tip = f"В шарі {self.layer_props['layer_real_name']} наявні об\'єкти", 
                        criticity = 0, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                    )
        
            self.check_result_dict['subitems'].append(insception_layer_is_empty)
            
            self.parse_bench.stop()
            # self.check_result_legacy[self.layer_props['related_layer_id']] = {}
            # self.check_result_legacy[self.layer_props['related_layer_id']]["is_empty"] = layer_is_empty
            
            if self.layer_EDRA_valid_class.nameError:
                self.parse_bench.start('check_layer_nameError')
                
                layer_name_errors_check_result = self.layer_EDRA_valid_class.check_text_in_objects_list(self.layer_EDRA_valid_class.layer_exchange_name, 'layer')

                if layer_name_errors_check_result['any_similar_name']:
                    
                    container_layer_error_name = None
                    container_layer_error_name = {}
                    container_layer_error_name['type'] = 'container'
                    container_layer_error_name['item_name'] = "Перевірка на наявність помилок в назві шару"
                    container_layer_error_name['subitems'] = []
                    
                    if len(layer_name_errors_check_result['result_dict'].keys()) > 0:
                        for x in layer_name_errors_check_result['result_dict']:
                            
                            if [x] == "general":
                                insception_dict_layer_error_name_general = None
                                insception_dict_layer_error_name_general = self.create_inspection_dict(                    
                                    inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                                    item_name = f"Назва класу «{self.layer_props['layer_real_name']}» не відповідає структурі", 
                                    item_tool_tip = f"Назва класу не відповідає структурі", 
                                    criticity = 2, 
                                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                                )
                                container_layer_error_name['subitems'].append(insception_dict_layer_error_name_general)
                                del insception_dict_layer_error_name_general
                            
                            if [x] == "used_alias":
                                insception_dict_layer_error_name_used_alias = None
                                insception_dict_layer_error_name_used_alias = self.create_inspection_dict(                    
                                    inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                                    item_name = f"Замість назви класу використано псевдонім «{self.layer_props['layer_real_name']}», вимагається «{layer_name_errors_check_result['result_dict']['valid_name']}»", 
                                    item_tool_tip = f"Замість назви класу використано псевдонім»", 
                                    criticity = 2, 
                                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                                )
                                container_layer_error_name['subitems'].append(insception_dict_layer_error_name_used_alias)
                                del insception_dict_layer_error_name_used_alias
                            
                            if [x] == "spaces_used":
                                insception_dict_layer_error_name_spaces_used = None
                                insception_dict_layer_error_name_spaces_used = self.create_inspection_dict(                    
                                    inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                                    item_name = f"В назві класу «{self.layer_props['layer_real_name']}» наявні пробіли", 
                                    item_tool_tip = f"В назві класу наявні пробіли", 
                                    criticity = 2, 
                                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                                )
                                container_layer_error_name['subitems'].append(insception_dict_layer_error_name_spaces_used)
                                del insception_dict_layer_error_name_spaces_used
                            
                            if [x] == "used_cyrillic":
                                insception_dict_layer_error_name_used_cyrillic = None
                                insception_dict_layer_error_name_used_cyrillic = self.create_inspection_dict(                    
                                    inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                                    item_name = f"В назві класу «{self.layer_props['layer_real_name']}» наявні кириличні літери", 
                                    item_tool_tip = f"В назві класу наявні кириличні літери", 
                                    criticity = 2, 
                                    help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                                )
                                container_layer_error_name['subitems'].append(insception_dict_layer_error_name_used_cyrillic)
                                del insception_dict_layer_error_name_used_cyrillic
                                

                    elif len(layer_name_errors_check_result['result_dict'].keys()) == 0:
                        insception_dict_layer_no_error_name = None
                        insception_dict_layer_no_error_name = self.create_inspection_dict(                    
                            inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                            item_name = f"Назва класу «{self.layer_props['layer_real_name']}» відповідає структурі", 
                            item_tool_tip = f"Назва класу відповідає структурі", 
                            criticity = 0, 
                            help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                        )
                        container_layer_error_name['subitems'].append(insception_dict_layer_no_error_name)
                        del insception_dict_layer_no_error_name

                    self.check_result_dict['subitems'].append(container_layer_error_name)
                    del container_layer_error_name
                    
                    self.parse_bench.stop()
                    
                    
                    self.parse_bench.start('reinit_class')
                    self.layer_EDRA_valid_class = EDRA_validator(self.layer_EDRA_valid_class.layer, layer_name_errors_check_result['result_dict']['valid_name'], self.layer_EDRA_valid_class.structure_json, self.layer_EDRA_valid_class.domains_json)
                    # self.check_result_legacy[self.layer_props['related_layer_id']]['layer_name_errors'] = layer_name_errors_check_result['result_dict']
                    self.parse_bench.stop()
                    
                    
                    self.parse_bench.start('write_result_dict_error_name')
                    
                    self.write_result_dict()
                    
                    self.parse_bench.stop()
                else: 
                    insception_dict_layer_error_name_else = None
                    insception_dict_layer_error_name_else = self.create_inspection_dict(                    
                        inspection_type_name = 'Перевірка імені шару', #Підтягувати перевірку з файлу структури з помилками
                        item_name = f"Назва класу «{self.layer_props['layer_real_name']}» не відповідає структурі", 
                        item_tool_tip = f"Назва класу не відповідає структурі", 
                        criticity = 2, 
                        help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
                    )
                    
                    self.check_result_dict['subitems'].append(insception_dict_layer_error_name_else)
                    del insception_dict_layer_error_name_else
                    
                del layer_name_errors_check_result
                    # self.check_result_legacy[self.layer_props['related_layer_id']]['layer_name_errors'] = layer_name_errors_check_result['result_dict']
                # self.check_result_dict[self.layer_props['related_layer_id']]['layer_name_errors']["general"] = [True,"Посилання на сторінку хелпу з переліком атрибутів"]
                
            else:
                
                self.parse_bench.start('write_result_dict_without_error_name')
                
                self.write_result_dict()
                
                self.parse_bench.stop()
            
            
            
        
        else:
            self.parse_bench.start('layer_invalid')
            
            insception_layer_valid_dict = None
            insception_layer_valid_dict = self.create_inspection_dict(                    
                inspection_type_name = 'Перевірка валідності шару', #Підтягувати перевірку з файлу структури з помилками
                item_name = f"Шар {self.layer_props['layer_name']} не валідний. GDAL не може зчитати шар", 
                item_tool_tip = f"Шар {self.layer_props['layer_real_name']}  не валідний.", 
                criticity = 2, 
                help_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D' #Rickroll
            )

            #Альтернативне посилання https://www.youtube.com/watch?v=asjQNZn7vng #Гендальф
            self.check_result_dict['subitems'].append(insception_layer_valid_dict)
            del insception_layer_valid_dict
            
            self.parse_bench.stop()
            # self.check_result_legacy[self.layer_props['layer_name']]['layer_invalid'] = True
        
        self.parse_bench.start('del_self_layer_EDRA_valid_class')
        
        del self.layer_EDRA_valid_class 
        
        self.parse_bench.stop()
        
        if self.write_result_dict_bench is not None:
            self.parse_bench.join(self.write_result_dict_bench)
        

        print(f"Завершення перевірки шару {self.layer_props['layer_name']}..... Done")
        print(self.parse_bench.get_report())
        print("end")

        return self.check_result_dict

        







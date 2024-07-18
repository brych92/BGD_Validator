import json, os

from osgeo import ogr

from qgis.core import QgsProviderRegistry

# Можливі помилки
# Об'єкт з id "0" має помилку: "segments 142 and 229 of line 0 intersect at 33.5424, 48.2325"
# value is not unique'


class EDRA_validator:
    
    def __init__(self, layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json):
    
        # super().__init__()
        self.id_field_layer_dict = {'settlement': 'katottg', 'buildings_polygon': 'build_code', 'streets': 'str_id'}
        self.layer = layer
        self.layerDefinition = self.layer.GetLayerDefn()
        self.layer_exchange_group = layer_exchange_group
        self.layer_exchange_name = layer_exchange_name
        self.layer_field_names = [self.layerDefinition.GetFieldDefn(i).GetName() for i in range(self.layerDefinition.GetFieldCount())]
        self.structure_json = structure_json
        self.domains_json = domains_json
        if layer_exchange_name in structure_json[layer_exchange_group]:
            self.structure_field_names = structure_json[layer_exchange_group][layer_exchange_name]['attributes'].keys()
            self.fields_structure_json = structure_json[layer_exchange_group][layer_exchange_name]['attributes']
            self.required_geometry_type = structure_json[layer_exchange_group][layer_exchange_name]['geometry_type']
            self.structure_field_meta_types = {"text":[10], "integer":[2, 4], "double precision":[6]}
            self.id_field = self.id_field_layer_dict[self.layer_exchange_name]
            self.nameError = False
        else:
            self.structure_field_names = None
            self.fields_structure_json = None
            self.required_geometry_type = None
            self.structure_field_meta_types = None
            self.id_field = None
            self.nameError = True

        
        
        self.qt_and_ogr_data_types = {'Integer': {'ogr_code': 0, 'qt_code': 2}, 'Real': {'ogr_code': 2, 'qt_code': 6}, 'String': {'ogr_code': 4, 'qt_code': 10}, 'Date': {'ogr_code': 9, 'qt_code': 14}, 'Time': {'ogr_code': 10, 'qt_code': 15}, 'DateTime': {'ogr_code': 11, 'qt_code': 16}, 'Binary': {'ogr_code': 15, 'qt_code': None}, 'IntegerList': {'ogr_code': 16, 'qt_code': None}, 'RealList': {'ogr_code': 17, 'qt_code': None}, 'StringList': {'ogr_code': 18, 'qt_code': 0}}

        


    def get_required_fields_names(self):
        required_field_names_list = []
        for x in self.structure_field_names:
            if self.fields_structure_json[x]['attribute_required'] == 'True':
                required_field_names_list.append(x)
            else: pass
        return required_field_names_list
    
    
    def get_unique_fields_names(self):
        unique_field_names_list = []
        for x in self.structure_field_names:
            if self.fields_structure_json[x]['attribute_unique'] == 'True':
                unique_field_names_list.append(x)
            else: pass
        return unique_field_names_list
                
                
    def compare_object_geometry_type(self, checking_object_geometry_type, required_geometry_type):
        try:
            if required_geometry_type in checking_object_geometry_type:
                return True
            else:
                return False
        except Exception as e:
            print(f'В функції check_object_geometry_type виникла помилка: "{e}"')
            return False
    

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
    

    def check_fields_type_and_names(self):
        list_check_fields: list[dict] = []
        
        for i in range(self.layerDefinition.GetFieldCount()):
            field_name = self.layerDefinition.GetFieldDefn(i).GetName()
            field_type_name = self.layerDefinition.GetFieldDefn(i).GetTypeName()
            
            if field_name in self.structure_field_names:
                
                check_field_name_result = field_name in self.structure_field_names
                check_field_type_result = field_type_name in self.structure_field_meta_types[self.fields_structure_json[field_name]['attribute_type']]
                #print(self.structure_field_meta_types[self.fields_structure_json[field_name]['attribute_type']])
                list_check_fields.append({"current_field_name": field_name, "check_field_type_result": check_field_type_result, "current_field_type": field_type_name, "check_field_name_result": check_field_name_result, "required_field_type": self.structure_field_meta_types[self.fields_structure_json[field_name]['attribute_type']]})
            else:
                list_check_fields.append({"current_field_name": field_name, "check_field_type_result": False, "current_field_type": field_type_name, "check_field_name_result": False, "required_field_type": None})
        
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
                    self.layer.setFieldConstraint(layer.fields().indexOf(x['current_field_name']), ConstraintNotNull, ConstraintStrengthHard)
                if self.fields_structure_json[x['current_field_name']]['attribute_unique'] == 'unique':
                    self.layer.setFieldConstraint(layer.fields().indexOf(x['current_field_name']), ConstraintUnique, ConstraintStrengthHard)


    def check_feature_geometry(self, feature):
        
        feature_geometry = feature.geometry()
        geometry_type_check_result = self.check_object_geometry_type(feature_geometry, self.required_geometry_type)
        
        return {"geometry_type_check_result": {"current_type": QgsWkbTypes().displayString(feature_geometry.wkbType()), "required_type": self.required_geometry_type, "check_result":geometry_type_check_result}, "isEmpty":feature_geometry.isEmpty(), "isValid":feature_geometry.validateGeometry()}
    
    
    def check_feature_attributes(self, feature):
        
        attr_validate_result_list = []
        for field in feature.fields():
            attr_validate_result = QgsVectorLayerUtils.validateAttribute(layer, feature, feature.fields().indexOf(field.name()), 1, 0), 
            attr_validate_result_list.append({field.name(): attr_validate_result})
            
        return attr_validate_result_list
    
    
    def check_feature_req_attrs_is_empty(self, feature):
        
        req_attrs_is_empty_result_list = []
        
        for field in feature.fields():
            if field.name() in self.fields_structure_json.keys():
                if self.fields_structure_json[field.name()]['attribute_required'] == 'True':
                    if feature[field.name()] == '' or feature[field.name()] == None:
                        req_attrs_is_empty_result_list.append({field.name(): True})
                    else:
                        req_attrs_is_empty_result_list.append({field.name(): False})
                else: pass
                    
        return req_attrs_is_empty_result_list

    
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

    def check_attr_value_in_domain(self, feature, field_name):

        if field_name in self.fields_structure_json.keys():
            if self.fields_structure_json[field_name]['domain'] != '' and self.fields_structure_json[field_name]['domain'] != None:
                domain_codes = self.domains_json[self.fields_structure_json[field_name]['domain']]['codes']
            else:
                domain_codes = []
        else: domain_codes = []
        
        return feature[field_name] in domain_codes

class EDRA_exchange_layer_checker:
    def __init__(self, layer_EDRA_valid_class: EDRA_validator, layer_props: dict, layer_id: str):
        
        self.layer_EDRA_valid_class = layer_EDRA_valid_class
        self.layer_props = layer_props
        self.check_result_dict = {}
        self.layer_id = layer_id
        
    def check_is_layer_empty(self):
        if self.layer_EDRA_valid_class.layer.GetFeatureCount() < 0:
            return True
        else:
            return False

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
        
    def check_wrong_layer_geometry_type(self):
        # feature_geometry = feature.geometry()
        geometry_type_check_result = self.layer_EDRA_valid_class.compare_object_geometry_type(ogr.GeometryTypeToName(self.layer_EDRA_valid_class.layer.GetGeomType()), self.layer_EDRA_valid_class.required_geometry_type)
        
        if not geometry_type_check_result:
            return [ogr.GeometryTypeToName(self.layer_EDRA_valid_class.layer.GetGeomType()), self.layer_EDRA_valid_class.required_geometry_type]
        else:
            return []
            # self.check_result_dict['missing required fields'] = [QgsWkbTypes().displayString(layer.wkbType(), self.layer_EDRA_valid_class.check_extra_fields())]

    def check_wrong_fields_types(self):
        # {"current_field_name": x.name(), "check_field_type_result": check_field_type_result, "current_field_type": x.type(), "check_field_name_result": check_field_name_result, "required_field_type": self.structure_field_meta_types[self.fields_structure_json[x.name()]['attribute_type']]}
        
        error_field_type_list = []
        for x in self.fields_check_results_list:
            if x['check_field_type_result'] == False and x['check_field_name_result'] == True:
                error_field_type_list.append({x['current_field_name']:[x['current_field_type'], x['required_field_type']]})
            else: pass
        
        return error_field_type_list    
                # self.check_result_dict['wrong feild type'] = {}
                # self.check_result_dict['wrong feild type'][x['current_field_name']] = [ x['current_field_type'], x['required_field_type'] ]

    def set_fields_constraints(self):
        if len(self.fields_check_results_list) > 0:
            self.layer_EDRA_valid_class.set_fields_constraints(self.fields_check_results_list)
            # return True
        else:
            print('Жодне поле не пройшло перевірку на назву та тип, тому обмеження не можуть бути встановлені')
            
    
    def write_features_check_result(self):
        features_dict = {}
        
        for feature in self.layer_EDRA_valid_class.layer:
            features_dict[feature.GetFID()] = {'geometry_errors':
                                                {"empty" : True,
                                                "null" : False,
                                                "geometry_type_wrong" : [1,1]}}
        #print(features_dict)
        return features_dict
            
    def run(self):
        self.check_result_dict[self.layer_props['layer_name']] = {}
        # if (checker_layer_empty):      

        self.check_result_dict[self.layer_props['layer_name']]['is_empty'] = self.check_is_layer_empty()
        self.check_result_dict[self.layer_props['layer_name']]['layer_id'] = self.layer_id
        
        if self.layer_EDRA_valid_class.nameError:
            self.check_result_dict[self.layer_props['layer_name']]['layer_name_errors'] = {}
            self.check_result_dict[self.layer_props['layer_name']]['layer_name_errors']["general"] = [True,"Посилання на сторінку хелпу з переліком атрибутів"]
        
        else:
            self.fields_check_results_list = self.layer_EDRA_valid_class.check_fields_type_and_names()

            self.check_result_dict[self.layer_props['layer_name']]['layer_name_errors'] = {}
            self.check_result_dict[self.layer_props['layer_name']]['field_errors'] = {}
            self.check_result_dict[self.layer_props['layer_name']]['field_errors'] ['missing_required_fields'] = self.check_missing_required_fields()
            self.check_result_dict[self.layer_props['layer_name']]['field_errors'] ['missing_fields'] = self.check_missing_fields()
            #self.check_result_dict[self.layer_props['name']] ['field_errors']['wrong_field_type'] = self.check_wrong_fields_types()
            #self.check_result_dict[layer_EDRA_valid_class.layer.name()] ['wrong_layer_CRS'] = []
            self.check_result_dict[self.layer_props['layer_name']]['wrong_geometry_type'] = self.check_wrong_layer_geometry_type()
            self.check_result_dict[self.layer_props['layer_name']]['features'] = self.write_features_check_result()
        
        return self.check_result_dict
        






from qgis.core import QgsVectorLayer, QgsVectorFileWriter

def get_real_layer_name(layer):
    if layer.providerType() == "postgres":
        uri = layer.dataProvider().uri()
        source_layer_name = uri.table()
        source_layer_name = source_layer_name.strip("''")
    elif layer.providerType() == "ogr":
        uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        if uri_components["layerName"]:
            source_layer_name = uri_components["layerName"]
        else:
            directory, filename_with_extension = os.path.split(uri_components["path"])
            source_layer_name, extension = os.path.splitext(filename_with_extension)
    else:
        raise Error("Не зміг визначити імя джерела для шару {layer.name()}")
        source_layer_name = ''
        
    return source_layer_name




def get_layer_list_for_validator(selected_layers):
    layers_dict = {}
    for layer in selected_layers:
        # print(type(x))
        uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        
        path_to_layer = uri_components['path']
        
        layer_name = layer.name()#get_real_layer_name(layer)
        print(f'Назва {layer_name} {path_to_layer}')
        driver_name = layer.dataProvider().storageType()
        
        layers_dict[layer.id()] = {'layer_name': layer_name, 'path': path_to_layer, 'driver_name': driver_name} 
        
    return layers_dict

def get_json_info_files(structure_bgd_file_path, domains_bgd_file_path):
    
    with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
        structure_json = json.loads(f.read())
        
    with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
        domains_json = json.loads(f.read())
        
    
        
def run_validator(layers_dict):
    all_layers_check_result_dict = {}
    all_layers_check_result_dict['layers'] = {}
    all_layers_check_result_dict['exchange_format_error'] = []
    all_layers_check_result_dict['missing_layers'] = []
    
    for layer_id in layers_dict:
        driver = ogr.GetDriverByName(layers_dict[layer_id]['driver_name'])
        dataSource = driver.Open(layers_dict[layer_id]['path'], 0) # 0 means read-only. 1 means writeable.

        layer = dataSource.GetLayer()
        
        layer_exchange_group = 'EDRA'
        layer_exchange_name = layers_dict[layer_id]['layer_name']
        
        
        structure_bgd_file_path = 'C:/Users/brych/OneDrive/Документы/01 Робота/98 Сторонні проекти/ua mbd team/Плагіни/Перевірка на МБД/BGD_Validator/EDRA_structure/structure_bgd3.json'
        domains_bgd_file_path = r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator\EDRA_structure\structure_bgd3.json'
        
        with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
            structure_json = json.loads(f.read())
        
        with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
            domains_json = json.loads(f.read())
            
        if layer is not None:
            layer_EDRA_valid_class = EDRA_validator(layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json)
        
        

        validate_checker = EDRA_exchange_layer_checker(layer_EDRA_valid_class, layers_dict[layer_id], layer_id)
        validate_result = validate_checker.run()
        
        all_layers_check_result_dict['layers'][list(validate_result.keys())[0]] = validate_result[list(validate_result.keys())[0]]
        
    return all_layers_check_result_dict
        
        
#selected_layers = iface.layerTreeView().selectedLayersRecursive()

#print(run_validator(get_layer_list_for_validator(selected_layers)))
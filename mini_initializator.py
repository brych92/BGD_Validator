import json 


from osgeo import ogr


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








domains_bgd_file_path = '/home/bohdan/Programming/ПЛАГІН/domain.json'
structure_bgd_file_path = r'/home/bohdan/Programming/ПЛАГІН/structure_bgd3.json'
        
with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
    structure_json = json.loads(f.read())
        
with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
    domains_json = json.loads(f.read())


layer_exchange_group = 'EDRA'

path_to_layer = '/home/bohdan/Programming/ПЛАГІН/buildings_polygon.geojson'


driver = ogr.GetDriverByName('GeoJSON')
dataSource = driver.Open(path_to_layer, 0) # 0 means read-only. 1 means writeable.

layer = dataSource.GetLayer()

layer_exchange_name = 'buildings_polygon'
    
layer_EDRA_valid_class = EDRA_validator(layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json)
         
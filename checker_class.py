import json

from osgeo import ogr

# Можливі помилки
# Об'єкт з id "0" має помилку: "segments 142 and 229 of line 0 intersect at 33.5424, 48.2325"
# value is not unique'


class EDRA_validator:
    
    def __init__(self, layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json):
        try:
            # super().__init__()
            self.id_field_layer_dict = {'settlement': 'katottg', 'buildings_polygon': 'build_code', 'streets': 'str_id'}
            self.layer = layer
            self.layerDefinition = self.layer.GetLayerDefn()
            self.layer_exchange_group = layer_exchange_group
            self.layer_exchange_name = layer_exchange_name
            self.layer_field_names = [self.layerDefinition.GetFieldDefn(i).GetName() for i in range(self.layerDefinition.GetFieldCount())]
            self.structure_json = structure_json
            self.domains_json = domains_json
            self.structure_field_names = structure_json[layer_exchange_group][layer_exchange_name]['attributes'].keys()
            self.fields_structure_json = structure_json[layer_exchange_group][layer_exchange_name]['attributes']
            self.required_geometry_type = structure_json[layer_exchange_group][layer_exchange_name]['geometry_type']
            self.structure_field_meta_types = {"text":[10], "integer":[2, 4], "double precision":[6]}

            self.id_field = self.id_field_layer_dict[self.layer_exchange_name]

        except Exception as e:
            print(f'error {str(e)}')


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

path_to_geojson_file = '/home/bohdan/Programming/ПЛАГІН/Рядове межа (копія).geojson'

driver = ogr.GetDriverByName('GeoJSON')

dataSource = driver.Open(path_to_geojson_file, 0) # 0 means read-only. 1 means writeable.

layer = dataSource.GetLayer()


structure_bgd_file_path = '/home/bohdan/Робота/ЄДЕССБ/ПЛАГІН/structure_bgd3.json'
with open(structure_bgd_file_path, 'r', encoding='utf-8') as f: 
    structure_json = json.loads(f.read())
    
domains_bgd_file_path = '/home/bohdan/Робота/ЄДЕССБ/ПЛАГІН/domain.json'
with open(domains_bgd_file_path, 'r', encoding='utf-8') as f: 
    domains_json = json.loads(f.read())
    
layer_exchange_group = 'EDRA'
layer_exchange_name = 'settlement'

if layer.isValid:
    layer_EDRA_valid_class = EDRA_validator(layer, layer_exchange_group, layer_exchange_name, structure_json, domains_json)

class EDRA_exchange_layer_checker:
    def __init__(self, layer_EDRA_valid_class: EDRA_validator):
        
        self.layer_EDRA_valid_class = layer_EDRA_valid_class
        self.check_result_dict = {}
        self.fields_check_results_list = layer_EDRA_valid_class.check_fields_type_and_names()
        
    def check_is_layer_empty(self):
        if len(layer_EDRA_valid_class.layer.GetFeatureCount()) > 0:
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
        geometry_type_check_result = layer_EDRA_valid_class.compare_object_geometry_type(ogr.GeometryTypeToName(layer_EDRA_valid_class.layer.GetGeomType()), layer_EDRA_valid_class.required_geometry_type)
        
        if not geometry_type_check_result:
            return [ogr.GeometryTypeToName(layer_EDRA_valid_class.layer.GetGeomType()), layer_EDRA_valid_class.required_geometry_type]
            # self.check_result_dict['missing required fields'] = [QgsWkbTypes().displayString(layer.wkbType(), self.layer_EDRA_valid_class.check_extra_fields())]

    def check_wrong_fields_types(self):
        # {"current_field_name": x.name(), "check_field_type_result": check_field_type_result, "current_field_type": x.type(), "check_field_name_result": check_field_name_result, "required_field_type": self.structure_field_meta_types[self.fields_structure_json[x.name()]['attribute_type']]}
        
        error_field_type_list = []
        for x in self.fields_check_results_list:
            if x['check_field_type_result'] == False and x['check_field_name_result'] == True:
                error_field_type_list.append({x.current_field_name:[x.current_field_type, x.required_field_type]})
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
            
    # def write_features_check_result(self):
    #     self.check_result_dict['features'] = {}
    def run(self):
        self.check_result_dict['LAYER_NAME'] = {}
        # if (checker_layer_empty):
        self.check_result_dict['is_empty'] = self.check_is_layer_empty()
        #
        self.check_result_dict['missing_required_fields'] = self.check_missing_required_fields()
        
        self.check_result_dict['missing_fields'] = self.check_missing_fields()
        
        self.check_result_dict['wrong_geometry_type'] = self.check_wrong_layer_geometry_type()
        
        self.check_result_dict['wrong_field_type'] = self.check_wrong_fields_types()
        
        return self.check_result_dict
        
b = EDRA_exchange_layer_checker(layer_EDRA_valid_class)
print(b.run())






import json
import copy
from osgeo import ogr

# Можливі помилки
# Об'єкт з id "0" має помилку: "segments 142 and 229 of line 0 intersect at 33.5424, 48.2325"
# value is not unique'


class EDRA_validator:
    
    def __init__(self, layer, layer_exchange_name, structure_json, domains_json):

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
        if layer_exchange_name in structure_json:
            self.structure_field_names = structure_json[layer_exchange_name]['attributes'].keys()
            self.fields_structure_json = structure_json[layer_exchange_name]['attributes']
            self.required_geometry_type = structure_json[layer_exchange_name]['geometry_type']
            self.qt_and_ogr_data_types = {'integer': {'ogr_code': 0, 'qt_code': 2}, 
                                    'double precision': {'ogr_code': 2, 'qt_code': 6}, 'text': {'ogr_code': 4, 'qt_code': 10}, 
                                    'Date': {'ogr_code': 9, 'qt_code': 14}, 'Time': {'ogr_code': 10, 'qt_code': 15}, 
                                    'DateTime': {'ogr_code': 11, 'qt_code': 16}, 'Binary': {'ogr_code': 15, 'qt_code': None}, 
                                    'IntegerList': {'ogr_code': 16, 'qt_code': None}, 'RealList': {'ogr_code': 17, 'qt_code': None}, 
                                    'StringList': {'ogr_code': 18, 'qt_code': 0}}
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


    def get_required_fields_names(self):
        required_field_names_list = []
        for x in self.structure_field_names:
            if self.fields_structure_json[x]['attribute_required'] == 'True':
                required_field_names_list.append(x)
            else: pass
        return required_field_names_list
    
    def check_feature_geometry_is_empty(self, feature):
        if self.check_feature_geometry_is_null(feature) == True:
            if feature.geometry().IsEmpty():
                return True
            else:
                return False
        else:
            return False
    
    def check_feature_geometry_is_null(self, feature):
        if feature.GetGeometryRef() == None:
            return True
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
    

    def check_fields_type_and_names(self, checker_object):
        list_check_fields: list[dict] = []
        
        for i in range(checker_object.GetFieldCount()):
            current_field_name = self.layerDefinition.GetFieldDefn(i).GetName()
            current_field_type_name = self.layerDefinition.GetFieldDefn(i).GetTypeName()
            required_field_type_name = self.fields_structure_json[current_field_name]['attribute_type']
            required_field_type_number = self.qt_and_ogr_data_types[required_field_type_name]['ogr_code']
            
            if current_field_name in self.structure_field_names:
                
                check_field_name_result = current_field_name in self.structure_field_names
                check_field_type_result = current_field_type_name in ogr.GetFieldTypeName(required_field_type_number)
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
        
        req_attrs_is_empty_result_list = {}
        
        for i in range(feature.GetFieldCount()):
            field_name = feature.GetFieldDefnRef(i).GetNameRef()
            if field_name in self.fields_structure_json.keys():
                if self.fields_structure_json[field_name]['attribute_required'] == 'True':
                    if feature[field_name] == '' or feature[field_name] == None:
                        req_attrs_is_empty_result_list[field_name] = True
                    else:
                        req_attrs_is_empty_result_list[field_name] = False
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

    def get_list_duplicated_fid(self, feature, layer_id, feature_fids):
            duplicated_id_list = []
            for id, fid in feature_fids.items():
                if fid == feature[self.id_field] and id != feature.GetFID():
                    duplicated_id_list.append([id, layer_id])
            return duplicated_id_list
        
    
    def check_attr_value_in_domain(self, feature, field_name):        
            
        domain_codes = self.domains_json[self.fields_structure_json[field_name]['domain']]['codes']
            
        return feature[field_name] in domain_codes
    
    def get_layer_crs(self):
        srs = self.layer.GetSpatialRef()
        auth_name = str(srs.GetAuthorityName('GEOGCS'))
        auth_code = str(srs.GetAuthorityCode('GEOGCS'))
        return f'{auth_name}:{auth_code}'
                    
        
        
    


class EDRA_exchange_layer_checker:
    def __init__(self, layer_EDRA_valid_class: EDRA_validator, layer_props: dict, layer_id: str):
        
        self.layer_EDRA_valid_class = layer_EDRA_valid_class
        self.layer_props = layer_props
        self.check_result_dict = {}
        self.layer_id = layer_id
        self.layer_props['layer_id'] = layer_id

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
            return [ogr.GeometryTypeToName(geom_type), self.layer_EDRA_valid_class.required_geometry_type]
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
            
    def check_required_fields_is_empty(self, feature):
        check_required_fields_is_empty_result = self.layer_EDRA_valid_class.check_feature_req_attrs_is_empty(feature)
        empty_required_fields_list = []
        if check_required_fields_is_empty_result:
            for x in check_required_fields_is_empty_result:
                if check_required_fields_is_empty_result[x]:
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
                    check_is_value_in_domain = self.layer_EDRA_valid_class.check_attr_value_in_domain(feature, field_name) 
                    
                    if not check_is_value_in_domain:
                        result_dict[field_name] =  [feature[field_name], 'Посилання до домену']
                    else:
                        result_dict[field_name] = []   
                
                else:
                    continue
            else:
                continue
                
        return result_dict
    
    def write_features_check_result(self):
        features_dict = {}
        
        features_fids = {}
        for feature in self.layer_EDRA_valid_class.layer:
            features_fids[feature.GetFID()] = feature[self.layer_EDRA_valid_class.id_field]

        
        for feature in self.layer_EDRA_valid_class.layer:
            features_dict[feature.GetFID()] = {
                'geometry_errors':
                    {"empty" : self.layer_EDRA_valid_class.check_feature_geometry_is_empty(feature),
                    "null" : self.layer_EDRA_valid_class.check_feature_geometry_is_null(feature),
                    "geometry_type_wrong" : self.check_wrong_object_geometry_type(feature)},
                "required_attribute_empty": self.check_required_fields_is_empty(feature),
                "attribute_value_unclassifyed": self.check_attr_value_in_domain(feature),
                "duplicated_GUID": self.layer_EDRA_valid_class.get_list_duplicated_fid(feature, self.layer_props['layer_id'], features_fids)
                }
            
            
        #print(features_dict)
        return features_dict
            
    def run(self):
        self.check_result_dict[self.layer_props['layer_id']] = {}
        self.check_result_dict[self.layer_props['layer_id']]['layer_name'] = self.layer_props['layer_name']
        self.check_result_dict[self.layer_props['layer_id']]['layer_real_name'] = self.layer_props['layer_real_name']
        # if (checker_layer_empty):  
        
            
        if self.layer_EDRA_valid_class.layer is not None:
            self.check_result_dict[self.layer_props['layer_id']]['is_empty'] = self.layer_EDRA_valid_class.get_is_layer_empty()
            
            
            if self.layer_EDRA_valid_class.nameError:
                self.check_result_dict[self.layer_props['layer_id']]['layer_name_errors'] = {}
                self.check_result_dict[self.layer_props['layer_id']]['layer_name_errors']["general"] = [True,"Посилання на сторінку хелпу з переліком атрибутів"]
                
            else:
                self.fields_check_results_list = self.layer_EDRA_valid_class.check_fields_type_and_names(self.layer_EDRA_valid_class.layerDefinition)
                
                
                self.check_result_dict[self.layer_props['layer_id']]['wrong_layer_CRS'] = self.check_crs_is_equal_required()
                self.check_result_dict[self.layer_props['layer_id']]['layer_name_errors'] = {}
                self.check_result_dict[self.layer_props['layer_id']]['field_errors'] = {}
                self.check_result_dict[self.layer_props['layer_id']]['field_errors']['missing_required_fields'] = self.check_missing_required_fields()
                self.check_result_dict[self.layer_props['layer_id']]['field_errors']['missing_fields'] = self.check_missing_fields()
                self.check_result_dict[self.layer_props['layer_id']]['field_errors']['wrong_field_type'] = self.check_wrong_fields_types()
                #self.check_result_dict[layer_EDRA_valid_class.layer.name()] ['wrong_layer_CRS'] = []
                self.check_result_dict[self.layer_props['layer_id']]['wrong_geometry_type'] = self.check_wrong_object_geometry_type(self.layer_EDRA_valid_class.layer)
                self.check_result_dict[self.layer_props['layer_id']]['features'] = self.write_features_check_result()
            
            return self.check_result_dict
        
        else:
            self.check_result_dict[self.layer_props['layer_name']]['layer_invalid'] = True

        







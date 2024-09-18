import json
import csv

inputCsvFilePath = 'structure.csv'
outputJsonFilePath = 'structure_bgd3.json'

def csv_to_json_data(inputCsvFilePath):
    jsonArray = []
      
    #read csv file
    with open(inputCsvFilePath, encoding='utf-8') as csvf: 
        #load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf) 

        #convert each csv row into python dict
        for row in csvReader: 
            #add this python dict to json array
            jsonArray.append(row)
  
    #convert python jsonArray to JSON String and write to file
    structure_bgd = jsonArray
    
    return structure_bgd

def create_structure_json_file(structure_bgd, outputJsonFilePath):
    # print(structure_bgd)
    classes = set()
    layers_names_en = set()
    layers_names_ua = set()

    for x in structure_bgd:
        classes.add(x['class'])
        layers_names_en.add(x['layer_name_en'])
        layers_names_ua.add(x['layer_name_ua'])
        
    # print(layers_names_en)

    classes_with_layers_dict = {}
    for x in classes:
        classes_with_layers_dict[x] = {}
        
    # print(classes_with_layers_dict)

    for x in structure_bgd:
        for y in classes_with_layers_dict:
            # print(y)
            if x['class'] in classes_with_layers_dict.keys():
                if x['layer_name_en'] not in classes_with_layers_dict[x['class']]:
                    classes_with_layers_dict[x['class']][x['layer_name_en']] = {}

    for x in structure_bgd:
        for y in classes_with_layers_dict:
            # for i in y:

                for k in classes_with_layers_dict[y]:
                    if x['layer_name_en'] == k:
                        if 'geometry_type' not in classes_with_layers_dict[y][k]:

                            classes_with_layers_dict[y][k]['geometry_type'] = x['geometry_type']
                            classes_with_layers_dict[y][k]['layer_name_ua'] = x['layer_name_ua']
                        

                        if 'attributes' not in classes_with_layers_dict[y][k]:
                            # print(x['attribute_name_en'])
                            classes_with_layers_dict[y][k]['attributes'] = {}
                            classes_with_layers_dict[y][k]['attributes'][x['attribute_name_en']] = {
                                'attribute_name_ua': x['attribute_name_ua'],
                                "attribute_type": x['attribute_type'],
                                "attribute_required": x['attribute_required'],
                                "attribute_len": x['attribute_len'],
                                "attribute_default_value": x['attribute_default_value'],
                                "attribute_unique" : x['attribute_unique'],
                                "domain" : x['domain']
                                }
                        elif 'attributes' in classes_with_layers_dict[y][k]:
                            # print(x['attribute_name_en'])
                            classes_with_layers_dict[y][k]['attributes'][x['attribute_name_en']] = {
                                'attribute_name_ua': x['attribute_name_ua'],
                                "attribute_type": x['attribute_type'],
                                "attribute_required": x['attribute_required'],
                                "attribute_len": x['attribute_len'],
                                "attribute_default_value": x['attribute_default_value'],
                                "attribute_unique" : x['attribute_unique'],
                                "domain" : x['domain']
                                }
                            

    # print(classes_with_layers_dict)

    # import json 
    with open(outputJsonFilePath, 'w', encoding='utf-8') as jsonf: 
            jsonString = json.dumps(classes_with_layers_dict, indent=4)
            jsonf.write(jsonString)

structure_bgd = csv_to_json_data(inputCsvFilePath)
# print(type(structure_bgd))
if structure_bgd != False:
    create_structure_json_file(structure_bgd, outputJsonFilePath)

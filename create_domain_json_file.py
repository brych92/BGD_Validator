import json
import csv

inputCsvFilePath = 'domain.csv'
outputJsonFilePath = 'domain.json'

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
    domains_structure = jsonArray
    
    return domains_structure

def create_structure_json_file(domains_structure, outputJsonFilePath):
    
    domains_names_en = set()

    for x in domains_structure:
        domains_names_en.add(x['name_eng'])

    domain_with_codes_dict = {}
    for x in domains_names_en:
        domain_with_codes_dict[x] = {}
        domain_with_codes_dict[x]['codes'] = {}
        domain_with_codes_dict[x]['name_ukr'] = {}
    
    for x in domains_structure:
        
         for y in domain_with_codes_dict:
             # print(type(y))
             if x['name_eng'] == y:
                 if x['code'] not in domain_with_codes_dict[y]['codes']:
                    domain_with_codes_dict[y]['codes'][x['code']] = x['value']
                    domain_with_codes_dict[y]['name_ukr'] = x['name_ukr']
                    print(type(domain_with_codes_dict[y]['codes'][x['code']]))
                    # print(type(domain_with_codes_dict[y]['name_ukr']))
                 else: pass

    with open(outputJsonFilePath, 'w', encoding='utf-8') as jsonf: 
            jsonString = json.dumps(domain_with_codes_dict, indent=4)
            jsonf.write(jsonString)

domains_structure = csv_to_json_data(inputCsvFilePath)

if domains_structure != False:
    create_structure_json_file(domains_structure, outputJsonFilePath)

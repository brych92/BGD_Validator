import csv
import os


# The `Csv_to_json_structure_converter` class provides methods to convert CSV data into nested
# dictionary structures for layers and attributes, as well as domain names and codes.
class Csv_to_json_structure_converter:
    def __init__(self, path_to_folder:str):
        """
        The function initializes an object with specified file names and a path to a folder.
        
        :param path_to_folder: The `__init__` method you provided is a constructor for a class. It
        initializes three instance variables: `structure_csv_filename`, `domains_csv_filename`, and
        `path_to_folder`. The `path_to_folder` parameter is a string that represents the path to a
        folder in the file system
        :type path_to_folder: str
        """
        self.structure_csv_filename = 'structure.csv'
        self.domains_csv_filename = 'domain.csv'
        self.metadata_csv_filename = 'metadata.csv'
        self.crs_csv_filename = 'crs.csv'
        self.path_to_folder = path_to_folder
        
    def csv_to_json_data(self, inputCsvFilePath):
        """
        This function reads data from a CSV file, converts each row into a Python dictionary, stores
        them in a JSON array, and returns the JSON array.
        
        :param inputCsvFilePath: The `inputCsvFilePath` parameter in the `csv_to_json_data` function is
        the file path to the CSV file that you want to convert to JSON data. This function reads the
        data from the CSV file, converts each row into a Python dictionary, and then appends these
        dictionaries to a JSON
        :return: The function `csv_to_json_data` is returning the data read from the CSV file in the
        form of a list of dictionaries (jsonArray).
        """
        
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

    def create_structure_json(self):
        """
        The function `create_structure_json` converts CSV data to a nested dictionary structure in
        Python.
        
        :param structure_bgd: The `create_structure_json` method takes a `structure_bgd` parameter,
        which is expected to be a list of dictionaries representing structure data. The method processes
        this data to create a JSON structure representing the layers and attributes
        :return: The function `create_structure_json` is returning a dictionary `layers_structure_dict`
        that contains information about the structure of layers. Each key in the dictionary represents a
        layer name in English, and the corresponding value is a dictionary containing details such as
        the layer name in Ukrainian, geometry type, class, and attributes. The attributes dictionary
        further contains information about each attribute of the layer, including its name in English
        """
        structure_bgd = self.csv_to_json_data(os.path.join(self.path_to_folder, self.structure_csv_filename))
        
        if structure_bgd:
            layers_structure_dict = {}

            for x in structure_bgd:
                
                if x['layer_name_en'] not in layers_structure_dict:
                    layers_structure_dict[x['layer_name_en']] = {}
                layers_structure_dict[x['layer_name_en']]['layer_name_ua'] = x['layer_name_ua']
                x['geometry_type'] = x['geometry_type'].replace(', ', ',')
                layers_structure_dict[x['layer_name_en']]['geometry_type'] = x['geometry_type'].split(',')
                layers_structure_dict[x['layer_name_en']]['class'] = x['class']
                
                if 'attributes' not in layers_structure_dict[x['layer_name_en']]:
                    layers_structure_dict[x['layer_name_en']]['attributes'] = {}
                layers_structure_dict[x['layer_name_en']]['attributes'][x['attribute_name_en']] = {
                                        'attribute_name_ua': x['attribute_name_ua'],
                                        "attribute_type": x['attribute_type'],
                                        "attribute_required": x['attribute_required'],
                                        "attribute_len": x['attribute_len'],
                                        "attribute_default_value": x['attribute_default_value'],
                                        "attribute_unique" : x['attribute_unique'],
                                        "domain" : x['domain'],
                                        "attribute_is_id": x['attribute_is_id']
                                        }
            return layers_structure_dict
        
    def create_domain_json(self):
        """
        The function `create_domain_json` converts CSV data into a nested dictionary structure for
        domain names and codes.
        
        :param domains_structure: The `domains_structure` parameter in the `create_domain_json` method
        is expected to be a list of dictionaries representing domain information. Each dictionary should
        have the keys 'name_eng', 'name_ukr', 'code', and 'value' to store the English name, Ukrainian
        name, code,
        :return: The function `create_domain_json` is returning a dictionary `domain_with_codes_dict`
        that contains domain names in English as keys, and for each domain name, it contains a
        dictionary with the corresponding name in Ukrainian and a dictionary of codes and their values.
        """
        
        domains_structure = self.csv_to_json_data(os.path.join(self.path_to_folder, self.domains_csv_filename))
        
        if domains_structure:
            domain_with_codes_dict = {}
            
            for x in domains_structure:
                if x['name_eng'] not in domain_with_codes_dict:
                    domain_with_codes_dict[x['name_eng']] = {}
                domain_with_codes_dict[x['name_eng']]['name_ukr'] = x['name_ukr']
                if 'codes' not in domain_with_codes_dict[x['name_eng']]:
                    domain_with_codes_dict[x['name_eng']]['codes'] = {}
                domain_with_codes_dict[x['name_eng']]['codes'][x['code']] = x['value']
                

            return domain_with_codes_dict
        
    def create_metadata_json(self):
        """
        The function `create_metadata_json` converts CSV data to a JSON format with specific key-value
        pairs.
        :return: a JSON object containing metadata information extracted from a CSV file. The metadata
        includes fields such as short_structure_name, structure_name, structure_date, structure_version,
        author, description, and format. The function processes the data from the CSV file and organizes
        it into a JSON structure before returning it.
        """
        
        metadata_structure = self.csv_to_json_data(os.path.join(self.path_to_folder, self.metadata_csv_filename))
        
        if metadata_structure:
            metadata_json = {}
            
            for x in metadata_structure:
                metadata_json['short_structure_name'] = x['short_structure_name']
                metadata_json['structure_name'] = x['structure_name']
                metadata_json['structure_date'] = x['structure_date']
                metadata_json['structure_version'] = x['structure_version']
                metadata_json['author'] = x['author']
                metadata_json['description'] = x['description']
                x['format'] = x['format'].replace(', ', ',')
                metadata_json['format'] = x['format'].split(',')
                
            return metadata_json
        
    def create_crs_json(self):
        """
        The function `create_crs_json` converts data from a CSV file to a JSON format with specific
        key-value pairs.
        :return: A JSON object is being returned, where the keys are the 'crs' values from the input
        data and the values are the corresponding 'alias' values.
        """
        
        crs_structure = self.csv_to_json_data(os.path.join(self.path_to_folder, self.crs_csv_filename))
        
        if crs_structure:
            crs_json = {}
            
            for x in crs_structure:
                if len(x["crs"]) > 20:                    
                    description = f"{x['crs'][:35]}..."
                else:
                    description = x['crs']
                
                crs_json[f'{x["alias"]}({description})'] = x['crs']
                
            return crs_json

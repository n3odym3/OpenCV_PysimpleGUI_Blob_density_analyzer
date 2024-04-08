#!/usr/bin/env python
import json

def load_json(filename) :
    '''Load the json file containing the saved settings and return a list with each settings to update the GUI'''
    try:
        with open(filename, 'r') as openfile:
            settings_import = json.load(openfile)
    except :
        print("Error while reading file")
        return False
    
    print("Reading " + filename)

    return settings_import

def save_json(file, settings_export):
    '''Save the current GUI settings in a JSON file'''

    json_object = json.dumps(settings_export, indent=4)

    try :
        with open(file, "w") as outfile:
            outfile.write(json_object)
    except :
        print("Settings not saved ! Slow down, you are clicking too fast on the GUI !")

settings = load_json('settings.json')
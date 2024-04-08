import numpy as np

def edit_bin_settings(imageprocess, settings_dict):
    '''Edit the [bin] settings from the GUI values'''
    imageprocess.enabled = settings_dict['bin-bin']
    imageprocess.showselec = settings_dict['bin-showselec']
    imageprocess.bsize = settings_dict['bin-bsize']
    imageprocess.bthresh = settings_dict['bin-bthresh']
    imageprocess.blur = settings_dict['bin-blur']

def update_gui_from_settings(settings_dict,imageprocess,to_gui_list): 
    '''Update the GUI using the settings dict. \n Input : path of the json file''' 
    try :
        for setting, state in settings_dict["gui"].items() :
            if setting in settings_dict["skiplist"] :
                continue
            to_gui_list.append(('W1',setting,state))
        
        #Update the bin, tracker and denseflow instances
    except Exception as e:
        print(e)
    
    edit_bin_settings(imageprocess, settings_dict["gui"])

if __name__ == '__main__' :
	#region Libs
	import cv2
	import pandas as pd
	import numpy as np
	from functions import *
	from gui import *
	from plot import *
	from edit_settings import *
	from file_tools import *
	import multiprocessing
	#endregion Libs==============
	
	#region Default settings
	multiprocessing.freeze_support()
	sg.set_options(dpi_awareness=False)

	frame = None
	zoomed_frame = None
	selected_ROI_frame = None
	ret = False
	last_clic = (0,0)

	imageprocess = ImageProcess()
	plotgui = PlotGUI()
	folderprocess = FolderProcess()
	timelapse = Timelpase()
	speedzen = SpeedZen()
	fileindex = 0
	file = ""
	mode = ""
	#endregion 

	#region Queues
	from_gui = multiprocessing.Queue(10) #New GUI events
	to_gui = multiprocessing.Queue(10) #Update GUI
	to_plot = multiprocessing.Queue(10) #Send figure to plot window
	to_gui_list = [] #List of update to send to GUI
	#endregion ==============================
	
	#region Automation functions
	def mouse_callback(event, x, y, flags, params):
		global frame, cropped_frame, zoomed_frame,selected_ROI_frame, gui_values, last_clic

		if params == "Frame" : #Ne réagit que si l'on clique sur la fenêtre principale

			zoomed_frame = timelapse.crop_frame(frame,(x,y),int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))

			tempframe = frame.copy()
			tempframe = timelapse.display_rect(tempframe, (x,y),int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))

			cv2.imshow('Frame',tempframe)
			
			if event == cv2.EVENT_LBUTTONDOWN : #Left clic
				if timelapse.enabled :#If timelapse enabled, get the average pixel vlaue at the clicked position
					timelapse.x = x
					timelapse.y = y
					timelapse.ROI_position = (x,y) #Get te position of the clic
					timelapse.ROI_dimensions = (int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h'])) #Get the dimension of the ROI from the GUI
					selected_ROI_frame = timelapse.crop_frame(frame,(x,y),int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))
					
					init_opencv_window('Selection', width= int(gui_values['timelapse-roi_w'])*5, height= int(gui_values['timelapse-roi_h'])*5)
					last_clic = (x,y)

					cv2.imshow('Selection',selected_ROI_frame)
					cv2.imshow('Frame',frame)

	def init_opencv_window(name = "Frame", width=None, height=None):
		'''Initialize a new OpenCV windows with a custom [name] and [resolution]'''
		cv2.namedWindow(name, cv2.WINDOW_NORMAL)
		cv2.setMouseCallback(name, mouse_callback, name)
		if width is not None and height is not None :
			cv2.resizeWindow(name, width, height)

	#region Sofwtare init
	multiprocessing.Process(target=gui, args=((mainwindow,plotwindow,loadingwindow),from_gui,to_gui,to_plot,), name='gui').start()
	gui_window, gui_event, gui_values = "","",{}
	gui_ids_values = None
	gui_control_values = None
	update_gui_from_settings(settings,imageprocess,to_gui_list)
	#endregion

	while True: #Main loop
		
		#region Queues sync [GUI]
		if not from_gui.empty() : #Get GUI event     
			gui_window, gui_event, temp_gui_values = from_gui.get()
			#User closed the main window => Exit program
			if gui_window == 'W1' and gui_event in (None, 'Exit'):
				break
			#Determines with which window the user has interacted
			if gui_window == 'W1' : #Main window
				gui_values = temp_gui_values
			elif gui_window == 'W2' : #Plot window
				gui_plot_values = temp_gui_values
			elif gui_window == "CANVAS" : #Figure on the plot window
				print(temp_gui_values)
		#endregion Queues sync [GUI]
		
		#region GUI events handling
		if gui_event and gui_event not in ('none', '__TIMEOUT__') :

			if type(gui_event) is tuple : #Correction for the table element that return a tuple instead of a string
				gui_event = gui_event[0] #Get the table selected line

			eventsplit = gui_event.split('-') #Split "topic" and "payload"
			match eventsplit[0] :

				case 'bin' : 
					edit_bin_settings(imageprocess,gui_values) #Update settings
					
					match eventsplit[1] :
						case 'plotdistr' : #Plot cells surfaces + size thresholds
							to_gui_list.append(('W1','window-plotenabled', True))
							# to_gui_list.append(('W2', 'file-figname', gui_values['video-folder'].split('/').pop().split('.')[0]))
							figure = plotgui.plot_sizes(imageprocess.raw_areas, imageprocess.left_thresh, imageprocess.right_thresh, 'Surfaces distribution')
							to_plot.put(figure)
			
						case 'mask' : #Show mask
							imageprocess.mask_enabled = gui_values['bin-mask']
							if gui_values['bin-mask'] :   
								init_opencv_window('Bin mask')
							else :
								try :
									cv2.destroyWindow('Bin mask')
								except :
									print("You tried to close a non existing window")						

				case 'timelapse' : #timelapse processor
					match eventsplit[1]:
						case 'table' :
							#Display the selected image
							if gui_values['timelapse-table'] : #If the table is not empty 
								
								fileindex = gui_values['timelapse-table'][0] 
								timelapse.currentimg = fileindex

								ret, frame = timelapse.grab(
									image_id = fileindex,
									negative = gui_values["timelapse-negative"], 
									color = gui_values["timelapse-color"],
									palette = gui_values["timelapse-colormap"],
									lower_norm = gui_values["timelapse-lowernorm"],
									upper_norm = gui_values["timelapse-uppernorm"]
									)
								
								if gui_values['image-show'] :
									init_opencv_window("Frame")
									cv2.imshow('Frame', frame )

						case 'read' :
							to_gui_list.append(('W1','timelapse-table',zip(timelapse.filelist, timelapse.statuslist)))
							if timelapse.set_folder(gui_values['timelapse-folder'], gui_values['timelapse-filextension']): #If the folder contains jpg files
								to_gui_list.append(('W1','timelapse-table',zip(timelapse.filelist, timelapse.statuslist))) #Display the image list on the GUI 
								to_gui.put([('W4', 'loading-bar1', 0),('W4', 'loading-title1', 'Reading images')]) #
								timelapse.filelist = [] #Filename list
								timelapse.imglist = [] #Frame list (numpy matrix)

								for i in range(len(timelapse.pathlist)) :
									frame,intensity = timelapse.read(timelapse.pathlist[i])
									timelapse.filelist.append(timelapse.pathlist[i].split('/')[-1])
									timelapse.imglist.append(frame)
									timelapse.intlist.append(intensity)
									to_gui.put([
									('W4', 'loading-bar1', (100/len(timelapse.pathlist))*i),
									('W4', 'loading-title1', 'Reading image : {}/{}'.format(i,len(timelapse.pathlist)))
									])

								to_gui.put([('W4', 'close')])
								ret, frame = timelapse.grab(
									image_id = 0,
									negative = gui_values["timelapse-negative"], 
									color = gui_values["timelapse-color"],
									palette = gui_values["timelapse-colormap"],
									lower_norm = gui_values["timelapse-lowernorm"],
									upper_norm = gui_values["timelapse-uppernorm"]
									)

						case 'lowernorm' :
							ret, frame = timelapse.grab(
									image_id = fileindex,
									negative = gui_values["timelapse-negative"], 
									color = gui_values["timelapse-color"],
									palette = gui_values["timelapse-colormap"],
									lower_norm = gui_values["timelapse-lowernorm"],
									upper_norm = gui_values["timelapse-uppernorm"]
									)

							if gui_values['image-show'] :
								init_opencv_window("Frame")
								cv2.imshow('Frame', frame) #TODO
						
						case 'uppernorm' :
							ret, frame = timelapse.grab(
									image_id = fileindex,
									negative = gui_values["timelapse-negative"], 
									color = gui_values["timelapse-color"],
									palette = gui_values["timelapse-colormap"],
									lower_norm = gui_values["timelapse-lowernorm"],
									upper_norm = gui_values["timelapse-uppernorm"]
									)

							if gui_values['image-show'] :
								try :
									init_opencv_window('Frame')
									cv2.imshow('Frame', frame)
								except :
									print("Select the image first !")

				case 'image' :
					match eventsplit[1] :
						case 'zoom' :
							if gui_values['image-zoom']: #Show video
								init_opencv_window('Zoom', width= int(gui_values['timelapse-roi_w'])*5, height= int(gui_values['timelapse-roi_h'])*5)
							else : #Hide video
								try :
									cv2.destroyWindow('Zoom')
								except :
									print("You tried to close a non existing window")
							
						
						case 'show' :
							if gui_values['image-show']: #Show video
								init_opencv_window("Frame")
							else : #Hide video
								try :
									cv2.destroyWindow('Frame')
								except :
									print("You tried to close a non existing window")

				case 'fluo' :
					match eventsplit[1] :
						case 'asc' :
							IMG_list = speedzen.translate_asc_file(gui_values['fluo-asc'])
							to_gui_list.append(('W1', 'fluo-imgcount', "Decoded IMG : {}".format(len(IMG_list))))
							to_gui_list.append(('W1', 'fluo-name', gui_values['fluo-asc'].split('/')[-1].split('.')[0]))
						
						case 'export' :
							if gui_values['fluo-onlyfm'] :
								Corrected_FM = speedzen.correct_fluo(IMG_list)
								speedzen.export_images(Corrected_FM, os.path.dirname(gui_values['fluo-asc']), gui_values['fluo-name'])
							else :
								speedzen.export_images(IMG_list, os.path.dirname(gui_values['fluo-asc']), gui_values['fluo-name'])
						
						case 'batchexport' :
							if speedzen.set_folder(gui_values['fluo-folder'], ".asc"):
								to_gui.put([('W4', 'loading-bar1', 0),('W4', 'loading-title1', 'Reading images')]) #
								speedzen.filelist = [] #Filename list
								speedzen.imglist = [] #Frame list (numpy matrix)

								for i in range(len(speedzen.pathlist)) :
									IMG_list = speedzen.translate_asc_file(speedzen.pathlist[i])
									print(gui_values['fluo-folder'])
									filename = speedzen.pathlist[i].split('/')[-1].split('.')[0]
									print(gui_values['fluo-folder'])

									if gui_values['fluo-onlyfm'] :
										Corrected_FM = speedzen.correct_fluo(IMG_list)
										speedzen.export_images(Corrected_FM, gui_values['fluo-folder'], filename)
									else :
										speedzen.export_images(IMG_list,gui_values['fluo-folder'], filename)


									to_gui.put([
									('W4', 'loading-bar1', (100/len(speedzen.pathlist))*i),
									('W4', 'loading-title1', 'Reading image : {}/{}'.format(i,len(speedzen.pathlist)))
									])

								to_gui.put([('W4', 'close')])


			settings["gui"] = gui_values #Save the metadatas
			save_json('settings.json', settings) #Export the current settings
		#endregion

		if timelapse.enabled : 
			ret, frame = timelapse.grab(
							image_id = fileindex,
							negative = gui_values["timelapse-negative"], 
							color = gui_values["timelapse-color"],
							palette = gui_values["timelapse-colormap"],
							lower_norm = gui_values["timelapse-lowernorm"],
							upper_norm = gui_values["timelapse-uppernorm"]
							)

			if ret : 
				if gui_values['image-zoom'] :
					if cv2.getWindowProperty('Zoom',cv2.WND_PROP_VISIBLE) != -1 : #If the window is closed
						try :
							cv2.imshow('Zoom', zoomed_frame)
						except Exception as e:
							pass
						
				if imageprocess.enabled : 
					binarisedframe, overlay, mask = imageprocess.binarise(frame)
					cv2.imshow('Frame', binarisedframe)

					#Show (only) the selection on a separated window
					if gui_values['bin-mask'] and gui_values['image-show']:
						cv2.imshow('Bin mask', mask)

					if cv2.getWindowProperty('Selection',cv2.WND_PROP_VISIBLE) != -1 : #If the window is open
						selected_ROI_frame = timelapse.crop_frame(binarisedframe,last_clic,int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))
						try :
							cv2.imshow('Selection', selected_ROI_frame)
						except Exception as e:
							pass
					
					cropped_frame = timelapse.crop_frame(frame,last_clic,int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))
					cropped_mask = timelapse.crop_frame(mask,last_clic,int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))

					ROI_intens, Background_intens = imageprocess.get_itensity(cropped_frame,cropped_mask)
					intensity = (255-ROI_intens)-(255-Background_intens)
					to_gui_list.append(('W1','bin-counttxt',f'ROI Intensity : {intensity}'))

				else :
					cropped_frame = timelapse.crop_frame(frame,last_clic,int(gui_values['timelapse-roi_w']),int(gui_values['timelapse-roi_h']))
					ROI_intens = imageprocess.get_raw_itensity(cropped_frame)
					to_gui_list.append(('W1','bin-counttxt',f'ROI Intensity : {ROI_intens}'))

				
		if 'image-show' in gui_values and gui_values['image-show'] : #Display/update the video window
				key = cv2.waitKey(1) #Modify to change the framerate
		
		if len(to_gui_list) > 0 and not to_gui.full() : #Update the GUI
			to_gui.put(to_gui_list)
			to_gui_list = []

		gui_event = 'none'
	#GUI-----------------------------------------------------------------------------------

	#EXIT------------------
	cv2.destroyAllWindows()
	#EXIT------------------
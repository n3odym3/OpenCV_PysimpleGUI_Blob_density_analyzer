#!/usr/bin/env python

import cv2
import numpy as np
import math
import matplotlib.pyplot as plt
import os 
import pandas as pd
from natsort import natsorted
# from scipy.ndimage import label, generate_binary_structure, iterate_structure
# from scipy.ndimage.filters import maximum_filter


class FolderProcess :
	enabled = False #Feature enabled/disabled
	folder = '' #Folder path
	pathlist = [] #List of video [path] to process
	filelist = [] #List of video [name] to process
	statuslist = [] #List of video status 
	currentvid = 0 #Current video index
	currentpath = '' #Current video path
	csv_tracking = {} #Output dict that will be converter to a csv file
	dense_multiprocess_result = [] #TEMPORARY

	def set_folder(self,folder):
		'''Select the folder to process and list tha video it contains'''

		#Reset the settings
		self.folder = folder
		self.first_frame_index = 0
		self.first_frames = []
		#Find all the .mp4 video in the selected folder
		try :
			self.filelist = [ fname for fname in natsorted(os.listdir(folder)) if fname.endswith('.mp4')]
		except :
			return False
		
		self.pathlist =  [self.folder + '/'+ fname for fname in self.filelist] #Path list for the GUI
		self.statuslist = ['Not processed'] * len(self.filelist) #Status list for the GUI
		self.currentvid = 0 #Current vid index
		return True

	def start_folder(self) :
		'''Initialize the processing of a new folder'''
		self.enabled = True
		self.csv_tracking = {}
		self.currentvid = 0
		self.statuslist[self.currentvid] = 'Processing'
		self.currentpath = self.pathlist[self.currentvid]

	def next_video(self):
		'''Process the next video in the folder list'''
		self.statuslist[self.currentvid] = 'Done'
		self.currentvid +=1

		if self.currentvid < len(self.pathlist) :
			self.statuslist[self.currentvid] = 'Processing'
			self.currentpath = self.pathlist[self.currentvid]
			return True
	
	def save_last_tracking(self, Traces):
		'''Add a new column in the csv file with the results of the last tracking'''
		data = []
		for i in range(len(Traces['Trace'])):
			if Traces['Validity'][i] == 1:
				data.append(Traces['Trace'][i])
		self.csv_tracking[self.filelist[self.currentvid].split('.')[0]] = data

	def save_last_tracking_dense(self, Vectors, thresh =(0,500), name = None):
		data =[]
		for i in range(len(Vectors)):
			data.append(Vectors[i])
		if name is None :
			self.csv_tracking[self.filelist[self.currentvid].split('.')[0]] = data
		else :
			self.csv_tracking[name] = data
	
	def save_csv(self,metadata=""):
		'''Export the results as a csv file'''
		df = pd.DataFrame({ key:pd.Series(value) for key, value in self.csv_tracking.items()})
		out_file = self.folder + '/' + self.folder.split('/').pop() + "_" + metadata + '.csv'
		print('Exporting data as : ' + out_file )
		df.to_csv(out_file,index=False) 

		return out_file

	def save_simplifed_csv_dense(self):
		speed_df = pd.DataFrame({ key:pd.Series(value) for key, value in self.csv_tracking.items()})
		speed_df = pd.DataFrame(speed_df.mean()).transpose() 
		out_file = self.folder + '/' + self.folder.split('/').pop() + "_simplified_dense.csv"
		print('Exporting data as : ' + out_file )
		speed_df.to_csv(out_file,index=False) 

class ImageProcess :
	#region Init
	enabled = False
	bthresh = 10 #Binarisation threshold
	bsize = 11 #Block size
	blur = 1 #Blur level (to reduce the effect of image noise)
	erosion = 10 #Erosion level (to "close" open cells)
	sthreshinf = 0 #Lower size threshold (in %)
	sthreshsup = 100 #Upper size threshold (in %)
	left_thresh = 0 #Lower size threshold (in µm²)
	right_thresh = 500 #Upper size threshold (in µm²)
	enabled = False #Enable/disable the tracker
	anot = False #Show/hide anotations
	showselec = False #Show selected areas
	showboxes = False #Show boxes around selected areas
	showcenter = False #Show the center of the objects
	mask_enabled = False #Enable/disable the selection mask
	mask = None #Selection mask
	otsu = False #Enable/disable Ostu thresholding
	raw_areas = [] #ALL objects surfaces (even those outside the size threshold )
	results = None #Result of the cell detection = [cells_centers,cells_dimensions,cells_compactnesses,cells_areas]
	#endregion Init

	def binarise (self, frame) :
		anaframe = frame.copy()

		if len(anaframe.shape) == 3 :
			anaframe = cv2.cvtColor(anaframe, cv2.COLOR_BGR2GRAY)

		anaframe = cv2.GaussianBlur(anaframe, (int(self.blur), int(self.blur)), 0)

		mask = np.zeros_like(anaframe)
		overlay = anaframe.copy()

		if self.otsu : #Select the Otsu thresholding algorithm
			_,mask = cv2.threshold(anaframe,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
		else : #Select the adaptative thresholding algorithm
			mask = cv2.adaptiveThreshold(anaframe,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,int(self.bsize),self.bthresh+2)

		if self.showselec is True : #Show selected surfaces
			anaframe = cv2.cvtColor(anaframe,cv2.COLOR_GRAY2BGR) #Convert binary frame to BGR

			overlay = np.zeros_like(anaframe)
			overlay[mask == 255] = [0, 255, 0]
			
			anaframe = cv2.addWeighted(anaframe, 1, overlay, 0.5, 0)

		return anaframe, overlay, mask
	
	def get_itensity(self,frame, mask) :
		mask_bool = mask == 255
		avg_selection = np.mean(frame[mask_bool])
		avg_out =np.mean(frame[~mask_bool])

		return avg_selection, avg_out
	
	def get_raw_itensity(self,frame) :
		avg_selection = np.mean(frame)
		return avg_selection
		
class Timelpase :

	def __init__(self):
		self.enabled = False
		self.ROI_position = (0,0)
		self.ROI_dimensions = (10,10)
		self.framenum = 0

		self.folder = '' #Folder path
		self.pathlist = [] #List of images [path] to process
		self.filelist = [] #List of images [name] to process
		self.statuslist = [] #List of images status 
		self.currentpath = '' #Current path
		# self.csv_tracking = {} #Output dict that will be converter to a csv file

		self.imglist = []
		self.intlist = []

		self.x = 500
		self.y = 500

	def remap_pixel_intensity(self, image, low, high):
		"""
		Remap the pixel values of the image such that the range [low, high] 
		is stretched to [0, 255]. This boosts the visibility of features 
		in the specified range.
		"""

		image = image.astype(np.float32)
		normalized_img = (image - low) / (high - low)
		normalized_img = np.clip(normalized_img, 0, 1)
		rescaled_img = (255 * normalized_img).astype(np.uint8)
		return rescaled_img

	def read(self, file : str) -> tuple: 
		""" Read an image

		Args:
			file (str): File path

		Returns:
			tuple: frame and average pixels intensity
		"""
		self.enabled = True
		frame = cv2.imread(file, cv2.IMREAD_UNCHANGED)
		intensity = np.mean(frame).round(1)

		return frame, intensity

	def grab(self, image_id,negative = False, color = True, palette = "Inferno", lower_norm = 0, upper_norm = 255):
		'''Grab an image from the timelapse list'''
		if(image_id >= len(self.imglist) or image_id < 0):
			return False, None

		frame = self.imglist[image_id]
		
		if frame.dtype == np.uint16 :
			frame = (frame >> 4).astype(np.uint8)

		frame = self.remap_pixel_intensity(frame, lower_norm, upper_norm)
		if negative :
			frame = abs(255-frame)

		if color :
			match palette :
				case 'Inferno' :
					frame = cv2.applyColorMap(frame, cv2.COLORMAP_INFERNO)
				case 'Jet' : 
					frame = cv2.applyColorMap(frame, cv2.COLORMAP_JET)
				case 'Hot' : 
					frame = cv2.applyColorMap(frame, cv2.COLORMAP_HOT)
		
		if len(frame.shape) == 2:
			frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
			
		return True, frame

	def calc_roi(self, frameindex, position, dimension):
		x1 = position[0] - math.ceil(dimension[0]/2)
		y1 = position[1] - math.ceil(dimension[1]/2)
		x2 = position[0] + math.ceil(dimension[0]/2)
		y2 = position[1] + math.ceil(dimension[1]/2)
		ROI = self.imglist[frameindex][y1:y2, x1:x2]

		average_intensity = np.average(ROI)
	
		return average_intensity
	
	def set_folder(self,folder, extension = ".png"):
		'''Select the folder to process and list tha video it contains'''
		#Reset the settings
		self.folder = folder
		self.first_frame_index = 0
		self.first_frames = []
		#Find all the .mp4 video in the selected folder
		try :
			self.filelist = [ fname for fname in natsorted(os.listdir(folder)) if fname.endswith(extension)]
		except :
			return False
		
		self.pathlist =  [self.folder + '/'+ fname for fname in self.filelist] #Path list for the GUI
		self.statuslist = ['Not processed'] * len(self.filelist) #Status list for the GUI
		self.currentimg = 0 #Current vid index
		return True
	
	def crop_frame(self, frame, center, width, height):
		# x = max(0,int(center[0] - width / 2))
		# y =  max(0,int(center[1] - height/ 2))
		# x2 = min(center[0] + height, frame.shape[1])
		# y2 = min(center[1] + height, frame.shape[0])
		anaframe = frame.copy()

		x1 = center[0] - math.ceil(width/2)
		y1 = center[1] - math.ceil(height/2)
		x2 = center[0] + math.ceil(width/2)
		y2 = center[1] + math.ceil(height/2)

		anaframe = anaframe[y1:y2, x1:x2]

		return anaframe
	
	def overlap_frame(self, original_frame, mask_frame, center, width, height):
		# x = max(0,int(center[0] - width / 2))
		# y =  max(0,int(center[1] - height/ 2))

		# x2 = min(center[0] + height, original_frame.shape[1])
		# y2 = min(center[1] + height, original_frame.shape[0])
		x1 = center[0] - math.ceil(width/2)
		y1 = center[1] - math.ceil(height/2)
		x2 = center[0] + math.ceil(width/2)
		y2 = center[1] + math.ceil(height/2)

		original_frame[y1:y2, x1:x2] = mask_frame

		return original_frame
	
	def display_rect(self, frame,center, width, height) :
		x1 = center[0] - math.ceil(width/2)
		y1 = center[1] - math.ceil(height/2)
		x2 = center[0] + math.ceil(width/2)
		y2 = center[1] + math.ceil(height/2)
		
		frame = cv2.rectangle(frame,(x1,y1),(x2,y2),(255,0,0),2)

		return frame
	
class SpeedZen :
	imglist = []

	def set_folder(self,folder, extension = ".asc"):
		'''Select the folder to process and list tha video it contains'''
		#Reset the settings
		self.folder = folder
		self.first_frame_index = 0
		self.first_frames = []
		#Find all the .asc video in the selected folder
		try :
			self.filelist = [ fname for fname in natsorted(os.listdir(folder)) if fname.endswith(extension)]
		except :
			return False
		
		self.pathlist =  [self.folder + '/'+ fname for fname in self.filelist] #Path list for the GUI
		self.statuslist = ['Not processed'] * len(self.filelist) #Status list for the GUI
		self.currentimg = 0 #Current vid index
		return True

	def translate_asc_file(self, file_path) :
		with open(file_path, 'r') as file:
			TextFile = file.readlines()

		metadata = TextFile[0].strip().split(',')
		img_count = int(metadata[0])
		img_width = int(metadata[1])
		img_height = int(metadata[2])

		Start_index = 0
		for i in range(len(TextFile)) :
			if len(TextFile[i])>1000 :
				Start_index = i
				break

		IMG_List = []

		for i in range(img_count):
			image = np.fromstring(TextFile[Start_index+i].strip(), dtype='uint16',count=img_width*img_height, sep=',').reshape((img_width, img_height))
			IMG_List.append(image)

		return IMG_List

	def export_images(self,IMG_list, folder, name):
		for i in range(len(IMG_list)) :
			cv2.imwrite("{}/{}_{}.png".format(folder, name, i),IMG_list[i],[cv2.IMWRITE_PNG_COMPRESSION, 0])

	def correct_fluo(self, IMG_list) :
		output = []
		corrected_fm = cv2.subtract(IMG_list[2], IMG_list[0])
		output.append(corrected_fm)
		return output
	
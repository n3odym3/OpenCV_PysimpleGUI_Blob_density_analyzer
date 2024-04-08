#!/usr/bin/env python
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import seaborn as sns
from joypy import joyplot
import numpy as np
from scipy import stats
import math
from random import randint
import numpy as np
import pyperclip
from scipy.signal import savgol_filter

class PlotGUI :
	figure = None #Current figure
	axes = None #Currenf figure axes
	type = '' #To name the saved svg file 
	
	def create_figure(self) :
		'''Create an empty figure in the canvas'''
		if self.figure :
			self.figure.clf()
		else :
			self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
	
	def save_figure(self,path, name):
		'''Save the figure as .svg in the provided folder'''
		outfilename = path + name + "_" + self.type + '.svg'
		self.figure.savefig(outfilename)
		print('Saving ' + outfilename)
		return
	
	def get_angle(self,p1, p2):
		'''Calculate the angle between the horizontal axis and the line defined by p1 (X1,Y2) and p2 (X2,Y2) to create a polar graph'''
		angl = math.degrees(math.atan2(0,1) -math.atan2(p2[1]-p1[1], p2[0]-p1[0]))
		return angl + 360 if angl < 0 else angl
	
	def find_nearest_index(self,array,value):
		'''Find the index of the closest value in the provided array
		\n Input : array = [10,20,30,40,50], value=38
		\n Output : 3'''

		idx = np.searchsorted(array, value, side="left")
		if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
			return idx-1
		else:
			return idx
		
	def plot_speeds(self,data,validity,thresh,tracking_period,title):
		'''Plot [histogram + kde] the speed of ALL the tracked cells
		\n Input :
		\n - data : [array] containing all the traces
		\n - validity : [array] containing the validity of all the traces
		\n - thresh : [tuple] containing the left and right speed threshold
		\n - tracking_period : video FPS/trace length (usually =1)
		\n - title : figure title
		'''

		#Init figure
		self.type = 'histogram_speed'
		self.create_figure()

		plotlist = [] #Array of values to plot

		for i in range(len(data)) : #Iterate over all the traces
			if validity[i] == 1 : #Check if the trace is valid
				trace = data[i] * tracking_period #Convert distance (µm) in speed (µm/s)
				if((trace > thresh[0]) and (trace < thresh[1])): #Check if the trace is inside the user defined threshold
					plotlist.append(trace) #Add the trace to the plot

		#Create the plot
		sns.histplot(plotlist, lw=1,stat="density", alpha=0.5, binwidth=5, ax=self.axes)
		sns.kdeplot(plotlist, ax=self.axes, lw=2, fill=True)

		#Set the title and axes names
		title = title + ' {:.1f} {:.1f}'.format(np.mean(plotlist),np.std(plotlist))
		self.axes.set_title(title)
		self.axes.set_xlabel('Speed (µm/s)')
		self.axes.set_ylabel('Density (normalized)')

		return  self.figure 
	
	def plot_sizes(self,data, lower_thresh, upper_thresh, title):
		'''Plot the [histogram + kde] of the area distribution of the cells and draw the size threshold of the counter tool
		\n Input :
		\n - data : [array] containing all the areas
		\n - lower_thresh : [float] lower area threshold
		\n - lower_thresh : [float] lower area threshold
		\n - title : figure title'''

		#Init figure
		self.type = 'histogram_area'
		self.create_figure()

		#Create the plot
		sns.histplot(data, lw=1,stat="density", alpha=0.5, binwidth=int(len(data)/15), ax=self.axes)
		sns.kdeplot(data, ax=self.axes, lw=2, fill=True)

		#Set the title and axes names
		self.axes.axvline(x = lower_thresh,ymin = 0,ymax = 1)
		self.axes.axvline(x = upper_thresh,ymin = 0,ymax = 1)
		self.axes.set_title(title)
		self.axes.set_xlabel('Area (µm²)')
		self.axes.set_ylabel('Count')

		return self.figure

	def plot_speed_dense(self, speeds, thresh=(0,500)) :
		'''Plot the [histogram + kde] of the [agregated] speeds of the cells calculated from the dense optical flow
		\n Input :
		\n - data : [array] containing all the speeds'''

		#Init figure
		self.type = 'hitogram_speeds'
		self.create_figure()

		#Create the plot
		plotlist = []
		for i in range(len(speeds)) : #Iterate over all the traces
				if((speeds[i] > thresh[0]) and (speeds[i] < thresh[1])): #Check if the trace is inside the user defined threshold
					plotlist.append(speeds[i]) #Add the trace to the plot

		sns.histplot(plotlist, lw=1,stat="density", alpha=0.5, binwidth=5, ax=self.axes)
		sns.kdeplot(plotlist, ax=self.axes, lw=2, fill=True)

		#Set the title and axes names
		title ='{:.1f} {:.1f}'.format(np.mean(plotlist),np.std(plotlist)) 
		self.axes.set_title(title)
		self.axes.set_xlabel('Speed (µm/s)')
		self.axes.set_ylabel('Density (normalized)')
		return  self.figure 

	def plot_orient(self,angles,bin_width=10):
		'''Plot the [polar graph] of the cells orientations
		\n Input :
		\n - data : [array] containing all the angles'''

		self.type = 'angles'
		self.create_figure()
		self.figure.clf()
		self.axes = self.figure.add_axes([0.025, 0.025, 0.95, 0.95], polar=True)

		if 360%bin_width == 0 :
			num_bins = int(360/bin_width)
		else :
			print("Bin_width should be a multiple of 360° ! The default bin_width of 10 has been used")
		bin_counts = np.zeros(num_bins, dtype=int)
		
		for angle in angles:
			bin_index = int(angle / bin_width)
			bin_counts[bin_index] += 1

		# Define the theta values for the bin centers
		theta = np.deg2rad(np.arange(0, 360, bin_width))
		colors = plt.cm.hsv(theta / (2 * np.pi))

		self.axes.bar(theta, bin_counts, width=np.deg2rad(bin_width), color=colors, alpha=0.75)
		self.axes.set_theta_direction(-1)
		self.axes.set_xticklabels([])
		self.axes.set_yticklabels([])
		return self.figure
	
	def plot_lineplot_csv(self,data,thresh,smoothing = False, both = False, savgolsettings = (10,2), title="Average speed of the samples"):
		'''Create a line plot from the mean of each column of the input dataframe'''
		
		#Init figure
		self.type = 'lineplot_speed'
		self.create_figure()
		
		groups = data.columns #Get the colnames

		#Create a list that contains the mean of every columns
		means = []

		for group in groups :
			data[group] = np.where((data[group] < thresh[0]) | (data[group] > thresh[1]), np.nan, data[group])
			means.append(np.mean(data[group]))
		pyperclip.copy('\n'.join(str(item) for item in means))

		if smoothing :
			try : 
				smooth = savgol_filter(means, int(savgolsettings[0]), int(savgolsettings[1]))
				pyperclip.copy('\n'.join(str(item) for item in smooth))
				sns.lineplot(x=groups, y=smooth, ax=self.axes)
			except :
				sns.lineplot(x=groups, y=means, ax=self.axes)
			if both :
				sns.lineplot(x=groups, y=means, ax=self.axes)
		else :
			sns.lineplot(x=groups, y=means, ax=self.axes)
			
		#Create the lineplot
		self.axes.set_title(title)

		return self.figure
		
	def plot_basic_lineplot(self,data,title="Average speed of the samples"):
		'''Create a line plot from the mean of each column of the input dataframe'''
		#Init figure
		self.type = 'lineplot_speed'
		self.create_figure()
		
		pyperclip.copy('\n'.join(str(item) for item in data))
		#Create the lineplot
		sns.lineplot(data, ax=self.axes)
		self.axes.set_title(title)

		return self.figure
	
	def plot_basic_lineplot_withX(self,data,title="Average speed of the samples"):
		'''Create a line plot from the mean of each column of the input dataframe'''
		#Init figure
		self.type = 'lineplot_speed'
		self.create_figure()
		df = pd.DataFrame({'X': data[0], 'Y': data[1]})
		pyperclip.copy('\n'.join(str(item) for item in data))
		#Create the lineplot
		sns.lineplot(data=df,x='X', y='Y', ax=self.axes)
		self.axes.set_title(title)

		return self.figure
	
	def plot_kdeplot_csv(self,data,thresh,title="Speed distribution of the samples"):
		'''Create a kde plot from the mean of each column of the input dataframe'''
		
		#Init figure
		self.type = 'kde_speed'
		self.create_figure()
		self.axes.set_title(title)

		#Create the kde plot
		sns.kdeplot(data, ax=self.axes)
		
		return self.figure
	
	def plot_boxplot_csv(self,data,thresh,title="Speed distribution of the samples") :
		'''Create a boxplot from the mean of each column of the input dataframe'''
		
		#Init figure
		self.type = 'boxplot_speed'
		self.create_figure()
		self.axes.set_title(title)

		#Create the boxplot
		sns.boxplot(data, ax=self.axes, showfliers = False)

		return  self.figure 

	def plot_joyplot_csv(self,data,thresh, title="Speed distribution of the samples") :
		'''Create a joyplot from the mean of each column of the input dataframe'''
		
		#Init figure
		self.type = 'joyplot_speed'
		self.create_figure()
		# self.axes.set_title(title)

		#Create the joyplot
		joyplot(data, ax=self.axes,colormap=sns.color_palette("crest", as_cmap=True))

		return self.figure
	
	def draw_heatmap_posthoc_csv(self,data,labels) :
		'''Draw a matrix that display the statisitcal significance of pairwise sample comparison'''
		stat_comparator = 'T' #Comparison based on the T-value

		#Init figure
		self.create_figure()
		self.type = 'matrix posthoc'

		result = [] #Array containing every sample pair stat val (each pair is another array containig Ai vs B1, B2, B3, ....)
		i = -1 
		for sample_A in labels :
			i+=1
			result.append([])#Result of sample Ai vs all the other samples

			for sample_B in labels :
				#Stat val = 0 if the sample is compare with itself
				if sample_A == sample_B :
					result[i].append(0)
					continue

				#Get stat val of the current sample pair
				stat_val = data.loc[(data['A'] == sample_A) & (data['B'] == sample_B), stat_comparator].values
				#If A vs B is not found search for B vs A
				if len(stat_val)==0 :
					stat_val = data.loc[(data['A'] == sample_B) & (data['B'] == sample_A), stat_comparator].values
				
				#Append Ai vs Bx at the index  
				result[i].append(abs(stat_val[0]))

		 
		result =  np.array(result) #Convert the python array to numpy array 
		
		#Significance threshold
		bounds=[4.99,5] #T-val > 5 = significant difference
		# bounds=[0.049,0.05] #P-val > 0.05 = significant difference

		#Set the color of the cells depending on the significance of the stat value
		cmap = mpl.colors.ListedColormap(['green','red'])
		norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

		#Set the name of the cells 
		self.axes.set_xticks(np.arange(len(labels)), labels=labels)
		self.axes.set_yticks(np.arange(len(labels)), labels=labels)
		
		#Add white lines between cells
		self.axes.hlines(y=np.arange(0, result.shape[1])+0.5, xmin=np.full(result.shape[1], 0)-0.5, xmax=np.full(result.shape[1], result.shape[1])-0.5, color="w")
		self.axes.vlines(x=np.arange(0, result.shape[1])+0.5, ymin=np.full(result.shape[1], 0)-0.5, ymax=np.full(result.shape[1],result.shape[1])-0.5, color="w")
		
		#Display the stat val in each matrix cell		
		# for i in range(len(labels)):
		# 	for j in range(len(labels)):
		# 		self.axes.text(j, i, format(result[i,j], '.4f'),ha="center", va="center", color="w")

		self.axes.imshow(result,interpolation='nearest',cmap = cmap,norm=norm)

		return self.figure

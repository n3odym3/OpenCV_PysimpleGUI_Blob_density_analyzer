#!/usr/bin/env python
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns
import numpy as np
import pyperclip

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

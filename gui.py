#!/usr/bin/env python

import PySimpleGUI as sg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
from json_settings import *

sg.theme('DarkGrey9')

newevent = None

def on_click(event):
    '''Plot clic callback'''
    global newevent
    newevent = event.xdata

class MainWindow : 
    window = None
    last_filextension = ''
    last_colormap = ''

    top_layout = [
        sg.Checkbox('Show img', key='image-show', default=True, enable_events = True),
        sg.Checkbox('Zoom selec.', key='image-zoom', default=False, enable_events = True),
        sg.Checkbox('Show plot', key='window-plotenabled', default=False, enable_events = True),
    ]

    timelapse_layout =[
        [sg.FolderBrowse(),sg.Text('Folder'), sg.In(enable_events=True ,key='timelapse-folder', size=(5,5), expand_x=True)],
        [
            sg.Button('Read images', key='timelapse-read'),
            sg.OptionMenu(values=('.png', '.jpg', '.bmp', '.tif'), default_value = '.png' , k='timelapse-filextension'),
        ],
        [sg.Table(values=[['Image','Not processed']], headings=['File Name', 'Status'],key='timelapse-table', justification='center', size=(25,5), expand_x=True, expand_y=False, enable_click_events=True, enable_events=True)],
        [
            sg.Radio('normal',key='timelapse-normal', group_id="timelapse-normneg", default=True, enable_events=True),
            sg.Radio('negative',key='timelapse-negative', group_id="timelapse-normneg", default=False, enable_events=True),
            sg.VSep(),
            sg.Checkbox('Color', key='timelapse-color', default=True,enable_events=True),
            sg.OptionMenu(values=('Inferno', 'Jet', 'Hot'), default_value = 'Inferno' , k='timelapse-colormap'),  
        ],
        [   
            sg.Text('Image Normalization : ', font=('Helvetica', 10)),
            sg.Slider(key='timelapse-lowernorm',size=(10,10),font=('Helvetica', 8),range=(1,255),default_value=0, orientation='h',enable_events=True),
            sg.Slider(key='timelapse-uppernorm',size=(10,10),font=('Helvetica', 8),range=(1,255),default_value=255, orientation='h',enable_events=True),
        ] ,
        [sg.HSep()],
        [
            sg.Text('Image processing', font=('Helvetica', 10, 'bold', 'underline')),
        ],
        [
            sg.Text('ROI (W,H) ', font=('Helvetica', 10)),
            sg.InputText("10",size=(5,1),key="timelapse-roi_w",enable_events = True),
            sg.InputText("10",size=(5,1),key="timelapse-roi_h",enable_events = True),
            sg.Text('Blur'),
            sg.Slider(key='bin-blur',range=(1,20),resolution=2,size=(15,10),font=('Helvetica', 8), default_value=1,orientation='h',enable_events = True),
        ],
        [
            sg.Checkbox('Smart selection', key='bin-bin',default=False, enable_events = True), 
            sg.Checkbox('Selec', key='bin-showselec', default=False, enable_events = True),
            sg.Checkbox('Mask', key='bin-mask',default=False, enable_events = True),
        ],
        [   
            sg.Text('Size/Thresh'),
            sg.Slider(key='bin-bsize',range=(5,200),size=(15,10),font=('Helvetica', 8),resolution=2,default_value=3,orientation='h',enable_events = True),
            sg.Slider(key='bin-bthresh',range=(1,100),size=(15,10),font=('Helvetica', 8),default_value=4,orientation='h',enable_events = True)
        ],
        [sg.Text('ROI intensity : 0', font=('Helvetica', 10, 'bold'), key='bin-counttxt')],
        
    ]

    speedzen_layout = [
        [
            sg.Text('Single file', font=('Helvetica', 10, 'bold', 'underline')),
        ],
        [sg.FileBrowse(file_types=(("SpeedZen Files", "*.asc"),)),sg.Text('.asc File'), sg.In(size=(25,1), enable_events=True ,key='fluo-asc')],
        [sg.Text(text='Decoded IMG : NA',key='fluo-imgcount')],
        [
            sg.Text("Name : "),
            sg.In(size=(25,1) ,key='fluo-name')
        ],
        [
            sg.Radio('ALL Raw images',key='fluo-raw', group_id="fluo-mode", default=False, enable_events=True),
            sg.Radio('ONLY corrected Fm',key='fluo-onlyfm', group_id="fluo-mode", default=True, enable_events=True),
        ],
        [sg.Button('Save as PNG', key='fluo-export', expand_x=True)],
        [sg.HSep()],
        [
            sg.Text('Batch processing', font=('Helvetica', 10, 'bold', 'underline')),
        ],
        [sg.FolderBrowse(),sg.Text('Folder'), sg.In(enable_events=True ,key='fluo-folder', size=(5,5), expand_x=True)],
        [sg.Button('Save folder as PNG', key='fluo-batchexport', expand_x=True)],
    ]

    def __init__(self) :
        self.layout = [ 
            self.top_layout,
            [sg.TabGroup([[
                sg.Tab('Images', self.timelapse_layout),
                sg.Tab('SpeedZen', self.speedzen_layout),
                
            ]],
            key='-TAB GROUP-', expand_x=True, expand_y=True)
        ]]
            
        self.window = sg.Window(
            'Settings', 
            self.layout ,
            grab_anywhere=True, 
            resizable=True, 
            margins=(0,0), 
            use_custom_titlebar=False, 
            finalize=False, 
            keep_on_top=False, 
            return_keyboard_events=True,
            alpha_channel=1,
        )

class PlotWindow :       
    window = None
    figure = None
    fig_agg = None

    def make(self) :
        plot_layout =  [
        [sg.Canvas(key='plot-canvas',expand_x=True, expand_y=True)],
        [sg.Canvas(key='plot-control')],
        [   
            sg.Button('Save fig.', key='file-savefig', enable_events=True),
            sg.Text('Fig. name'), 
            sg.InputText(key='file-figname',size =(25, 1))
        ]
        ]
            
        if self.window is None :
            self.window = sg.Window('Plot', plot_layout, grab_anywhere=False, resizable=True, finalize=True)

    def close(self):
        if self.window :
            self.window.close()
            self.window = None

    def draw_figure(self):
        '''Draw the figure on the [plot] GUI Window'''

        #Reset the canva and toolbar if they already exist
        canvas = self.window['plot-canvas'].TKCanvas
        toolbar = self.window['plot-control'].TKCanvas
        if canvas.children:
            for child in canvas.winfo_children():
                child.destroy()
        if toolbar.children:
            for child in toolbar.winfo_children():
                child.destroy()
        
        #Draw the figure
        figure_canvas_agg = FigureCanvasTkAgg(self.figure, canvas) 
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

        #Add the toolbar
        toolbar = NavigationToolbar2Tk(figure_canvas_agg, toolbar)
        toolbar.update()

        #Add the clic callback
        self.figure.canvas.mpl_connect('button_press_event', on_click)

        return figure_canvas_agg

class LoadingWindow :
    window = None

    def make(self) :
        main_layout = [
            [
                sg.Text('Loading text', key='loading-title1',justification='center',expand_x=True )
            ],
            [
                sg.ProgressBar(100, orientation='h', expand_x=True, size=(30, 20),key="loading-bar1"), 
            ]
        ]

        layout = [
            main_layout
        ]

        if self.window is None :
            self.window = sg.Window(
                "Wait ! I'm doing something.", 
                layout, 
                grab_anywhere=False, 
                resizable=True, 
                finalize=True, 
                keep_on_top=False,
                )
    
    def close(self):
        if self.window :
            self.window.close()
            self.window = None

mainwindow = MainWindow()
plotwindow = PlotWindow()
loadingwindow = LoadingWindow()

#GUI handler========================================================
def gui(windows, from_gui, to_gui, to_plot):
    '''GUI handler. This function should run on a separated process !'''
    global newevent
    event, values = '',''
    # mainwindow, plotwindow = windows
    
    #GUI reading
    while True :  

        if newevent :
            from_gui.put(('CANVAS', 'none', newevent))
            newevent = None
            continue
        
        event, values = mainwindow.window.read(timeout=10)

        if event in (None, 'Exit') : #Close the program when the main window is closed
            from_gui.put(('W1','Exit',None)) 
            break

        if(mainwindow.last_filextension != values['timelapse-filextension']): #Fake event for Optionmenu
            mainwindow.last_filextension = values['timelapse-filextension']
            event = 'timelapse-filextension'

        if(mainwindow.last_colormap != values['timelapse-colormap']): #Fake event for Optionmenu
            mainwindow.last_colormap = values['timelapse-colormap']
            event = 'timelapse-colormap'

        if from_gui.empty() and event != "__TIMEOUT__":
            from_gui.put(('W1',event,values))

        if values and values['window-plotenabled'] :
            if plotwindow.window is None :
                plotwindow.make()

            event, values = plotwindow.window.read(timeout=10)

            if from_gui.empty() and event != "__TIMEOUT__":
                from_gui.put(('W2',event,values))

            if event in (None, 'Exit'):
                mainwindow.window['window-plotenabled'].update(False)
                continue
            
            if not to_plot.empty() :
                plotwindow.figure = to_plot.get_nowait()

                if plotwindow.figure :
                    if plotwindow.fig_agg :
                        plotwindow.fig_agg.get_tk_widget().forget()
                    
                    plotwindow.fig_agg = plotwindow.draw_figure()   
        else :
            if plotwindow.window :
                plotwindow.close()

        if loadingwindow.window :
            loadingevent, loadingvalues = loadingwindow.window.read(timeout=10)

            if loadingevent in (None, 'Exit'):
                loadingwindow.close()

        if not to_gui.empty() :
            updates  = to_gui.get_nowait()

            for update in updates :
                if update[0] == 'W1' :
                    mainwindow.window[update[1]].update(update[2])
                    
                if update[0] == 'W2' :
                    if plotwindow.window is None :
                        plotwindow.make()
                        plotwindow.window.read(timeout=10)
                    plotwindow.window[update[1]].update(update[2])

                if update[0] == 'W4' :
                    if loadingwindow.window is None :
                        loadingwindow.make()
                    if update[1] == 'close' :
                        loadingwindow.close()
                    else :
                        loadingwindow.window[update[1]].update(update[2])
#GUI handler========================================================




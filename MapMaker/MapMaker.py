# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 10:25:18 2020

@author: sebas

Map maker for tiled rpg game.

"""


import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename, askopenfilename
from PIL import Image, ImageTk
import numpy as np
import pathlib
import time
import gc
import os


CANVAS_BG_COLOR = '#222222'
CANVAS_GRID_COLOR = '#282828'
CANVAS_NULLTILE_COLOR = '#000000'
TILESIZE_MAX = 64
CURSOR_STEP = 0.1
CURSOR_SIZE = 20

ROOTDIR = os.path.abspath(os.path.dirname(__file__))
GAMEDIR = os.path.abspath(os.path.dirname(ROOTDIR))
MAP_DIR = os.path.join(GAMEDIR, os.path.join("res", "map"))
TILETHEME_DIR = os.path.join(MAP_DIR, "tiles")


def black_to_transparency(img):
    x = np.asarray(img.convert('RGBA')).copy()
    x[:, :, 3] = (255 * (x[:, :, :3] != 0).any(axis=2)).astype(np.uint8)
    return Image.fromarray(x)


def white_to_transparency(img):
    x = np.asarray(img.convert('RGBA')).copy()
    x[:, :, 3] = (255 * (x[:, :, :3] != 255).any(axis=2)).astype(np.uint8)
    return Image.fromarray(x)


class ScrollableFrame(tk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        


class AppliCanevas(tk.Tk):
    
    def __init__(self):
        
        tk.Tk.__init__(self)
        
        
        self.width = 880
        self.height = 720
        self.settingWidth = 300
        self.geometry("{0:d}x{1:d}".format(self.width+self.settingWidth, self.height))
        
        self.genMenu = True
        self.tileMenu = False
        self.objMenu = False
        self.wallMenu = False
        
        
        self.mapW = 10
        self.mapH = 16
        self.mapName = 'default name'
        self.oriX = 0.0
        self.oriY = 0.0
        
        self.Ntrans = 0
        self.Nanimobj = 0
        self.Nstaticobj = 0
        self.Nclickobj = 0
        self.Npnj = 0
        self.Nmobs = 0
        self.Nmobsutil = 0
        self.Nclickobjsutil = 0
        self.keptTrans = []
        self.keptAnimobj = []
        self.keptStaticobj = []
        self.keptClickobj = []
        self.keptPnj = []
        self.keptMobs = []
        self.keptMobsUtil = []
        self.keptClickobjsUtil = []
        
        #self.map_str = list(np.zeros((self.mapW, self.mapH), dtype=str))
        #self.map_id = list(np.zeros((self.mapW, self.mapH), dtype=int))
        self.map = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        self.mapFG = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        self.mapEdgeX = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.mapEdgeY = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.tileSize = TILESIZE_MAX
        self.canvCursor = [0, 0] # cursor for tile editing
        self.canvCursorExtend = [1, 1] #cursor for tile editing, width and height
        self.keyCtrlPressed = False
        self.canvMouseX = 0.0 # cursor for wall editing
        self.canvMouseY = 0.0
        self.wallBeginX = 0.0
        self.wallBeginY = 0.0
        self.wallEndX = 0.0
        self.wallEndY = 0.0
        self.wallWebbing = False # True when the beginning of the wall has been set already
        self.walls = []
        self.selectedWall = 0
        self.selectingWall = False
        self.BGvisible = True
        self.FGvisible = True
        
        
        
        self.tileTheme = 0
        self.tileThemes = []
        self.tilesLib = {}
        self.tilesPhoto = {}
        self.tilesPhotoFG = {}
        self.tilesLib_maxsize = 0
        self.tilesLib_buttonsize = 0
        self.tileMenuButton = []
        self.tileMenuPhoto = {} # similar to tilesLib but for the button image (resize to 64x64)
        self.tileMenuPhotoFG = {} # similar to tilesLib but for the button image (resize to 64x64)
        self.tileTobepasted = ""
        
        
        self.loadTilesLib()
        
        
        self.editedLayer = tk.IntVar()
        self.editedLayer.set(1)
        self.mapName = tk.StringVar()
        self.mapName.set('name')
        self.mapSizeX = tk.StringVar()
        self.mapSizeX.set(str(self.mapW))
        self.mapSizeY = tk.StringVar()
        self.mapSizeY.set(str(self.mapH))
        self.visibleLayer_bg = tk.IntVar()
        self.visibleLayer_bg.set(1)
        self.visibleLayer_fg = tk.IntVar()
        self.visibleLayer_fg.set(1)
        
        self.create_widgets()
        
        self.setEdgeTiles()
        self.drawMonitor()
        
        #self.bind_all("<Button-1>", lambda e: self.loosefocus(e)) 

    # def loosefocus(self, event): 
    #     w = self.focus_get() 
    #     print('focus on ', w)
    #     if str(w) == '.!frame.!notebook.!frame.!frame.!entry':
    #         print('focus entry detected')
    #         self.focus_set(self)
    #     #     self.focus_set()


    def loadTilesLib(self):
        print(TILETHEME_DIR)
        print(os.listdir(TILETHEME_DIR))
        for p in os.listdir(TILETHEME_DIR):
            if os.path.isdir(os.path.join(TILETHEME_DIR, p)):
                self.tileThemes.append(p)
        for d in self.tileThemes:
            self.tilesLib[d] = []
            self.tileMenuPhoto[d] = []
            self.tileMenuPhotoFG[d] = []
            self.tilesPhoto[d] = []
            self.tilesPhotoFG[d] = []
            for f in os.listdir(os.path.join(TILETHEME_DIR, d)):
                filepath = os.path.join(TILETHEME_DIR, os.path.join(d, f))
                if os.path.isfile(filepath):
                    self.tilesLib[d].append(f)
                    if len(f) > self.tilesLib_buttonsize:
                        self.tilesLib_buttonsize = len(f)
                    self.tileMenuPhoto[d].append(ImageTk.PhotoImage(Image.open(filepath).resize((64, 64), Image.ANTIALIAS)) )  #"grass.bmp") ))
                    self.tileMenuPhotoFG[d].append(ImageTk.PhotoImage(white_to_transparency(Image.open(filepath)).resize((64, 64), Image.ANTIALIAS)) )  #"grass.bmp") ))
                    self.tilesPhoto[d].append(ImageTk.PhotoImage(Image.open(filepath).resize((64, 64), Image.ANTIALIAS)) )  #"grass.bmp") ))
                    self.tilesPhotoFG[d].append(ImageTk.PhotoImage(white_to_transparency(Image.open(filepath)).resize((64, 64), Image.ANTIALIAS)) )  #"grass.bmp") ))
                    
            if len(self.tilesLib[d]) > self.tilesLib_maxsize:
                self.tilesLib_maxsize = len(self.tilesLib[d])
        
        

    def create_widgets(self):
        # création canevas
        self.canv = tk.Canvas(self, bg=CANVAS_BG_COLOR, borderwidth=1, height=self.height, width=self.width)
        self.canv.config(borderwidth=1)
        self.canv.pack(side=tk.LEFT)
        
        self.canv.bind('<Motion>', self.canvMotion)
        self.canv.bind('<Button-1>', self.canvClick)
        self.canv.bind('<KeyPress>', self.canvCursorKey)
        #self.canv.bind('<KeyRelease>', self.keyRelease)
        self.canv.bind('<BackSpace>', self.removeTile)
        
        # Full setting panel
        self.settingPanel = tk.Frame(self)
        
        self.settingNotebook = ttk.Notebook(self.settingPanel, width=self.settingWidth)
        
        self.sN_genFrame = tk.Frame(self.settingNotebook)
        self.sN_gF_nameFrame = tk.Frame(self.sN_genFrame, pady=5)
        self.sN_gF_nameLabel = tk.Label(self.sN_gF_nameFrame, text='Map name')
        self.sN_gF_nameLabel.pack(side=tk.LEFT)
        #self.vcmd_str = (self.register(self.callback_entryStr))
        self.sN_gF_nameEntry = tk.Entry(self.sN_gF_nameFrame, text=self.mapName.get(), textvariable=self.mapName)#, validate='key', validatecommand=self.callback_name)
        self.sN_gF_nameEntry.bind('<Return>', self.set_mapName)
        self.sN_gF_nameEntry.pack(side=tk.LEFT, fill=tk.X)
        self.sN_gF_nameFrame.pack(side=tk.TOP, fill=tk.X)
        self.sN_gF_mapsizeXFrame = tk.Frame(self.sN_genFrame, pady=5)
        self.sN_gF_mapsizeXLabel = tk.Label(self.sN_gF_mapsizeXFrame, text='Map Width')
        self.sN_gF_mapsizeXLabel.pack(side=tk.LEFT)
        #self.vcmd_str = (self.register(self.callback_entryStr))
        self.sN_gF_mapsizeXEntry = tk.Entry(self.sN_gF_mapsizeXFrame, text=self.mapSizeX.get(), textvariable=self.mapSizeX)#, validate='key', validatecommand=self.callback_name)
        self.sN_gF_mapsizeXEntry.bind('<Return>', self.callback_mapSizeX)
        self.sN_gF_mapsizeXEntry.pack(side=tk.LEFT, fill=tk.X)
        self.sN_gF_mapsizeXFrame.pack(side=tk.TOP, fill=tk.X)
        self.sN_gF_mapsizeYFrame = tk.Frame(self.sN_genFrame, pady=5)
        self.sN_gF_mapsizeYLabel = tk.Label(self.sN_gF_mapsizeYFrame, text='Map Height')
        self.sN_gF_mapsizeYLabel.pack(side=tk.LEFT)
        #self.vcmd_str = (self.register(self.callback_entryStr))
        self.sN_gF_mapsizeYEntry = tk.Entry(self.sN_gF_mapsizeYFrame, text=self.mapSizeY.get(), textvariable=self.mapSizeY)#, validate='key', validatecommand=self.callback_name)
        self.sN_gF_mapsizeYEntry.bind('<Return>', self.callback_mapSizeY)
        self.sN_gF_mapsizeYEntry.pack(side=tk.LEFT, fill=tk.X)
        self.sN_gF_mapsizeYFrame.pack(side=tk.TOP, fill=tk.X)
        self.sN_gF_moveFrame = tk.LabelFrame(self.sN_genFrame, text="Translate the map", padx=2, pady=2)
        self.sN_gF_moveMapButton_up = tk.Button(self.sN_gF_moveFrame, text="UP", bg='#FFEEDD', width=12, command=self.moveMapUp).grid(row=0, column=1)
        self.sN_gF_moveMapButton_left = tk.Button(self.sN_gF_moveFrame, text="LEFT", bg='#FFEEDD', width=12, command=self.moveMapLeft).grid(row=1, column=0)
        self.sN_gF_moveMapButton_right = tk.Button(self.sN_gF_moveFrame, text="RIGHT", bg='#FFEEDD', width=12, command=self.moveMapRight).grid(row=1, column=2)
        self.sN_gF_moveMapButton_down = tk.Button(self.sN_gF_moveFrame, text="DOWN", bg='#FFEEDD', width=12, command=self.moveMapDown).grid(row=2, column=1)
        
        self.sN_gF_moveFrame.pack(side=tk.TOP, fill=tk.X)
        
        
        self.sN_gF_saveButton = tk.Button(self.sN_genFrame, text="Export map", bg='#BBFFBB', height=1, pady=10, command=self.saveMap)
        self.sN_gF_saveButton.pack(side=tk.BOTTOM, fill=tk.X)
        self.sN_gF_loadButton = tk.Button(self.sN_genFrame, text="Import map", bg='#FFFFBB', height=1, pady=10, command=self.loadMap)
        self.sN_gF_loadButton.pack(side=tk.BOTTOM, fill=tk.X)
        self.sN_gF_newButton = tk.Button(self.sN_genFrame, text="New map", bg='#CCCCFF', height=1, pady=10, command=self.newMap)
        self.sN_gF_newButton.pack(side=tk.BOTTOM, fill=tk.X)
        self.sN_genFrame.pack(side=tk.TOP, fill=tk.X)
        self.settingNotebook.add(self.sN_genFrame, text='General')
        
        self.sN_tileFrame = tk.Frame(self.settingNotebook)
        self.sN_tF_layerFrame = tk.LabelFrame(self.sN_tileFrame, text="Working layer", padx=2, pady=2)
        self.sN_tF_layerBGFrame = tk.Frame(self.sN_tF_layerFrame)
        self.sN_tF_layerBGRadiobutton = tk.Radiobutton(self.sN_tF_layerBGFrame, text="Background",padx = 20, variable=self.editedLayer, value=1, command=self.selectLayer)#.pack(anchor=tk.W)
        self.sN_tF_layerBGRadiobutton.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        self.sN_tF_layerBGCheckbutton = tk.Checkbutton(self.sN_tF_layerBGFrame, text="", variable=self.visibleLayer_bg, command=self.set_visibleLayer)
        self.sN_tF_layerBGCheckbutton.pack(side=tk.RIGHT)
        self.sN_tF_layerBGFrame.pack(side=tk.TOP, fill=tk.X)
        self.sN_tF_layerFGFrame = tk.Frame(self.sN_tF_layerFrame)
        self.sN_tF_layerFGRadiobutton = tk.Radiobutton(self.sN_tF_layerFGFrame, text="Foreground",padx = 20, variable=self.editedLayer, value=2, command=self.selectLayer)#.pack(anchor=tk.W)
        self.sN_tF_layerFGRadiobutton.pack(side=tk.LEFT, fill=tk.X, anchor=tk.W)
        self.sN_tF_layerFGCheckbutton = tk.Checkbutton(self.sN_tF_layerFGFrame, text="", variable=self.visibleLayer_fg, command=self.set_visibleLayer)
        self.sN_tF_layerFGCheckbutton.pack(side=tk.RIGHT)
        self.sN_tF_layerFGFrame.pack(side=tk.TOP, fill=tk.X)
        self.sN_tF_layerFrame.pack(side=tk.TOP, fill=tk.X)
        self.editedLayer.set(1)
        self.sN_tF_themeList = ttk.Combobox(self.sN_tileFrame, state="readonly", values=self.tileThemes)
        self.sN_tF_themeList.bind("<<ComboboxSelected>>", self.chooseTileTheme)
        self.sN_tF_themeList.pack(side=tk.TOP, anchor=tk.N)
        self.canvas = tk.Canvas(self.sN_tileFrame, bg = 'white')
        self.sN_tF_tileList = tk.Frame(self.canvas, bg = 'white')
        self.canvas.create_window((0, 0), window=self.sN_tF_tileList, anchor="n")
        self.tiles_scroll = ttk.Scrollbar(self.canvas, orient = "vertical", 
            command = self.canvas.yview)
        self.tiles_scroll.pack(side = tk.RIGHT, fill = tk.Y)
        self.canvas.config(yscrollcommand = self.tiles_scroll.set)
        self.sN_tF_tileList.bind("<Configure>", self.OnFrameConfigure)
        self.sN_tF_tileList.bind_all("<MouseWheel>", self.OnFrameConfigureScroll)
        self.canvas.pack(side = tk.RIGHT, fill = tk.BOTH, expand = True)
        for i in range(self.tilesLib_maxsize):
            self.tileMenuButton.append(
                tk.Button(self.sN_tF_tileList, text="", width=280,#self.tilesLib_buttonsize, 
                          anchor='w', compound='left' ) )
            self.tileMenuButton[i].bind('<Enter>', self.OnMouseOver)
        self.sN_tileFrame.pack(side=tk.TOP, fill=tk.X)
        self.settingNotebook.add(self.sN_tileFrame, text='Tiles')
        
        self.sN_objFrame = tk.Frame(self.settingNotebook)
        self.sN_objFrame.pack(side=tk.TOP, fill=tk.X)
        self.settingNotebook.add(self.sN_objFrame, text='Objects')
        
        self.sN_wallFrame = tk.Frame(self.settingNotebook)
        self.sN_wF_tree = ttk.Treeview(self.sN_wallFrame)
        self.sN_wF_tree.pack(side=tk.LEFT, fill=tk.BOTH)
        self.sN_wF_vsb = ttk.Scrollbar(self.sN_wallFrame, orient="vertical", command=self.sN_wF_tree.yview)
        self.sN_wF_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.sN_wF_tree.configure(yscrollcommand=self.sN_wF_vsb.set)
        self.sN_wF_tree["columns"]=("x1","y1","x2","y2")
        self.sN_wF_tree.column("#0", width=0, minwidth=0, stretch=False)
        self.sN_wF_tree.column("x1", width=65, minwidth=65, stretch=False)
        self.sN_wF_tree.column("y1", width=65, minwidth=65, stretch=False)
        self.sN_wF_tree.column("x2", width=65, minwidth=65, stretch=False)
        self.sN_wF_tree.column("y2", width=65, minwidth=65, stretch=False)
        self.sN_wF_tree.heading("#0",text="")
        self.sN_wF_tree.heading("x1", text="x1",anchor=tk.W)
        self.sN_wF_tree.heading("y1", text="y1",anchor=tk.W)
        self.sN_wF_tree.heading("x2", text="x2",anchor=tk.W)
        self.sN_wF_tree.heading("y2", text="y2",anchor=tk.W)
        self.sN_wF_tree.tag_bind('wall', '<<TreeviewSelect>>', self.select_wallTree)
        self.sN_wF_tree.tag_bind('wall', '<KeyPress>', self.remove_wallTree)
        #self.sN_wF_tree.tag_bind('wall', '<<TreeviewClose>>', self.looseFocus_wallTree)
        #self.sN_wF_tree.pack(side=tk.TOP,fill=tk.X)
        self.sN_wallFrame.pack(side=tk.TOP, fill=tk.X)
        self.settingNotebook.add(self.sN_wallFrame, text='Walls')
        
        self.settingNotebook.bind('<<NotebookTabChanged>>', self.on_sNtab_change)
        self.settingNotebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.infoPanel = tk.Frame(self.settingPanel)
        self.infoXpos = tk.Label(self.infoPanel, padx = 5)
        self.infoXpos.pack(side=tk.LEFT)
        self.infoYpos = tk.Label(self.infoPanel, padx = 5)
        self.infoYpos.pack(side=tk.LEFT)
        self.infoPanel.pack(side=tk.BOTTOM, fill=tk.X)
        self.settingPanel.pack(side=tk.RIGHT, fill=tk.BOTH)
        
    
    # def FrameWidth(self, event):
    #     canvas_width = event.width
    #     self.canvas.itemconfig(self.canvas_frame, width = canvas_width)

    def OnFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    
    def OnFrameConfigureScroll(self, event):
        direction = 0
        if event.num == 5 or event.delta == -120:
         direction = 1
        if event.num == 4 or event.delta == 120:
         direction = -1
        self.canvas.yview_scroll(direction, tk.UNITS)
    
    
    def setEdgeTiles(self):
        topleft = [0, 0]
        canvasRatio = self.width / self.height
        mapRatio = self.mapW / self.mapH
        if (mapRatio > canvasRatio):
            print("width full and set the tile size, height centering")
            if (self.width > self.mapW*TILESIZE_MAX):
                self.tileSize = TILESIZE_MAX
                topleft[0] = int((self.width - self.mapW*self.tileSize)/2)
            else:
                self.tileSize = int((self.width / self.mapW))
                topleft[0] = 0
            topleft[1] = int((self.height - self.mapH*self.tileSize)/2)
        else:
            print("height full and set the tile size, width centering")
            if (self.height > self.mapH*TILESIZE_MAX):
                self.tileSize = TILESIZE_MAX
                topleft[1] = int((self.height - self.mapH*self.tileSize)/2)
            else:
                self.tileSize = int((self.height / self.mapH))
                topleft[1] = 0
            topleft[0] = int((self.width - self.mapW*self.tileSize)/2)
    
        for i in range(self.mapW+1):
            for j in range(self.mapH+1):
                self.mapEdgeX[i][j] = topleft[0] + i*self.tileSize
                self.mapEdgeY[i][j] = topleft[1] + j*self.tileSize
        
        for d in self.tileThemes:
            for i in range(len(self.tilesLib[d])):
                f = self.tilesLib[d][i]
                filepath = os.path.join(TILETHEME_DIR, os.path.join(d, f))
                if os.path.isfile(filepath):
                    self.tilesPhoto[d][i] = ImageTk.PhotoImage(Image.open(filepath).resize((self.tileSize, self.tileSize), Image.ANTIALIAS))   #"grass.bmp") ))
                    self.tilesPhotoFG[d][i] = ImageTk.PhotoImage(white_to_transparency(Image.open(filepath)).resize((self.tileSize, self.tileSize), Image.ANTIALIAS))   #"grass.bmp") ))
                    
        return
    
    
    def drawMonitor(self):
        self.canv.delete("all")
        
        # Draw the tiles Background
        if((self.tileMenu and self.BGvisible) or not self.tileMenu):
            for i in range(self.mapW):
                for j in range(self.mapH):
                    if self.map[i][j][0] == "":
                        self.canv.create_rectangle(self.mapEdgeX[i][j], self.mapEdgeY[i][j],
                                                   self.mapEdgeX[i+1][j+1], self.mapEdgeY[i+1][j+1], fill=CANVAS_NULLTILE_COLOR)
                    else:
                        if True:#self.map_id[i][j] < len(self.tilesPhoto[self.map_str[i][j]]):
                            self.canv.create_image(self.mapEdgeX[i][j], self.mapEdgeY[i][j], image = self.tilesPhoto[self.map[i][j][0]][self.map[i][j][1]] , anchor = "nw" )
                        else:
                            self.canv.create_rectangle(self.mapEdgeX[i][j], self.mapEdgeY[i][j],
                                                       self.mapEdgeX[i+1][j+1], self.mapEdgeY[i+1][j+1], fill=CANVAS_NULLTILE_COLOR)
                
        # Draw the tiles Foreground
        if((self.tileMenu and self.FGvisible) or not self.tileMenu):
            for i in range(self.mapW):
                for j in range(self.mapH):
                    if self.mapFG[i][j][0] == "":
                        pass
                        # self.canv.create_rectangle(self.mapEdgeX[i][j], self.mapEdgeY[i][j],
                        #                            self.mapEdgeX[i+1][j+1], self.mapEdgeY[i+1][j+1], fill=CANVAS_NULLTILE_COLOR)
                    else:
                        if True:#self.map_id[i][j] < len(self.tilesPhoto[self.map_str[i][j]]):
                            self.canv.create_image(self.mapEdgeX[i][j], self.mapEdgeY[i][j], image = self.tilesPhotoFG[self.mapFG[i][j][0]][self.mapFG[i][j][1]] , anchor = "nw" )
                        else:
                            pass
                            # self.canv.create_rectangle(self.mapEdgeX[i][j], self.mapEdgeY[i][j],
                            #                            self.mapEdgeX[i+1][j+1], self.mapEdgeY[i+1][j+1], fill=CANVAS_NULLTILE_COLOR)
                
        
        # Draw the grid
        for i in range(self.mapW+1):
            self.canv.create_line(self.mapEdgeX[i][0], self.mapEdgeY[i][0], 
                                  self.mapEdgeX[i][-1], self.mapEdgeY[i][-1], 
                                  fill=CANVAS_GRID_COLOR, dash=(2, 2))
        for i in range(self.mapH+1):
            self.canv.create_line(self.mapEdgeX[0][i], self.mapEdgeY[0][i], 
                                  self.mapEdgeX[-1][i], self.mapEdgeY[-1][i], 
                                  fill=CANVAS_GRID_COLOR, dash=(2, 2))
        
        
        # Draw the walls
        if (len(self.walls) > 0):
            for i in range(len(self.walls)):
                x1 = self.walls[i][0]*self.tileSize + self.mapEdgeX[0][0]
                y1 = self.walls[i][1]*self.tileSize + self.mapEdgeY[0][0]
                x2 = self.walls[i][2]*self.tileSize + self.mapEdgeX[0][0]
                y2 = self.walls[i][3]*self.tileSize + self.mapEdgeY[0][0]
                if self.selectingWall and i == self.selectedWall:
                    self.canv.create_line(x1, y1, x2, y2, fill='#FFFFFF', width=2)
                else:
                    self.canv.create_line(x1, y1, x2, y2, fill='#AAAAAA', width=1)
        
            
        # Draw the canvCursor, if tileMenu is True
        if self.tileMenu:
            self.canv.create_rectangle(self.mapEdgeX[self.canvCursor[0]][self.canvCursor[1]], self.mapEdgeY[self.canvCursor[0]][self.canvCursor[1]],
                                      self.mapEdgeX[self.canvCursor[0]+self.canvCursorExtend[0]][self.canvCursor[1]+self.canvCursorExtend[1]], self.mapEdgeY[self.canvCursor[0]+self.canvCursorExtend[0]][self.canvCursor[1]+self.canvCursorExtend[1]],
                                      outline = '#FF0000', width=2)
        
        
        if self.wallMenu:
            if self.wallWebbing:
                x1 = self.wallBeginX*self.tileSize + self.mapEdgeX[0][0]
                y1 = self.wallBeginY*self.tileSize + self.mapEdgeY[0][0]
                x2 = self.canvMouseX*self.tileSize + self.mapEdgeX[0][0]
                y2 = self.canvMouseY*self.tileSize + self.mapEdgeY[0][0]
                self.canv.create_line(x1, y1, x2, y2, fill='#FFFFFF', width=1)
            x = self.canvMouseX*self.tileSize + self.mapEdgeX[0][0]
            y = self.canvMouseY*self.tileSize + self.mapEdgeY[0][0]
            self.canv.create_line(x - CURSOR_SIZE/2, y, x + CURSOR_SIZE/2, y, fill = '#FFFFFF', width=3)
            self.canv.create_line(x, y - CURSOR_SIZE/2, x, y + CURSOR_SIZE/2, fill = '#FFFFFF', width=3)
            
        return
        
    
    def selectLayer(self):
        # for i in range(self.tilesLib_maxsize):
        #     self.tileMenuButton[i].pack_forget()
        
        if len(self.tileMenuButton) > 0 and self.tileTheme != 0:
            self.tileTheme = self.sN_tF_themeList.get()
            #print(self.tilesLib[self.tileTheme])
            for i in range(self.tilesLib_maxsize):
                if i < len(self.tilesLib[self.tileTheme]):
                    if self.editedLayer.get() == 1:
                        self.tileMenuButton[i].configure(image=self.tileMenuPhoto[self.tileTheme][i])
                    elif self.editedLayer.get() == 2:
                        self.tileMenuButton[i].configure(image=self.tileMenuPhotoFG[self.tileTheme][i])
                    # self.tileMenuButton[i].pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
    
    
    def set_visibleLayer(self):
        if(self.visibleLayer_bg.get() == 1):
            self.BGvisible = True
        else:
            self.BGvisible = False
        if(self.visibleLayer_fg.get() == 1):
            self.FGvisible = True
        else:
            self.FGvisible = False
        self.drawMonitor()
        
    
    
    def chooseTileTheme(self, event):
        for i in range(self.tilesLib_maxsize):
            self.tileMenuButton[i].pack_forget()
        
        self.tileTheme = self.sN_tF_themeList.get()
        #print(self.tilesLib[self.tileTheme])
        for i in range(self.tilesLib_maxsize):
            if i < len(self.tilesLib[self.tileTheme]):
                if self.editedLayer.get() == 1:
                    self.tileMenuButton[i].configure(text=self.tilesLib[self.tileTheme][i], compound='left', width=280, #self.tilesLib_buttonsize,
                                                  image=self.tileMenuPhoto[self.tileTheme][i],
                                                  command=self.pasteTile)#tk.PhotoImage(file="grass.gif"))#img)) 
                elif self.selectedLayer.get() == 2:
                    self.tileMenuButton[i].configure(text=self.tilesLib[self.tileTheme][i], compound='left', width=280, #self.tilesLib_buttonsize,
                                                  image=self.tileMenuPhotoFG[self.tileTheme][i],
                                                  command=self.pasteTile)#tk.PhotoImage(file="grass.gif"))#img)) 
                #self.tileMenuButton[i].image = self.photo #tk.PhotoImage(file="grass.gif")
                self.tileMenuButton[i].pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
            
            
        self.canv.focus_set()
        self.drawMonitor()
        
        
    def OnMouseOver(self, event):
        self.tileTobepasted = event.widget['text']
    
    
    
    def pasteTile(self):
        """action in event of button 1 on tree view"""
        # select row under mouse
        f = self.tileTobepasted
        # for i in range(len(self.tilesLib[self.tileTheme])):
        #     print(str(self.tileMenuButton[i]['state']))# == :
                #f = self.tilesLib[self.tileTheme][i]
               # break
        item = os.path.join(self.tileTheme, f) #+ self.text
        
        if item:
            # mouse pointer over item
            #print("you clicked on {0}".format(item )  )
            #self.map_str[self.canvCursor[0]][self.canvCursor[1]] = self.tileTheme
            #self.map_id[self.canvCursor[0]][self.canvCursor[1]] = self.tilesLib[self.tileTheme].index(f)
            if self.editedLayer.get() == 1:
                print("paste tile on layer BACKGROUND")
                for i in range(self.canvCursorExtend[0]):
                    for j in range(self.canvCursorExtend[1]):
                        self.map[self.canvCursor[0] + i][self.canvCursor[1] + j][0] = self.tileTheme
                        self.map[self.canvCursor[0] + i][self.canvCursor[1] + j][1] = self.tilesLib[self.tileTheme].index(f)
            elif self.editedLayer.get() == 2:
                print("paste tile on layer FOREGROUND")
                for i in range(self.canvCursorExtend[0]):
                    for j in range(self.canvCursorExtend[1]):
                        self.mapFG[self.canvCursor[0] + i][self.canvCursor[1] + j][0] = self.tileTheme
                        self.mapFG[self.canvCursor[0] + i][self.canvCursor[1] + j][1] = self.tilesLib[self.tileTheme].index(f)
            #print("map_str: {0}".format(self.map[self.canvCursor[0]][self.canvCursor[1]][0]))
            #print("map_id:  {0}".format(self.map[self.canvCursor[0]][self.canvCursor[1]][1]))
            
            #self.sN_tF_tileList.selection_set(iid)
            #self.contextMenu.post(event.x_root, event.y_root)            
        else:
            print("click not identified")
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            
        self.canv.focus_set()
        self.drawMonitor()
        self.canv.focus_set()
        
    
    def addWall(self):
        self.walls.append([self.wallBeginX, self.wallBeginY, self.wallEndX, self.wallEndY])
        self.sN_wF_tree.insert("", 'end', "{0}".format(len(self.walls)-1), 
                               text="",#"{0}".format(len(self.walls)-1), 
                               values=("{0:.1f}".format(self.wallBeginX), "{0:.1f}".format(self.wallBeginY), 
                                       "{0:.1f}".format(self.wallEndX), "{0:.1f}".format(self.wallEndY) ),
                               tags = ('wall') )
        
    
    def remove_wallTree(self, event):
        #print("process keypress event")
        if self.wallMenu:
            #print("process keypress event")
            if event.keysym == 'BackSpace':
                if self.selectingWall:
                    #print('removing wall {0} temptative'.format(self.selectedWall))
                    for i in range(self.selectedWall, len(self.walls)):
                        if i < len(self.walls)-1:
                            itemToReplace = str(i)
                            itemToCopy = str(i+1)
                            #print(self.sN_wF_tree.set( itemToCopy ))
                            # self.sN_wF_tree.delete(itemToReplace)
                            # self.sN_wF_tree.insert("", i+1, itemToReplace, 
                            #    text=self.sN_wF_tree.set( itemToCopy )["#0"], 
                            #    values=(self.sN_wF_tree.set( itemToCopy , "y1"), self.sN_wF_tree.set( itemToCopy , "x2"), self.sN_wF_tree.set( itemToCopy , "y2")),
                            #    tags = ('wall') )
                            self.sN_wF_tree.set( itemToReplace , "x1" , self.sN_wF_tree.set( itemToCopy , "x1") )
                            self.sN_wF_tree.set( itemToReplace , "y1" , self.sN_wF_tree.set( itemToCopy , "y1") )
                            self.sN_wF_tree.set( itemToReplace , "x2" , self.sN_wF_tree.set( itemToCopy , "x2") )
                            self.sN_wF_tree.set( itemToReplace , "y2" , self.sN_wF_tree.set( itemToCopy , "y2") )
                    self.sN_wF_tree.delete(str(len(self.walls)-1))
                    del self.walls[self.selectedWall]
                    self.looseFocus_wallTree()
                    self.drawMonitor()
                    
    def newMap(self):
        N_ = len(self.walls)
        if(N_ > 0):
            for i in range(N_):
                self.sN_wF_tree.delete(str(len(self.walls)-1))
                self.walls.pop(len(self.walls)-1)
        self.canvCursor = [0, 0]
        self.canvCursorExtend = [1, 1]
        self.mapName.set('default name')
        self.mapW = 8
        self.mapH = 6
        self.mapSizeX.set(str(self.mapW))
        self.mapSizeY.set(str(self.mapH))
        self.set_mapSizeX()
        self.set_mapSizeY()
        for i in range(self.mapW):
            for j in range(self.mapH):
                self.map[i][j][0] = ""
                self.map[i][j][1] = 0
                self.mapFG[i][j][0] = ""
                self.mapFG[i][j][1] = 0
        self.drawMonitor()
        
        
    def moveMapDown(self):
        for i in range(self.mapW):
            for j in range(self.mapH - 1):
                self.map[i][self.mapH - 1 - j][0] = self.map[i][self.mapH - 2 - j][0]
                self.map[i][self.mapH - 1 - j][1] = self.map[i][self.mapH - 2 - j][1]
                self.mapFG[i][self.mapH - 1 - j][0] = self.mapFG[i][self.mapH - 2 - j][0]
                self.mapFG[i][self.mapH - 1 - j][1] = self.mapFG[i][self.mapH - 2 - j][1]
            self.map[i][0][0] = ""
            self.map[i][0][1] = 0
            self.mapFG[i][0][0] = ""
            self.mapFG[i][0][1] = 0
        if(len(self.walls)):
            for i in range(len(self.walls)):
                self.walls[i][1] += 1
                self.walls[i][3] += 1
                self.sN_wF_tree.set( i , "x1" , self.sN_wF_tree.set( i , "x1") )
                self.sN_wF_tree.set( i , "y1" , "{0:.1f}".format(self.walls[i][1]) )
                self.sN_wF_tree.set( i , "x2" , self.sN_wF_tree.set( i , "x2") )
                self.sN_wF_tree.set( i , "y2" , "{0:.1f}".format(self.walls[i][3]) )
        self.drawMonitor()
    
    
    def moveMapUp(self):
        for i in range(self.mapW):
            for j in range(self.mapH - 1):
                self.map[i][j][0] = self.map[i][j+1][0]
                self.map[i][j][1] = self.map[i][j+1][1]
                self.mapFG[i][j][0] = self.mapFG[i][j+1][0]
                self.mapFG[i][j][1] = self.mapFG[i][j+1][1]
            self.map[i][-1][0] = ""
            self.map[i][-1][1] = 0
            self.mapFG[i][-1][0] = ""
            self.mapFG[i][-1][1] = 0
        if(len(self.walls)):
            for i in range(len(self.walls)):
                self.walls[i][1] -= 1
                self.walls[i][3] -= 1
                self.sN_wF_tree.set( i , "x1" , self.sN_wF_tree.set( i , "x1") )
                self.sN_wF_tree.set( i , "y1" , "{0:.1f}".format(self.walls[i][1]) )
                self.sN_wF_tree.set( i , "x2" , self.sN_wF_tree.set( i , "x2") )
                self.sN_wF_tree.set( i , "y2" , "{0:.1f}".format(self.walls[i][3]) )
        self.drawMonitor()
    
    
    def moveMapLeft(self):
        for j in range(self.mapH):
            for i in range(self.mapW - 1):
                self.map[i][j][0] = self.map[i+1][j][0]
                self.map[i][j][1] = self.map[i+1][j][1]
                self.mapFG[i][j][0] = self.mapFG[i+1][j][0]
                self.mapFG[i][j][1] = self.mapFG[i+1][j][1]
            self.map[-1][j][0] = ""
            self.map[-1][j][1] = 0
            self.mapFG[-1][j][0] = ""
            self.mapFG[-1][j][1] = 0
        if(len(self.walls)):
            for i in range(len(self.walls)):
                self.walls[i][0] -= 1
                self.walls[i][2] -= 1
                self.sN_wF_tree.set( i , "x1" , "{0:.1f}".format(self.walls[i][0]) )
                self.sN_wF_tree.set( i , "y1" , "{0:.1f}".format(self.walls[i][1]) )
                self.sN_wF_tree.set( i , "x2" , "{0:.1f}".format(self.walls[i][2]) )
                self.sN_wF_tree.set( i , "y2" , "{0:.1f}".format(self.walls[i][3]) )
        self.drawMonitor()
    
    
    def moveMapRight(self):
        for j in range(self.mapH):
            for i in range(self.mapW - 1):
                self.map[self.mapW - 1 - i][j][0] = self.map[self.mapW - 2 - i][j][0]
                self.map[self.mapW - 1 - i][j][1] = self.map[self.mapW - 2 - i][j][1]
                self.mapFG[self.mapW - 1 - i][j][0] = self.mapFG[self.mapW - 2 - i][j][0]
                self.mapFG[self.mapW - 1 - i][j][1] = self.mapFG[self.mapW - 2 - i][j][1]
            self.map[0][j][0] = ""
            self.map[0][j][1] = 0
            self.mapFG[0][j][0] = ""
            self.mapFG[0][j][1] = 0
        if(len(self.walls)):
            for i in range(len(self.walls)):
                self.walls[i][0] += 1
                self.walls[i][2] += 1
                self.sN_wF_tree.set( i , "x1" , "{0:.1f}".format(self.walls[i][0]) )
                self.sN_wF_tree.set( i , "y1" , "{0:.1f}".format(self.walls[i][1]) )
                self.sN_wF_tree.set( i , "x2" , "{0:.1f}".format(self.walls[i][2]) )
                self.sN_wF_tree.set( i , "y2" , "{0:.1f}".format(self.walls[i][3]) )
        self.drawMonitor()
    
    
    def canvMotion(self, event):
        #x, y = event.x, event.y
        self.canvMouseX = int(((event.x - self.mapEdgeX[0][0]) / self.tileSize) / CURSOR_STEP) * CURSOR_STEP
        self.canvMouseY = int(((event.y - self.mapEdgeY[0][0]) / self.tileSize) / CURSOR_STEP) * CURSOR_STEP
        if self.wallMenu:
            self.drawMonitor()
        #print('{0:.2f}, {1:.2f}'.format(x, y))
        self.infoXpos.configure(text="X = {0:.2f}".format(self.canvMouseX - 0.5))
        self.infoYpos.configure(text="Y = {0:.2f}".format(self.canvMouseY - 0.5))
        
        time.sleep(0.025)
        
        
    def canvClick(self, event):
        if self.wallMenu:
            if self.selectingWall: self.looseFocus_wallTree()
            if not self.wallWebbing:
                self.wallBeginX = self.canvMouseX
                self.wallBeginY = self.canvMouseY
                self.wallWebbing = True
            else:
                self.wallEndX = self.canvMouseX
                self.wallEndY = self.canvMouseY
                self.wallWebbing = False
                self.addWall()
            self.drawMonitor()
    
    
    def canvCursorKey(self, event):
        #print("process keypress event")
        if self.tileMenu:
            
            if event.state == 0x0004 or event.state == 0x0001:#'Control' or 'Maj':
                #print("event: %s"%str(event))
                if event.keycode == 68: #'d':
                    if self.canvCursor[0] < self.mapW-self.canvCursorExtend[0]:
                        self.canvCursorExtend[0] += 1
                elif event.keycode == 65: #'a':
                    if self.canvCursorExtend[0] > 1:
                        self.canvCursorExtend[0] -= 1
                elif event.keycode == 83: #'s':
                    if self.canvCursor[1] < self.mapH-self.canvCursorExtend[1]:
                        self.canvCursorExtend[1] += 1
                elif event.keycode == 87: #'w':
                    if self.canvCursorExtend[1] > 1:
                        self.canvCursorExtend[1] -= 1
            else:
                #print("event: %s"%str(event))
                if event.keycode == 68: #'d':
                    if self.canvCursor[0] < self.mapW-self.canvCursorExtend[0]:
                        self.canvCursor[0] += 1
                elif event.keycode == 65: #'a':
                    if self.canvCursor[0] > 0:
                        self.canvCursor[0] -= 1
                elif event.keycode == 83: #'s':
                    if self.canvCursor[1] < self.mapH-self.canvCursorExtend[1]:
                        self.canvCursor[1] += 1
                elif event.keycode == 87: #'w':
                    if self.canvCursor[1] > 0:
                        self.canvCursor[1] -= 1
            self.drawMonitor()
            
    
        
            
    
    # def canvCursorExtKey(self, event):
    #     #print("process keypress event")
    #     if self.tileMenu:
    #         #print("process keypress event")
    #         if event.char == 'd':
    #             if self.canvCursor[0] < self.mapW-self.canvCursorExtend[0]:
    #                 self.canvCursorExtend[0] += 1
    #         elif event.char == 'a':
    #             if self.canvCursorExtend[0] > 1:
    #                 self.canvCursorExtend[0] -= 1
    #         elif event.char == 's':
    #             if self.canvCursor[1] < self.mapH-self.canvCursorExtend[1]:
    #                 self.canvCursorExtend[1] += 1
    #         elif event.char == 'w':
    #             if self.canvCursorExtend[1] > 1:
    #                 self.canvCursorExtend[1] -= 1
    #         self.drawMonitor()
            
    
    def removeTile(self, event):
        if self.tileMenu:
            if self.editedLayer.get() == 1:
                for i in range(self.canvCursorExtend[0]):
                    for j in range(self.canvCursorExtend[1]):
                        self.map[self.canvCursor[0] + i][self.canvCursor[1] + j][0] = ""
                        self.map[self.canvCursor[0] + i][self.canvCursor[1] + j][1] = 0
            elif self.editedLayer.get() == 2:
                for i in range(self.canvCursorExtend[0]):
                    for j in range(self.canvCursorExtend[1]):
                        self.mapFG[self.canvCursor[0] + i][self.canvCursor[1] + j][0] = ""
                        self.mapFG[self.canvCursor[0] + i][self.canvCursor[1] + j][1] = 0
        self.drawMonitor()
            
            
    def looseFocus_wallTree(self):
        self.selectingWall = False
        if len(self.sN_wF_tree.selection()) > 0:
            self.sN_wF_tree.selection_remove(self.sN_wF_tree.selection()[0])


    def select_wallTree(self, event):
        if len(self.sN_wF_tree.selection()) > 0:
            self.selectingWall = True
            self.selectedWall = int(self.sN_wF_tree.selection()[0])
            #print('wall selected: {0}'.format(self.selectedWall))
        else:
            self.selectingWall = False
            self.selectedWall = 0
            #print('wall deselected')
        self.drawMonitor()
        
        
    # def callback_name(self):
    #     print('setting map name')
    #     text = self.mapName.get()
    #     if len(text) == 0:
    #         return False
    #     else:
    #         return True
    #         # self.mapName.set('name')
    #         # self.sN_gF_nameEntry.selection_clear()


    def set_mapName(self, event):
        if event.keysym == 'Return':
            text = self.mapName.get()
            if len(text) == 0:
                self.mapName.set('name')
            self.canv.focus_set()


    def callback_mapSizeX(self, event):
        if event.keysym == 'Return':
            text = self.mapSizeX.get()
            if len(text) == 0:
                self.mapSizeX.set(str(self.mapW))
            else:
                try:
                    self.mapW = int(text)
                except:
                    self.mapSizeX.set(str(self.mapW))
                    self.canv.focus_set()
                    return
            if self.mapW < 3:
                self.mapW = 3
            self.set_mapSizeX()
            self.drawMonitor()
            self.canv.focus_set()
        
        
    def set_mapSizeX(self):
        m = self.map.copy()
        mFG = self.map.copy()
        self.map = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        self.mapFG = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        for i in range(self.mapW):
            for j in range(self.mapH):
                if i < len(m) and j < len(m[0]):
                    self.map[i][j][0] = m[i][j][0]
                    self.map[i][j][1] = m[i][j][1]
                    self.mapFG[i][j][0] = mFG[i][j][0]
                    self.mapFG[i][j][1] = mFG[i][j][1]
        self.mapEdgeX = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.mapEdgeY = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.setEdgeTiles()
        



    def callback_mapSizeY(self, event):
        if event.keysym == 'Return':
            text = self.mapSizeY.get()
            if len(text) == 0:
                self.mapSizeY.set(str(self.mapH))
            else:
                try:
                    self.mapH = int(text)
                except:
                    self.mapSizeY.set(str(self.mapH))
                    self.canv.focus_set()
                    return
            if self.mapH < 3:
                self.mapH = 3
            self.set_mapSizeY()
            self.drawMonitor()
            self.canv.focus_set()
            
            
    def set_mapSizeY(self):
        m = self.map.copy()
        mFG = self.map.copy()
        self.map = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        self.mapFG = [[["", 0]  for j in range(self.mapH)]  for i in range(self.mapW)]
        for i in range(self.mapW):
            for j in range(self.mapH):
                if i < len(m) and j < len(m[0]):
                    self.map[i][j][0] = m[i][j][0]
                    self.map[i][j][1] = m[i][j][1]
                    self.mapFG[i][j][0] = mFG[i][j][0]
                    self.mapFG[i][j][1] = mFG[i][j][1]
        self.mapEdgeX = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.mapEdgeY = np.zeros((self.mapW+1, self.mapH+1), dtype=int)
        self.setEdgeTiles()
        


    def on_sNtab_change(self, event):
        if self.wallMenu: self.looseFocus_wallTree()
        
        if self.settingNotebook.index(self.settingNotebook.select()) == 0: self.selectGenMenu()
        elif self.settingNotebook.index(self.settingNotebook.select()) == 1: self.selectTileMenu()
        elif self.settingNotebook.index(self.settingNotebook.select()) == 2: self.selectObjMenu()
        elif self.settingNotebook.index(self.settingNotebook.select()) == 3: self.selectWallMenu()
        else: self.selectGenMenu()
        #self.selectingWall = False
        self.drawMonitor()
        
    
    
    def selectGenMenu(self):
        self.genMenu = True
        self.tileMenu = False
        self.objMenu = False
        self.wallMenu = False
        self.canv.focus_set()
        
    def selectTileMenu(self):
        self.genMenu = False
        self.tileMenu = True
        self.objMenu = False
        self.wallMenu = False
        self.canv.focus_set()
        
    def selectObjMenu(self):
        self.genMenu = False
        self.tileMenu = False
        self.objMenu = True
        self.wallMenu = False
        self.canv.focus_set()
        
    def selectWallMenu(self):
        self.genMenu = False
        self.tileMenu = False
        self.objMenu = False
        self.wallMenu = True
        self.canv.focus_set()
        
        
        
    def loadMap(self):
        filename = askopenfilename(title="Export Map",
                                    initialdir = pathlib.Path(__file__).parent.absolute(),
                                    defaultextension='.map', filetypes=[("map files", '*.map')])
        
        if filename == "":
            return
        f = open(filename, 'r')
        lines = f.readlines()
        i = 0
        Ntiles = 0
        tileDic = {}
        Nwalls = 0
        loadingMobsUtil = False
        loadingClickobjsUtil = False
        while(i < len(lines)):
            if lines[i][0] != '!':
                buffer = lines[i].split(' = ')
                
                if buffer[0] == 'NAME':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.mapName.set(buffer[1])
                    i += 1
                elif buffer[0] == 'TILES':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    Ntiles = int(buffer[1])
                    i += 1
                    for j in range(Ntiles):
                        buffer = lines[i].split(' ')
                        while('' in buffer): buffer.remove('')
                        buffer[-1] = buffer[-1][:-1]
                        #print(buffer)
                        if len(buffer) == 2:
                            tileDic[buffer[0]] = [buffer[1], ""]
                        elif len(buffer) == 3:
                            tileDic[buffer[0]] = [buffer[1], buffer[2]]
                        i += 1
                elif buffer[0] == 'ORIGIN':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    coord = buffer[1].split(',')
                    self.oriX = float(coord[0])
                    self.oriY = float(coord[1])
                    i += 1
                elif buffer[0] == 'MAP':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    coord = buffer[1].split(',')
                    self.mapW = int(coord[0])
                    self.mapH = int(coord[1])
                    self.mapSizeX.set(str(self.mapW))
                    self.mapSizeY.set(str(self.mapH))
                    self.set_mapSizeX()
                    self.set_mapSizeY()
                    i += 1
                    for j in range(self.mapH):
                        buffer = lines[i].split(' ')
                        while('' in buffer): buffer.remove('')
                        buffer[-1] = buffer[-1][:-1]
                        #print(buffer)
                        for k in range(len(buffer)):
                            if buffer[k] != '-':
                                tilestoload = tileDic[buffer[k]]
                                if tilestoload[0].split('/')[0] in self.tilesLib.keys():
                                    self.map[k][j][0] = tilestoload[0].split('/')[0]
                                    try:
                                        self.map[k][j][1] = self.tilesLib[self.map[k][j][0]].index(tilestoload[0].split('/')[1])
                                    except:
                                        self.map[k][j][0] = ""
                                        self.map[k][j][1] = 0
                                if tilestoload[1].split('/')[0] in self.tilesLib.keys():
                                    self.mapFG[k][j][0] = tilestoload[1].split('/')[0]
                                    try:
                                        self.mapFG[k][j][1] = self.tilesLib[self.mapFG[k][j][0]].index(tilestoload[1].split('/')[1])
                                    except:
                                        self.mapFG[k][j][0] = ""
                                        self.mapFG[k][j][1] = 0
                            else:
                                self.map[k][j][0] = ""
                                self.map[k][j][1] = 0
                                self.mapFG[k][j][0] = ""
                                self.mapFG[k][j][1] = 0
                        i += 1
                elif buffer[0] == 'WALLS':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    Nwalls = int(buffer[1])
                    i += 1
                    for j in range(Nwalls):
                        buffer = lines[i].split(' ')
                        while('' in buffer): buffer.remove('')
                        buffer[-1] = buffer[-1][:-1]
                        self.wallBeginX = float(buffer[0]) + 0.5
                        self.wallBeginY = float(buffer[1]) + 0.5
                        self.wallEndX = float(buffer[2]) + 0.5
                        self.wallEndY = float(buffer[3]) + 0.5
                        self.addWall()
                        i += 1
                elif buffer[0] == 'TRANSITION':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Ntrans = int(buffer[1])
                    i += 1
                    if(self.Ntrans > 0):
                        self.keptTrans = []
                        for j in range(self.Ntrans):
                            self.keptTrans.append(lines[i])
                            i += 1
                elif buffer[0] == 'STATICOBJECTS':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Nstaticobj = int(buffer[1])
                    i += 1
                    if(self.Nstaticobj > 0):
                        self.keptStaticobj = []
                        for j in range(self.Nstaticobj):
                            self.keptStaticobj.append(lines[i])
                            i += 1
                elif buffer[0] == 'ANIMOBJECTS':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Nanimobj = int(buffer[1])
                    i += 1
                    if(self.Nanimobj > 0):
                        self.keptAnimobj = []
                        for j in range(self.Nanimobj):
                            self.keptAnimobj.append(lines[i])
                            i += 1
                elif buffer[0] == 'CLICKABLEOBJECTS':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Nclickobj = int(buffer[1])
                    i += 1
                    if(self.Nclickobj > 0):
                        self.keptClickobj = []
                        for j in range(self.Nclickobj):
                            self.keptClickobj.append(lines[i])
                            i += 1
                elif buffer[0] == 'PNJ':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Npnj = int(buffer[1])
                    i += 1
                    if(self.Npnj > 0):
                        self.keptPnj = []
                        for j in range(self.Npnj):
                            self.keptPnj.append(lines[i])
                            i += 1
                elif buffer[0] == 'MOBS':
                    loadingMobsUtil = False
                    loadingClickobjsUtil = False
                    self.Nmobs = int(buffer[1])
                    i += 1
                    if(self.Nmobs > 0):
                        self.keptMobs = []
                        for j in range(self.Nmobs):
                            self.keptMobs.append(lines[i])
                            i += 1
                elif buffer[0].strip() == 'MOBSUTIL':
                    print("mobsutil found")
                    loadingMobsUtil = True
                    loadingClickobjsUtil = False
                    i += 1
                elif buffer[0].strip() == 'CLICKOBJSUTIL':
                    print("clickobjsutil found")
                    loadingMobsUtil = False
                    loadingClickobjsUtil = True
                    i += 1
                else:
                    if loadingMobsUtil:
                        print(" mob util added")
                        self.Nmobsutil += 1
                        self.keptMobsUtil.append(lines[i])
                    elif loadingClickobjsUtil:
                        print(" clickobj util added")
                        self.Nclickobjsutil += 1
                        self.keptClickobjsUtil.append(lines[i])
                    i += 1
            else:
                i += 1
        self.drawMonitor()
            
     
    def saveMap(self):
        filename = asksaveasfilename(title="Export Map",
                                    initialdir = pathlib.Path(__file__).parent.absolute(),
                                    defaultextension='.map', filetypes=[("map files", '*.map')])
        if filename == "":
            return
        
        mapName = self.mapName.get() #"MapMaker default map"
        tileDic = {}
        mapId = -1*np.ones((self.mapW, self.mapH), dtype=int)
        idMax = 0
        Nwalls = len(self.walls)
        Ntrans = 0
        Nobj = 0
        Npnj = 0
        
        
        for j in range(self.mapH):
            for i in range(self.mapW):
                if self.map[i][j][0] in self.tilesLib.keys():
                    if self.map[i][j][1] < len(self.tilesLib[self.map[i][j][0]]):
                        tilename = str(self.map[i][j][0] + '/' + self.tilesLib[self.map[i][j][0]][self.map[i][j][1]])
                        if self.mapFG[i][j][0] != "":
                            if self.mapFG[i][j][0] in self.tilesLib.keys():
                                if self.mapFG[i][j][1] < len(self.tilesLib[self.mapFG[i][j][0]]):
                                    tilename += str(' ' + self.mapFG[i][j][0] + '/' + self.tilesLib[self.mapFG[i][j][0]][self.mapFG[i][j][1]])
                        if tilename in tileDic.keys():
                            mapId[i][j] = tileDic[tilename]
                        else:
                            tileDic[tilename] = idMax
                            mapId[i][j] = idMax
                            idMax += 1
        
        f = open(filename, 'w')
        f.write('!\n')
        f.write('! map generated by MapMaker\n')
        f.write('!\n')
        f.write('!\n')
        f.write('NAME = {0}\n'.format(mapName))
        f.write('!\n')
        f.write('TILES = {0}\n'.format(len(tileDic.keys())))
        for i in range(idMax):
            for key, value in tileDic.items():
                if value == i:
                    f.write('{0}'.format(value))
                    if value < 10:
                        f.write('   ')
                    elif value < 100:
                        f.write('  ')
                    else:
                        f.write(' ')
                    f.write(key + '\n')
                          
        f.write('!\n')
        f.write('ORIGIN = {0},{1}\n'.format(int(self.oriX), int(self.oriY)))
        f.write('!\n')
        f.write('MAP = {0},{1}\n'.format(self.mapW, self.mapH))
        for j in range(self.mapH):
            for i in range(self.mapW):
                if mapId[i][j] >= 0:
                    f.write('{0:4d}'.format(mapId[i][j]))
                else:
                    f.write('   -')
            f.write('\n')
        f.write('!\n')
        f.write('WALLS = {0}\n'.format(Nwalls))
        for i in range(Nwalls):
            for j in range(4):
                f.write('{0:.1f}'.format(self.walls[i][j]-0.5))
                for k in range(8-len('{0:.1f}'.format(self.walls[i][j]-0.5))):
                    f.write(' ')
            f.write('\n')
        f.write('!\n')
        f.write('TRANSITION = {0}\n'.format(self.Ntrans))
        if (self.Ntrans > 0):
            for l in self.keptTrans:
                f.write(l)
        f.write('!\n')
        f.write('STATICOBJECTS = {0}\n'.format(self.Nstaticobj))
        if (self.Nstaticobj > 0):
            for l in self.keptStaticobj:
                f.write(l)
        f.write('!\n')
        f.write('ANIMOBJECTS = {0}\n'.format(self.Nanimobj))
        if (self.Nanimobj > 0):
            for l in self.keptAnimobj:
                f.write(l)
        f.write('!\n')
        f.write('CLICKABLEOBJECTS = {0}\n'.format(self.Nclickobj))
        if (self.Nclickobj > 0):
            for l in self.keptClickobj:
                f.write(l)
        f.write('!\n')
        f.write('CLICKOBJSUTIL\n')
        if (self.Nclickobjsutil > 0):
            for l in self.keptClickobjsUtil:
                f.write(l)
        f.write('!\n')
        f.write('PNJ = {0}\n'.format(self.Npnj))
        if (self.Npnj > 0):
            for l in self.keptPnj:
                f.write(l)
        f.write('!\n')
        f.write('MOBS = {0}\n'.format(self.Nmobs))
        if (self.Nmobs > 0):
            for l in self.keptMobs:
                f.write(l)
        f.write('!\n')
        f.write('MOBSUTIL\n')
        if (self.Nmobsutil > 0):
            for l in self.keptMobsUtil:
                f.write(l)
        f.write('!\n')
        
        f.close()
        
        
        
    
if __name__ == "__main__":
    app = AppliCanevas()
    app.title("Map Maker v0(in dev.)")
    
    app.mainloop()
    
    gc.collect()
    

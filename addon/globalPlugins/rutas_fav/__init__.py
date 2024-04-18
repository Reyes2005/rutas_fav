# -*- coding: utf-8 -*-
# This file is covered by the GNU General Public License.
# See the file COPYING.txt for more details.
# Copyright (C) 2024 Ángel Reyes <angeldelosreyesfaz@gmail.com>

"""
Este addon tiene como finalidad el almacenar y administrar las rutas favoritas del usuario, para así poder lanzarlas más rápidamente.
"""

#Importamos las librerías del núcleo de NVDA
import globalPluginHandler
import ui
import wx
import gui
import globalVars
import tones
from scriptHandler import script
#Importamos librerías externas a NVDA
import os
import sys
import subprocess
import time
import json

class pathsInput(wx.Dialog):
	def __init__(self, frame):
		super(pathsInput, self).__init__(None, -1, title=_("Ingresar ruta"))
		self.frame = frame
		self.Panel = wx.Panel(self)
		label1 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Ruta absoluta que desee guardar (usar marcadores si están disponibles):"))
		self.path = wx.TextCtrl(self.Panel, wx.ID_ANY)
		label2 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Identificador de la ruta (nombre a mostrar en el menú virtual):"))
		self.identifier = wx.TextCtrl(self.Panel, wx.ID_ANY)
		self.acceptBTN = wx.Button(self.Panel, 0, label=_("&Aceptar"))
		self.Bind(wx.EVT_BUTTON, self.onAccept, id=self.acceptBTN.GetId())
		self.cancelBTN = wx.Button(self.Panel, 1, label=_("Cancelar"))
		self.Bind(wx.EVT_BUTTON, self.onCancel, id=self.cancelBTN.GetId())
		self.webBTN = wx.Button(self.Panel, 2, label=_("&Visitar la web del desarrollador"))
		self.Bind(wx.EVT_BUTTON, self.onWeb, id=self.webBTN.GetId())
		self.Bind(wx.EVT_CHAR_HOOK, self.onkeyWindowDialog)
		sizeV = wx.BoxSizer(wx.VERTICAL)
		sizeH = wx.BoxSizer(wx.HORIZONTAL)
		sizeV.Add(label1, 0, wx.EXPAND)
		sizeV.Add(self.path, 0, wx.EXPAND)
		sizeV.Add(label2, 0, wx.EXPAND)
		sizeV.Add(self.identifier, 0, wx.EXPAND)
		sizeH.Add(self.acceptBTN, 2, wx.EXPAND)
		sizeH.Add(self.cancelBTN, 2, wx.EXPAND)
		sizeH.Add(self.webBTN, 2, wx.EXPAND)
		sizeV.Add(sizeH, 0, wx.EXPAND)
		self.Panel.SetSizer(sizeV)
		self.CenterOnScreen()

	def run(self):
		self.Show()

	def onAccept(self, event):
		if any(value == "" for value in [self.path.GetValue(), self.identifier.GetValue()]):
			msg = "Asegúrese de llenar correctamente los campos solicitados."
			ui.message(msg)
			self.path.SetFocus() if self.path.GetValue() == "" else self.identifier.SetFocus() if self.identifier.GetValue() == "" else None
			return

		pathValue, identifierValue = self.path.GetValue(), self.identifier.GetValue()
		if os.path.exists(pathValue) and not identifierValue in self.paths['identifier']:
			self.paths['path'].append(pathValue)
			self.paths['identifier'].append(identifierValue)
			self._saveInfo()
			if self.empty:
				self.empty = False

		if self.IsModal():
			self.EndModal(0)
		else:
			self.Close()

	def onWeb(self, event):
		wx.LaunchDefaultBrowser("https://reyesgamer.com/")

	def onkeyWindowDialog(self, event):
		if event.GetKeyCode() == 27: # Pulsamos ESC y cerramos la ventana
			if self.IsModal():
				self.EndModal(1)
			else:
				self.Close()
		else:
			event.Skip()

	def onCancel(self, event):
		if self.IsModal():
			self.EndModal(1)
		else:
			self.Close()

#Declaramos la clase de la extensión global y heredamos de la clase padre globalPluginHandler.GlobalPlugin
class GlobalPlugin (globalPluginHandler.GlobalPlugin):
	def __init__(self):
		#Inicializamos la clase padre y las variables de la hija
		super(GlobalPlugin, self).__init__()
		self.paths = self._loadInfo()
		self.counter = -1
		self.last_time = 0
		self.empty = not self.paths

	def _loadInfo(self):
		filename = os.path.join(globalVars.appArgs.configPath, "addons", "rutas_fav", "data.json")
		paths = {"path": [], "identifier": []}
		try:
			with open(filename, "r") as f:
				paths = json.load(f)

		except FileNotFoundError:
			paths = {"path": [], "identifier": []}

		return paths

	def _saveInfo(self):
		if self.paths:
			filename = os.path.join(globalVars.appArgs.configPath, "addons", "rutas_fav", "data.json")
			with open(filename, "w") as f:
				json.dump(self.paths, f)
				tones.beep(440, 100)
				ui.message("Información guardada correctamente.")

	@script(
		description="Abre un cuadro de texto para ingresar nuevas rutas a añadir a la lista",
		gesture="kb:alt+NVDA+a",
	)
	def script_addNewPath(self, gesture):
		pathsI = pathsInput(gui.mainFrame, )
		pathsI.run()

	@script(
		description="Va a la ruta anterior en la lista",
		gesture="kb:alt+NVDA+j"
	)
	def script_previousPath(self, gesture):
		if self.empty:
			ui.message("¡No hay rutas guardadas!")

		else:
			ui.message(len(self.paths))
			self.counter -= 1
			if self.counter < 0:
				self.counter = len(self.paths['path'])-1

			ui.message(f"{self.paths['identifier'][self.counter]} {self.counter+1} de {len(self.paths['path'])}")

	@script(
		description="Va a la siguiente ruta en la lista",
		gesture="kb:alt+NVDA+k"
	)
	def script_nextPath(self, gesture):
		if self.empty:
			ui.message("¡No hay rutas guardadas!")

		else:
			self.counter += 1
			if self.counter > len(self.paths['path'])-1:
				self.counter = 0

			ui.message(f"{self.paths['identifier'][self.counter]} {self.counter+1} de {len(self.paths['path'])}")
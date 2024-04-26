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
import addonHandler
addonHandler.initTranslation()
from scriptHandler import script
#Importamos librerías externas a NVDA
import os
import json
import time

class pathsDialog(wx.Dialog):
	"""
	Clase que lanzará el diálogo para añadir las carpetas, heredando de wx.dialog.
	"""
	def __init__(self, frame, data):
		"""
		Método de inicialización donde se creará toda la interfaz y se vincularán eventos y demás.
		"""
		super(pathsDialog, self).__init__(None, -1, title=_("Ingresar ruta")) #Se inicializa la clase padre para establecer el título del diálogo.

		self.data = data #Se crea una referencia local hacia el objeto de globalPlugin creado más adelante, este es pasado en uno de los parámetros en el constructor.

		#Se asigna el marco correspondiente y se crea el panel donde serán añadidos los controles de GUI.
		self.frame = frame
		self.Panel = wx.Panel(self)

		#Se crean los cuadros de texto junto con su etiqueta, para de esta forma añadirlos más adelante.
		label1 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Ruta absoluta que desee guardar (usar marcadores si están disponibles):"))
		self.path = wx.TextCtrl(self.Panel, wx.ID_ANY)

		label2 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Identificador de la ruta (nombre a mostrar en el menú virtual):"))
		self.identifier = wx.TextCtrl(self.Panel, wx.ID_ANY)

		#Se crean los botones junto con su respectiva vinculación a un método de evento que ejecutará ciertas acciones en base a si son pulsados.
		self.acceptBTN = wx.Button(self.Panel, 0, label=_("&Aceptar"))
		self.Bind(wx.EVT_BUTTON, self.onAccept, id=self.acceptBTN.GetId())
		self.cancelBTN = wx.Button(self.Panel, 1, label=_("Cancelar"))
		self.Bind(wx.EVT_BUTTON, self.onCancel, id=self.cancelBTN.GetId())
		self.webBTN = wx.Button(self.Panel, 2, label=_("&Visitar la web del desarrollador"))
		self.Bind(wx.EVT_BUTTON, self.onWeb, id=self.webBTN.GetId())

		#Se hace una vinculación hacia un método de evento para controlar teclas en la ventana.
		self.Bind(wx.EVT_CHAR_HOOK, self.onkeyWindowDialog)

		#Se crean las instancias de contenedores para añadir los controles.
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

		#Se añaden estos contenedores (empaquetados en uno solo) al panel de la GUI, para luego centrar la ventana en la pantalla.
		self.Panel.SetSizer(sizeV)
		self.CenterOnScreen()

	def onAccept(self, event):
		"""
		Método que responde al evento de pulsar el botón aceptar.
		"""
		if any(value == "" for value in [self.path.GetValue(), self.identifier.GetValue()]): #Se verifica si no existe contenido en cualquiera de los dos campos de texto no para luego lanzar un mensaje de advertencia y enfocar el cuadro correspondiente.
			ui.message(_("Asegúrese de llenar correctamente los campos solicitados."))
			self.path.SetFocus() if self.path.GetValue() == "" else self.identifier.SetFocus() if self.identifier.GetValue() == "" else None
			return

		#Se obtienen los valores de los campos de texto para luego verificar si estos existen en el sistema de archivos y si su identificador no existe ya en la lista de la clave 'identifier' en el diccionario paths.
		pathValue, identifierValue = self.path.GetValue(), self.identifier.GetValue()
		pathValue = self.data.checkPath(pathValue)
		if os.path.exists(pathValue) and not identifierValue in self.data.paths['identifier']:
			#Si esta verificación procede, se añade lo recuperado de los cuadros a las listas correspondientes, para luego cambiar la variable empty a True por fines de control.
			self.data.paths['path'].append(pathValue)
			self.data.paths['identifier'].append(identifierValue)
			if self.data.empty:
				self.data.empty = False

			result = self.data._saveInfo() #Se almacena el valor devuelto por _saveInfo (método explicado más adelante).
			if result: #Si es True se emite un tono y un mensaje confirmando esta operación.
				tones.beep(432, 300)
				ui.message(_("Ruta añadida correctamente."))

		else: #Si la operación anterior falla se emite un mensaje para advertir al usuario.
			ui.message(_("Imposible añadir la ruta a la lista, favor de escribir correctamente la misma o verificar si su identificador no es igual al de uno ya existente."))

		if self.IsModal(): #Si el diálogo es modal, es decir, bloquea la interacción con otras interfaces cerrarlo y establecer su valor de retorno en 0.
			self.EndModal(0)

		else: #Si esto no ocurre, se cierra de todas formas.
			self.Close()

	def onWeb(self, event):
		"""
		Método que responde al evento de pulsar el botón para ir a la web del desarrollador.
		"""
		wx.LaunchDefaultBrowser("https://reyesgamer.com/") #Se lanza el navegador con la URL pasada como parámetro.

	def onkeyWindowDialog(self, event):
		"""
		Método que responde al evento de pulsar ciertas teclas en la ventana.
		"""
		if event.GetKeyCode() == 27: #Si se presiona la tecla ESC se cierra la ventana.
			if self.IsModal():
				self.EndModal(1)
			else:
				self.Close()
		else: #Si la condición anterior no se cumple, se omite el evento interno del diálogo.
			event.Skip()

	def onCancel(self, event):
		"""
		Método que responde al evento de pulsar el botón cancelar.
		"""
		if self.IsModal(): #Si la ventana está abierta, se cierra.
			self.EndModal(1)
		else:
			self.Close()

def disableInSecureMode(decoratedCls):
	"""
	Decorador para deshabilitar el uso de la clase a decorar en pantallas seguras.
	"""
	if globalVars.appArgs.secure: #Si se detecta la ejecución en este tipo de pantallas, se devuelve una instancia sin modificar de globalPluginHandler.GlobalPlugin, si no es así se devuelve la clase decorada.
		return globalPluginHandler.GlobalPlugin
	return decoratedCls

@disableInSecureMode #Se llama al decorador para deshabilitar el uso del complemento en pantallas seguras.
class GlobalPlugin (globalPluginHandler.GlobalPlugin):
	"""
	Clase que hereda de globalPluginHandler.GlobalPlugin para hacer los scripts relacionados a cada combinación de teclas pulsada, así como otras operaciones lógicas para el funcionamiento del addon.
	"""
	def __init__(self):
		"""
		Método de inicialización de la clase donde se inicializan valores tanto para la clase padre como para la clase hija (la actual).
		"""
		super(GlobalPlugin, self).__init__() #Se inicializa la clase padre con sus valores.

		#Se inicializan los valores de la instancia actual para su control.
		self.paths = self._loadInfo()
		self.counter = -1
		self.empty = not self.paths['path']
		self.lastPressTime = 0
		self.markers = {
			"$users": os.path.expanduser('~'),
			"$desktop": os.path.join(os.path.expanduser('~'), "Desktop"),
			"$downloads": os.path.join(os.path.expanduser('~'), "Downloads"),
			"$documents": os.path.join(os.path.expanduser('~'), "Documents"),
			"$videos": os.path.join(os.path.expanduser('~'), "Videos"),
			"$pictures": os.path.join(os.path.expanduser('~'), "Pictures")
		}

	def _loadInfo(self):
		"""
		Método de carga de la información de las rutas y sus identificadores respectivos (si existe una configuración guardada).
		"""
		filename = os.path.join(globalVars.appArgs.configPath, "rutas_fav.json") #Se crea la variable donde se espera que esté el archivo de configuración.
		paths = {"path": [], "identifier": []} #Diccionario con claves cuyo valor es una lista vacía.
		try: #Bloque try para controlar la excepción de archivo no encontrado.
			with open(filename, "r") as f: #Se abre un bloque de este tipo para abrir el archivo con un un manejador y cerrarlo al finalizar su contenido.
				paths = json.load(f) #Se carga el contenido del archivo json en el diccionario declarado arriba.

		except FileNotFoundError: #Excepción para controlar el error provocado por si el archivo no existe.
			paths = {"path": [], "identifier": []}

		return paths #Se devuelve el diccionario, sea con las claves inicializadas en vacío o con el contenido del json.

	def _saveInfo(self):
		"""
		Método de guardado de las rutas y sus identificadores respectivos en un archivo json.
		"""
		filename = os.path.join(globalVars.appArgs.configPath, "rutas_fav.json") #Se crea la variable donde se espera que esté el archivo de configuración.
		with open(filename, "w") as f: #Se abre un bloque de este tipo para abrir el archivo con un un manejador y cerrarlo al finalizar su contenido.
			json.dump(self.paths, f) #Se guarda el contenido del diccionario paths (rutas e identificadores) en un archivo json.
			return True #Se devuelve True por fines de control si la operación es exitosa.
		return False #Se devuelve False por fines de control si la operación falla.

	def checkPath(self, path):
		"""
		Método para verificar si la ruta pasada como parámetro tiene algún marcador para acortar el tamaño de la misma.
		"""
		newPath = self._checkMarkers(path) #Se establece una variable nueva a la que se le asigne como valor el resultado de la función check markers para hacer la verificación de si tiene alguno de los marcadores.
		if newPath is not None: #Si la variable no es None la devuelve.
			return newPath

		return path #De lo contrario, devuelve la variable original.

	def _checkMarkers(self, path):
		"""
		Método para reemplazar ocurrencias de alguno de los marcadores existentes en una cadena pasada si existe.
		"""
		for key,value in self.markers.items(): #Bucle for para recorrer los elementos del diccionario donde se guardan los marcadores.
			if path.startswith(key): #Si la cadena inicia con una de las claves (marcadores) la reemplaza por su valor, es decir, la ruta absoluta para luego devolverla.
				path = path.replace(key, value, 1)
				return path

		return None #Si no hay ningún marcador se devuelve None.

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	@script(
		description="Abre un cuadro de texto para ingresar nuevas rutas a añadir a la lista de rutas favoritas",
		gesture="kb:alt+NVDA+a",
	)
	def script_addNewPath(self, gesture):
		"""
		Método que ejecuta la acción de lanzar y enfocar el diálogo para añadir nuevas rutas.
		"""
		dialog = pathsDialog(gui.mainFrame, self) #Se crea una instancia del diálogo.
		if not dialog.IsShown(): #Si el diálogo no está enfocado, lo hace.
			gui.mainFrame.prePopup()
			dialog.Show()
			dialog.CentreOnScreen()
			gui.mainFrame.postPopup()

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	@script(
		description="Abre o elimina (si se pulsa 2 veces rápidamente) la ruta seleccionada en la lista de rutas favoritas",
		gesture="kb:alt+NVDA+l",
	)
	def script_launchOrDeletePath(self, gesture):
		"""
		Método para ejecutar la acción de lanzar o eliminar la ruta seleccionada en el menú virtual.
		"""
		if self.empty: #Si no hay ninguna ruta guardada, se lanza un mensaje de error y se detiene la ejecución de la función.
			ui.message(_("¡No hay rutas guardadas!"))
			return

		if not os.path.exists(self.paths['path'][self.counter]): #Si la ruta a verificar no existe se lanza un mensaje de error y se elimina del diccionario.
			ui.message(_("La ruta guardada no existe o está mal escrita."))
			del self.paths['path'][self.counter]
			del self.paths['identifier'][self.counter]
			self._saveInfo() #Se guardan las rutas actuales.
			if self.counter > len(self.paths['path'])-1: #Si la variable de contador para navegar en el menú excede la cantidad de elementos del diccionario se recorre hasta el final.
				self.counter = len(self.paths['path'])-1

			if not self.paths['path'] and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

		currentTime = time.time() #Se almacena el tiempo actual.
		if (currentTime - self.lastPressTime) > 0.5: #Si la diferencia entre el tiempo actual y el último momento en que se presionó la combinación de teclas es mayor a 500 ms, se abre la ruta.
			os.startfile(self.paths['path'][self.counter])

		else: #Si la diferencia es menor, se elimina ese elemento y se lanza un mensaje para indicárselo al usuario.
			del self.paths['path'][self.counter]
			del self.paths['identifier'][self.counter]
			ui.message(_("Ruta eliminada correctamente de la lista."))
			self._saveInfo()
			if not self.paths['path'] and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

		self.lastPressTime = currentTime #Se almacena el último momento en que se presionó la combinación de teclas.

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	@script(
		description="Va al elemento anterior en la lista de rutas favoritas",
		gesture="kb:alt+NVDA+j"
	)
	def script_previousPath(self, gesture):
		"""
		Método que hace la acción de ir hacia atrás en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia atrás y lo verbaliza, no sin antes verificar si este es menor a 0, para si es así, recorrerse hasta el final.
			self.counter -= 1
			if self.counter < 0:
				self.counter = len(self.paths['path'])-1

			ui.message(f"{self.paths['identifier'][self.counter]} {self.counter+1} de {len(self.paths['path'])}")

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	@script(
		description="Va al siguiente elemento en la lista de rutas favoritas",
		gesture="kb:alt+NVDA+k"
	)
	def script_nextPath(self, gesture):
		"""
		Método que hace la acción de ir hacia adelante en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia adelante y lo verbaliza, no sin antes verificar si este excede la longitud de elementos guardados, para si es así, volver a la posición original.
			self.counter += 1
			if self.counter > len(self.paths['path'])-1:
				self.counter = 0

			ui.message(f"{self.paths['identifier'][self.counter]} {self.counter+1} de {len(self.paths['path'])}")

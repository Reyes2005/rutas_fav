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
import gui
import globalVars
import api
import addonHandler
addonHandler.initTranslation()
from scriptHandler import script, getLastScriptRepeatCount
#Importamos librerías externas a NVDA
import os
import json
import database
from dialog import pathsDialog

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
	#Translators: name of the addon category that will appear in the input gestures section.
	scriptCategory = _("Rutas fav")
	def __init__(self):
		"""
		Método de inicialización de la clase donde se inicializan valores tanto para la clase padre como para la clase hija (la actual).
		"""
		super(GlobalPlugin, self).__init__() #Se inicializa la clase padre con sus valores.

		#Se inicializan los valores de la instancia actual para su control.
		self.dbPath = os.path.join(globalVars.appArgs.configPath, "rutas_fav.db")
		self.db = database.database(self.dbPath)
		self.db.create("paths", "path text not null, identifier text not null, fixed integer not null")
		self.paths = []
		self.counter = -1
		self.markers = {
			"$users": os.path.expanduser('~'),
			"$desktop": os.path.join(os.path.expanduser('~'), "Desktop"),
			"$downloads": os.path.join(os.path.expanduser('~'), "Downloads"),
			"$documents": os.path.join(os.path.expanduser('~'), "Documents"),
			"$videos": os.path.join(os.path.expanduser('~'), "Videos"),
			"$pictures": os.path.join(os.path.expanduser('~'), "Pictures")
		}
		self.load_info()
		self.empty = not self.paths['path']

	def convertFormat(self):
		filename = os.path.join(globalVars.appArgs.configPath, "rutas_fav.json") #Se crea la variable donde se espera que esté el archivo de configuración.
		paths = {} #Diccionario vacío que se usará para fines de control.
		try: #Bloque try para controlar la excepción de archivo no encontrado.
			with open(filename, "r") as f: #Se abre un bloque de este tipo para abrir el archivo con un un manejador y cerrarlo al finalizar su contenido.
				paths = json.load(f) #Se carga el contenido del archivo json en el diccionario declarado arriba.
				for path, identifier in zip(paths['path'], paths['identifier']):
					self.db.execute("insert into paths(path, identifier) values(?, ?)", (path, identifier))

				os.remove(filename)

		except FileNotFoundError: #Excepción para controlar el error provocado por si el archivo no existe.
			#no se hace nada.
			pass

		except json.JSONDecodeError:
			#se hace una excepción en caso de que la lectura/decodificación de algún objeto JSON no pueda ser llevada a cabo.
			#Translators: The user is notified that the configuration file could not be loaded correctly due to some data decoding error.
			ui.message(_("error en la decodificación de json."))

	def _loadInfo(self):
		"""
		Método de carga de la información de las rutas y sus identificadores respectivos (si existe una configuración guardada).
		"""
		self.convertFormat()
		paths = [] #Lista vacía la cual se convertirá en una de listas donde se almacenarán la ruta, el identificador y si estará fijada (true/false).
		try: #Bloque try para controlar la excepción de algún error sqlite.
			results = self.db.execute("select * from paths")
			paths = [list(result) for result in results]
			finalPaths = []
			for fixed in paths:
				if fixed[2] == True:
					finalPaths.append(fixed)
					paths.remove(fixed)

			self.paths = finalPaths.extend(paths)

		except sqlite3.OperationalError as e:
			ui.message(_("Ha ocurrido un error al obtener las rutas: {}").format(e))

	def _saveInfo(self):
		"""
		Método de guardado de las rutas y sus identificadores respectivos en la base de datos.
		"""
		#se añade un bloque try para poder manejar algunos errores con la db.
		try:
			self.db.commit()
				return True #Se devuelve True por fines de control si la operación es exitosa.
		except sqlite3.OperationalError as e: #manejo de errores de sqlite, se añade el manejador "e" para poder devolver el error al usuario.
			self.db.rollback()
			#Translators: An error message is displayed if the content cannot be saved to the file.
			ui.message(_("Error al guardar las rutas: {}").format(str(e))) #se le muestra el error al usuario usando ui
			return False  #se retorna falso por motivos de control

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
	#Translators: The function of the command is described, which is to copy the full path of the current position in the virtual menu.
	@script(
		description=_("Copia la ruta completa correspondiente a la posición actual del menú virtual"),
		gesture=None
	)
	def script_copyPath(self, gesture):
		"""
		Método que ejecuta la acción de copiar al portapapeles la ruta completa correspondiente a la posición actual del contador en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Error message to indicate that there are no saved paths in the list.
			ui.message(_("¡No hay rutas guardadas!"))
			return

		api.copyToClip(self.paths[self.counter][0], True)

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: The function of the command is described, which is to open the dialog to enter the required data and thus add it to the list.
	@script(
		description=_("Abre el diálogo para ingresar nuevas rutas a añadir a la lista de favoritas"),
		gesture="kb:alt+NVDA+a"
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
	#Translators: The function of the command is described, which is to open the selected route or delete it from the list if the command is pressed twice quickly.
	@script(
		description=_("Abre o elimina (si se pulsa 2 veces rápidamente) la ruta seleccionada en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+l"
	)
	def script_launchOrDeletePath(self, gesture):
		"""
		Método para ejecutar la acción de lanzar o eliminar la ruta seleccionada en el menú virtual.
		"""
		if self.empty: #Si no hay ninguna ruta guardada, se lanza un mensaje de error y se detiene la ejecución de la función.
			#Translators: Error message to indicate that there are no saved paths in the list.
			ui.message(_("¡No hay rutas guardadas!"))
			return

		if not os.path.exists(self.paths[self.counter][0]): #Si la ruta a verificar no existe se lanza un mensaje de error y se elimina del diccionario.
			#Translators: Error message to indicate that the path doesn't exists or is misspelled.
			ui.message(_("La ruta guardada no existe o está mal escrita."))
			del self.paths[self.counter]
			self._saveInfo() #Se guardan las rutas actuales.
			if self.counter > len(self.paths)-1: #Si la variable de contador para navegar en el menú excede la cantidad de elementos del diccionario se recorre hasta el final.
				self.counter = len(self.paths)-1

			if not self.paths and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

		pressCount = getLastScriptRepeatCount() # Se asigna a una variable de control las veces que se ha pulsado la combinación de teclas, asignando 0 si no se había pulsado y 1 si ya lo había hecho anteriormente.
		if pressCount < 1: #Si el valor de la variable anteriormente mencionada es menor a 1 (no ha sido pulsada antes la combinación) se ejecuta la ruta seleccionada.
			os.startfile(self.paths[self.counter][0])

		else: #De lo contrario, la ruta se elimina.
			del self.paths[self.counter]

			#Translators: Message to indicate that the operation was successful and the path along with its identifier were deleted.
			ui.message(_("Ruta eliminada correctamente de la lista."))
			self._saveInfo()
			if not self.paths and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: The function of the command is described, which is to navigate to the previous item in the paths list.
	@script(
		description=_("Va al elemento anterior en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+j"
	)
	def script_previousPath(self, gesture):
		"""
		Método que hace la acción de ir hacia atrás en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Error message to indicate that there are no saved paths in the list.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia atrás y lo verbaliza, no sin antes verificar si este es menor a 0, para si es así, recorrerse hasta el final.
			self.counter -= 1
			if self.counter < 0:
				self.counter = len(self.paths)-1

			#Translators: Message to be spoken when the counter position changes, being composed of the identifier and the current position based on the number of routes inserted.
			ui.message(_("{} {} de {}").format(self.paths[self.counter][1], self.counter+1, len(self.paths)))

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: The function of the command is described, which is to navigate to the next item in the paths list.
	@script(
		description=_("Va al siguiente elemento en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+k"
	)
	def script_nextPath(self, gesture):
		"""
		Método que hace la acción de ir hacia adelante en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Error message to indicate that there are no saved paths in the list.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia adelante y lo verbaliza, no sin antes verificar si este excede la longitud de elementos guardados, para si es así, volver a la posición original.
			self.counter += 1
			if self.counter > len(self.paths)-1:
				self.counter = 0

			#Translators: Message to be spoken when the counter position changes, being composed of the identifier and the current position based on the number of routes inserted.
			ui.message(_("{} {} de {}").format(self.paths[self.counter][1], self.counter+1, len(self.paths)))

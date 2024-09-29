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
import tones
import addonHandler
addonHandler.initTranslation()
from scriptHandler import script, getLastScriptRepeatCount
#Importamos librerías externas a NVDA
import os
import json
from . import database
from .dialog import pathsDialog

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
	#Translators: nombre de la categoría de complemento que aparecerá en la sección de gestos de entrada.
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
		self._loadInfo()
		self.empty = not self.paths
		self.lastFixed = -1

	def terminate(self):
		self.db.commit()
		self.db.close()

	def fix(self, path, identifier):
		idx = self.paths.index([path, identifier, 0])
		try:
			self.paths[idx][2] = 1
			new = self.paths.pop(idx)
			self.paths.insert((self.lastFixed+1), new)
			self.lastFixed = self.paths.index(new)
			self.db.execute("update paths set fixed=? where identifier=?", (1, identifier))
			self.db.commit()
			return True

		except ValueError:
			#Translators: Mensaje que indica que no fue posible fijar la ruta
			gui.messageBox(_("No fue posible fijar la ruta."), _("Error"))
			return False

	def unfix(self, path, identifier):
		idx = self.paths.index([path, identifier, 1])
		try:
			self.paths[idx][2] = 0
			new = self.paths.pop(idx)
			self.paths.append(new)
			self.db.execute("update paths set fixed=? where identifier=?", (0, identifier))
			self.db.commit()
			return True

		except ValueError:
			#Translators: Mensaje que indica que no fue posible desfijar la ruta.
			gui.messageBox(_("No fue posible desfijar la ruta."), _("Error"))
			return False

	def convertFormat(self):
		filename = os.path.join(globalVars.appArgs.configPath, "rutas_fav.json") #Se crea la variable donde se espera que esté el archivo de configuración.
		paths = {} #Diccionario vacío que se usará para fines de control.
		delete = False
		try: #Bloque try para controlar la excepción de archivo no encontrado.
			with open(filename, "r") as f: #Se abre un bloque de este tipo para abrir el archivo con un un manejador y cerrarlo al finalizar su contenido.
				paths = json.load(f) #Se carga el contenido del archivo json en el diccionario declarado arriba.
				for path, identifier in zip(paths['path'], paths['identifier']):
					self.db.execute("insert into paths(path, identifier, fixed) values(?, ?, ?)", (path, identifier, 0))

				delete = True

		except FileNotFoundError: #Excepción para controlar el error provocado por si el archivo no existe.
			#no se hace nada.
			pass

		except json.JSONDecodeError:
			#se hace una excepción en caso de que la lectura/decodificación de algún objeto JSON no pueda ser llevada a cabo.
			#Translators: Se notifica al usuario que el archivo de configuración no se pudo cargar correctamente debido a algún error de decodificación de datos.
			ui.message(_("error en la decodificación de json."))

		if delete:
			self.db.commit()
			os.remove(filename)

	def _loadInfo(self):
		"""
		Método de carga de la información de las rutas y sus identificadores respectivos (si existe una configuración guardada).
		"""
		self.convertFormat()
		paths = [] #Lista vacía la cual se convertirá en una de listas donde se almacenarán la ruta, el identificador y si estará fijada (true/false).
		try: #Bloque try para controlar la excepción de algún error sqlite.
			results = self.db.execute("select * from paths")
			paths = [list(result) for result in results]
			finalPaths = [fixed for fixed in paths if fixed[2] == 1]
			if finalPaths:
				self.lastFixed = paths.index(finalPaths[-1])
				paths = [path for path in paths if path not in finalPaths]
				finalPaths.extend(paths)
				self.paths = finalPaths

			else:
				self.paths = paths

		except sqlite3.OperationalError as e:
			#Translators: Mensaje que indica que ocurrió un error al obtener las rutas.
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
			#Translators: Se muestra un mensaje de error si el contenido no se puede guardar en el archivo.
			ui.message(_("Error al guardar las rutas: {}").format(str(e))) #se le muestra el error al usuario usando ui
			return False  #se retorna falso por motivos de control

	def renamePath(self, old_identifier, new_path, new_identifier):
		"""
		Método para renombrar una ruta existente.
		"""
		try:
			# Buscar el índice de la ruta existente
			idx = next(i for i, v in enumerate(self.paths) if v[1] == old_identifier)
			old_path, fixed = self.paths[idx][0], self.paths[idx][2]
			# Actualizar la ruta en la lista y en la base de datos
			self.paths[idx] = [new_path, new_identifier, fixed]
			self.db.execute("update paths set path=?, identifier=? where identifier=?", (new_path, new_identifier, old_identifier))
			self.db.commit()

			return True

		except StopIteration:
			#Translators: Mensaje que indica que la ruta no fue encontrada al querer renombrarla, junto con el título de la ventana.
			gui.messageBox(_("Ruta no encontrada."), _("Información"))
			return False
			
	def deletePath(self, identifier):
		"""
		Método para eliminar una ruta existente.
		"""
		try:
			# Buscar el índice de la ruta existente
			idx = next(i for i, v in enumerate(self.paths) if v[1] == identifier)

			# Eliminar la ruta de la lista y de la base de datos
			self.paths.pop(idx)
			self.db.execute("delete from paths where identifier=?", (identifier,))
			self.db.commit()
			return True

		except StopIteration:
			#Translators: Mensaje que indica que la ruta no fue encontrada al intentar eliminarla, junto con el título de la ventana.
			gui.messageBox(_("Ruta no encontrada."), _("Información"))
			return False

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

	def addPath(self, path, identifier, fixed=0):
		identifiers = [value[1] for value in self.paths]
		if os.path.exists(path) and not identifier in identifiers:
			#Si esta verificación procede, se añade lo recuperado de los cuadros a las listas correspondientes, para luego cambiar la variable empty a True por fines de control.
			self.paths.append([path, identifier, fixed])
			self.db.execute("insert into paths(path, identifier, fixed) values(?, ?, ?)", (path, identifier, fixed))
			self.db.commit()
			if self.empty:
				self.empty = False

			result = self._saveInfo() #Se almacena el valor devuelto por _saveInfo (método explicado más adelante).
			if result: #Si es True se emite un tono y un mensaje confirmando esta operación.
				tones.beep(432, 300)
				#Translators: Mensaje para indicar que la operación fue exitosa y la ruta se añadió a la lista.
				ui.message(_("Ruta añadida correctamente."))
				return True

		else: #Si la operación anterior falla se emite un mensaje para advertir al usuario.
			#Translators: Mensaje para indicar que la operación falló porque la ruta no existe, está mal escrita o el identificador ya existe.
			gui.messageBox(_("Imposible añadir la ruta a la lista, favor de escribir correctamente la misma o verificar si su identificador no es igual al de uno ya existente."), _("Error"))
			return False

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: descripción para el comando para copiar la ruta completa de la posición actual en el menú virtual.
	@script(
		description=_("Copia la ruta completa correspondiente a la posición actual del menú virtual"),
		gesture=None
	)
	def script_copyPath(self, gesture):
		"""
		Método que ejecuta la acción de copiar al portapapeles la ruta completa correspondiente a la posición actual del contador en el menú virtual.
		"""
		self.db.close()
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Mensaje de error para indicar que no hay rutas guardadas en la lista.
			ui.message(_("¡No hay rutas guardadas!"))
			return

		api.copyToClip(self.paths[self.counter][0], True)

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators:  descripción del comando para abrir el diálogo para ingresar los datos requeridos y así agregarlos a la lista.
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
	#Translators:  Descripción para el comando, el cual permite abrir la ruta seleccionada o eliminarla de la lista si se presiona dos veces rápidamente el comando.
	@script(
		description=_("Abre o elimina (si se pulsa 2 veces rápidamente) la ruta seleccionada en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+l"
	)
	def script_launchOrDeletePath(self, gesture):
		"""
		Método para ejecutar la acción de lanzar o eliminar la ruta seleccionada en el menú virtual.
		"""
		if self.empty: #Si no hay ninguna ruta guardada, se lanza un mensaje de error y se detiene la ejecución de la función.
			#Translators: Mensaje de error para indicar que no hay rutas guardadas en la lista.
			ui.message(_("¡No hay rutas guardadas!"))
			return

		if not os.path.exists(self.paths[self.counter][0]): #Si la ruta a verificar no existe se lanza un mensaje de error y se elimina del diccionario.
			#Translators: Mensaje de error para indicar que la ruta no existe o está mal escrita.
			ui.message(_("La ruta guardada no existe o está mal escrita."))
			self.deletePath(self.paths[self.counter][1])
			if self.counter > len(self.paths)-1: #Si la variable de contador para navegar en el menú excede la cantidad de elementos del diccionario se recorre hasta el final.
				self.counter = len(self.paths)-1

			if not self.paths and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

		pressCount = getLastScriptRepeatCount() # Se asigna a una variable de control las veces que se ha pulsado la combinación de teclas, asignando 0 si no se había pulsado y 1 si ya lo había hecho anteriormente.
		if pressCount < 1: #Si el valor de la variable anteriormente mencionada es menor a 1 (no ha sido pulsada antes la combinación) se ejecuta la ruta seleccionada.
			os.startfile(self.paths[self.counter][0])

		else: #De lo contrario, la ruta se elimina.
			self.deletePath(self.paths[self.counter][1])

			#Translators: Mensaje para indicar que la operación fue exitosa y se eliminó la ruta junto con su identificador.
			ui.message(_("Ruta eliminada correctamente de la lista."))
			self._saveInfo()
			if not self.paths and not self.empty: #Si la lista de las rutas está vacía y la variable empty está en False se establece en True para fines de control.
				self.empty = True

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: Descripción para el comando, el cual permite ir hacia atrás en el menú virtual.
	@script(
		description=_("Va al elemento anterior en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+j"
	)
	def script_previousPath(self, gesture):
		"""
		Método que hace la acción de ir hacia atrás en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Mensaje de error para indicar que no hay rutas guardadas en la lista.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia atrás y lo verbaliza, no sin antes verificar si este es menor a 0, para si es así, recorrerse hasta el final.
			self.counter -= 1
			if self.counter < 0:
				self.counter = len(self.paths)-1

			#Translators: Mensaje que indica cuando cambia la posición del contador, compuesto por el identificador y la posición actual en función del número de rutas insertadas.
			ui.message(_("{} {} de {}").format(self.paths[self.counter][1], self.counter+1, len(self.paths)))

	#Decorador para asignarle su descripción y atajo de teclado a esta función del addon.
	#Translators: Descripción del comando, el cual permite ir hacia adelante en el menú virtual.
	@script(
		description=_("Va al siguiente elemento en la lista de rutas favoritas"),
		gesture="kb:alt+NVDA+k"
	)
	def script_nextPath(self, gesture):
		"""
		Método que hace la acción de ir hacia adelante en el menú virtual.
		"""
		if self.empty: #Si no hay rutas guardadas se lanza un mensaje de error.
			#Translators: Mensaje de error para indicar que no hay rutas guardadas en la lista.
			ui.message(_("¡No hay rutas guardadas!"))

		else: #Si el resultado de la condición es lo contrario, recorre el contador en 1 hacia adelante y lo verbaliza, no sin antes verificar si este excede la longitud de elementos guardados, para si es así, volver a la posición original.
			self.counter += 1
			if self.counter > len(self.paths)-1:
				self.counter = 0

			#Translators: Mensaje que indica cuando cambia la posición del contador, compuesto por el identificador y la posición actual en función del número de rutas insertadas.
			ui.message(_("{} {} de {}").format(self.paths[self.counter][1], self.counter+1, len(self.paths)))

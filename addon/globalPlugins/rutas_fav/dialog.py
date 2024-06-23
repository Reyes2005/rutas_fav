import ui
import wx
import tones
import addonHandler
addonHandler.initTranslation()

class pathsDialog(wx.Dialog):
	"""
	Clase que lanzará el diálogo para añadir las carpetas, heredando de wx.dialog.
	"""
	def __init__(self, frame, data):
		"""
		Método de inicialización donde se creará toda la interfaz y se vincularán eventos y demás.
		"""
		#Translators: Title that will be displayed when the dialog appears.
		super(pathsDialog, self).__init__(None, -1, title=_("Rutas favoritas")) #Se inicializa la clase padre para establecer el título del diálogo.

		self.data = data #Se crea una referencia local hacia el objeto de globalPlugin creado en el módulo __init__, este es pasado en uno de los parámetros en el constructor.

		#Se asigna el marco correspondiente y se crea el panel donde serán añadidos los controles de GUI.
		self.frame = frame
		self.Panel = wx.Panel(self)

		#Se crean los cuadros de texto junto con su etiqueta, para de esta forma añadirlos más adelante.
		#Translators: Label for the text area in which the absolute path will be entered using markers if these are available.
		label1 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Ruta absoluta que desee guardar (usar marcadores si están disponibles):"))
		self.path = wx.TextCtrl(self.Panel, wx.ID_ANY)

		#Translators: Label for the text area where a common name will be written to identify the saved path.
		label2 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Identificador de la ruta (nombre a mostrar en el menú virtual):"))
		self.identifier = wx.TextCtrl(self.Panel, wx.ID_ANY)

		label3 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Rutas añadidas:"))
		self.list = wx.ListCtrl(self.Panel, wx.ID_ANY, style=wx.LC_HRULES | wx.LC_REPORT | wx.LC_SORT_ASCENDING | wx.LC_VRULES | wx.LC_SINGLE_SEL)
		self.list.Bind(wx.EVT_CONTEXT_MENU, self.onActions)

		#Se crean los botones junto con su respectiva vinculación a un método de evento que ejecutará ciertas acciones en base a si son pulsados.

		self.actionsBTN = wx.Button(self.Panel, label=_("Acciones"))
		self.actionsBTN.Bind(wx.EVT_BUTTON, self.onActions)
		#Translators: It is the accept button to confirm the data entered.
		self.acceptBTN = wx.Button(self.Panel, label=_("&Aceptar"))
		self.acceptBTN.Bind(wx.EVT_BUTTON, self.onAccept)
		#Translators: It is the cancel button to cancel the process and close the dialog.
		self.cancelBTN = wx.Button(self.Panel, label=_("Cancelar"))
		self.cancelBTN.Bind(wx.EVT_BUTTON, self.onCancel)
		#Translators: It is the web button to open the developer website in the browser.
		self.webBTN = wx.Button(self.Panel, label=_("&Visitar la web del desarrollador"))
		self.webBTN.Bind(wx.EVT_BUTTON, self.onWeb)
		#Se hace una vinculación hacia un método de evento para controlar teclas en la ventana.
		self.Bind(wx.EVT_CHAR_HOOK, self.onkeyWindowDialog)

		#Se crean las instancias de contenedores para añadir los controles.
		sizeV = wx.BoxSizer(wx.VERTICAL)
		sizeH = wx.BoxSizer(wx.HORIZONTAL)

		sizeV.Add(label1, 0, wx.EXPAND)
		sizeV.Add(self.path, 0, wx.EXPAND)
		sizeV.Add(label2, 0, wx.EXPAND)
		sizeV.Add(self.identifier, 0, wx.EXPAND)
		sizeV.Add(label3, 0, wx.EXPAND)
		sizeV.Add(self.list, 0, wx.EXPAND)

		sizeH.Add(self.actionsBTN, 2, wx.EXPAND)
		sizeH.Add(self.acceptBTN, 2, wx.EXPAND)
		sizeH.Add(self.cancelBTN, 2, wx.EXPAND)
		sizeH.Add(self.webBTN, 2, wx.EXPAND)

		sizeV.Add(sizeH, 0, wx.EXPAND)

		#Se añaden estos contenedores (empaquetados en uno solo) al panel de la GUI, para luego centrar la ventana en la pantalla.
		self.Panel.SetSizer(sizeV)
		self.CenterOnScreen()

	def onActions(self, event):
		self.menu = wx.Menu()
		item1 = self.menu.Append(1, _("Fijar ruta"))
		item2 = self.menu.Append(2, _("Desfijar ruta"))
		item3 = self.menu.Append(3, _("Eliminar ruta"))
		item4 = self.menu.Append(4, _("Renombrar ruta"))
		self.menu.Bind(wx.EVT_MENU, self.onMenu)
		self.actionsBTN.PopupMenu(self.menu)

	def onMenu(self, event):
		if self.list.GetItemCount() == 0:
			ui.message(_("No hay rutas guardadas."))
			return

		id = event.GetId()

	def onAccept(self, event):
		"""
		Método que responde al evento de pulsar el botón aceptar.
		"""
		if any(value == "" for value in [self.path.GetValue(), self.identifier.GetValue()]): #Se verifica si no existe contenido en cualquiera de los dos campos de texto no para luego lanzar un mensaje de advertencia y enfocar el cuadro correspondiente.
			#Translators: Message to indicate that the operation failed because one or both of the text areas are empty.
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
				#Translators: Message to indicate that the operation was successful and the path added to the list.
				ui.message(_("Ruta añadida correctamente."))

		else: #Si la operación anterior falla se emite un mensaje para advertir al usuario.
			#Translators: Message to indicate that the operation failed because the path doesn't exists, is misspelled or the identifier already exists.
			ui.message(_("Imposible añadir la ruta a la lista, favor de escribir correctamente la misma o verificar si su identificador no es igual al de uno ya existente."))

		if self.IsModal(): #Si el diálogo es modal, es decir, bloquea la interacción con otras interfaces cerrarlo y establecer su valor de retorno en 0.
			self.EndModal(wx.ID_CANCEL)

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
				self.EndModal(wx.ID_CANCEL)
			else:
				self.Close()
		else: #Si la condición anterior no se cumple, se omite el evento interno del diálogo.
			event.Skip()

	def onCancel(self, event):
		"""
		Método que responde al evento de pulsar el botón cancelar.
		"""
		if self.IsModal(): #Si la ventana está abierta, se cierra.
			self.EndModal(wx.ID_CANCEL)
		else:
			self.Close()


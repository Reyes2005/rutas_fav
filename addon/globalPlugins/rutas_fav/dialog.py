import ui
import wx
import addonHandler
addonHandler.initTranslation()
import os

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

		#Se crean los cuadros de texto y botones junto con su etiqueta, para de esta forma añadirlos más adelante.
		#Translators: Etiqueta para el área de texto en la que se ingresará la ruta absoluta usando marcadores si están disponibles.
		label1 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Ruta absoluta que desee guardar (usar marcadores si están disponibles):"))
		self.path = wx.TextCtrl(self.Panel, wx.ID_ANY)

		# Creamos el botón para permitir la selección de una ruta mediante el explorador de archivos.
		#Translators: un botón para abrir el explorador de archivos, lo que permite seleccionar una ruta de forma más intuitiva.
		self.browseBTN = wx.Button(self.Panel, label=_("&Examinar..."))
		self.browseBTN.Bind(wx.EVT_BUTTON, self.onBrowse)

		#Translators: Etiqueta para el área de texto donde se escribirá un nombre para identificar la ruta guardada.
		label2 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Identificador de la ruta (nombre a mostrar en el menú virtual):"))
		self.identifier = wx.TextCtrl(self.Panel, wx.ID_ANY)





		# Translators: Etiqueta que contiene el nombre de la lista donde se muestran las rutas.
		label3 = wx.StaticText(self.Panel, wx.ID_ANY, label=_("&Rutas añadidas:"))
		self.list = wx.ListCtrl(self.Panel, wx.ID_ANY, style=wx.LC_LIST | wx.LC_SINGLE_SEL)
		self.list.Bind(wx.EVT_CONTEXT_MENU, self.onActions)

		#Se crean los botones junto con su respectiva vinculación a un método de evento que ejecutará ciertas acciones en base a si son pulsados.

		# Translators: Botón que permite ejecutar el menú contextual que muestra las acciones para la ruta seleccionada
		self.actionsBTN = wx.Button(self.Panel, label=_("Acciones"))
		self.actionsBTN.Bind(wx.EVT_BUTTON, self.onActions)
		#Translators: Botón de aceptar para confirmar los datos ingresados.
		self.acceptBTN = wx.Button(self.Panel, label=_("&Aceptar"))
		self.acceptBTN.Bind(wx.EVT_BUTTON, self.onAccept)
		#Translators: Botón cancelar para cancelar el proceso y cerrar el diálogo.
		self.cancelBTN = wx.Button(self.Panel, label=_("Cancelar"))
		self.cancelBTN.Bind(wx.EVT_BUTTON, self.onCancel)
		#Translators: Botón para abrir el sitio web del desarrollador en el navegador.
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

		self.addListItems()

	def addListItems(self):
		for idx, row in enumerate(self.data.paths):
			#Translators: Etiquetas para los elementos de la lista. si la ruta está fijada y el nombre de la ruta
			self.list.InsertItem(idx, _("({}Nombre: {}, Ruta: {}").format("(Fijado) " if row[2]==1 else "", row[1], row[0]))
			self.list.Focus(0)

	def onActions(self, event):
		self.menu = wx.Menu()
		#Translators: Nombre del primer elemento del menú acciones, que funciona para fijar la ruta.
		item1 = self.menu.Append(1, _("Fijar ruta"))
		#Translators: Nombre del segundo elemento del menú acciones, que funciona para desfijar una ruta
		item2 = self.menu.Append(2, _("Desfijar ruta"))
		#Translators: Tercer elemento del menú acciones, el cual funciona para eliminar una ruta.
		item3 = self.menu.Append(3, _("Eliminar ruta"))
		#Translators: Cuarto elemento del menú acciones, el cual funciona para renombrar el identificador de una ruta
		item4 = self.menu.Append(4, _("Renombrar identificador"))
		self.menu.Bind(wx.EVT_MENU, self.onMenu)
		self.actionsBTN.PopupMenu(self.menu)

	def onMenu(self, event):
		if self.list.GetItemCount() == 0:
			#Translators: Mensaje que indica que no hay rutas guardadas
			ui.message(_("No hay rutas guardadas."))
			return

		id = event.GetId()
		item = self.list.GetItemText(self.list.GetFocusedItem())
		if item.startswith("(Fijado)"):
			item = item.replace(f"{item.split(')')[0]}) ", "", 1).strip()

		identifier = item.split(',')[0].split(':')[1].strip()
		path = item.split(',')[1]
		path = path.replace(f"{path.split(':')[0]}: ", "", 1).strip()
		if id == 1:
			result = self.data.fix(path, identifier)
			if result:
				#Translators: Mensaje indicando que la ruta se guardó exitosamente
				wx.MessageBox(_("Ruta fijada correctamente."), _("Información"), wx.ICON_INFORMATION)
				self.list.DeleteAllItems()
				self.addListItems()

		elif id == 2:
			result = self.data.unfix(path, identifier)
			if result:
				#Translators: Mensaje que indica que la ruta se desfijó correctamente.
				wx.MessageBox(_("Ruta desfijada correctamente."), _("Información"), wx.ICON_INFORMATION)
				self.list.DeleteAllItems()
				self.addListItems()
				
		elif id == 3:
			result = self.data.deletePath(identifier)
			if result:
				#Translators: Mensaje que indica que la ruta se eliminó correctamente.
				wx.MessageBox(_("Ruta eliminada correctamente."), _("Información"), wx.ICON_INFORMATION)
				self.list.DeleteAllItems()
				self.addListItems()
				if self.data.counter >= len(self.data.paths):
					self.data.counter = len(self.data.paths) - 1
				# Si la lista queda vacía, marca la variable `empty` como `True`.
				if not self.data.paths:
					self.data.empty = True
				return True

		elif id == 4:
			#Translators: Mensaje de diálogo que solicita el nuevo identificador para la ruta, junto con el título de la ventana.
			dlg = wx.TextEntryDialog(self, _("Ingrese el nuevo identificador:"), _("Renombrar identificador"), value=identifier)
			if dlg.ShowModal() == wx.ID_OK:
				new_identifier = dlg.GetValue()
				if self.data.renamePath(identifier, path, new_identifier):
					#Translators: Mensaje que indica que la ruta fue renombrada correctamente
					wx.MessageBox(_("Identificador renombrado correctamente."), _("Información"), wx.ICON_INFORMATION)
					self.list.DeleteAllItems()
					self.addListItems()
			dlg.Destroy()

	def onBrowse(self, event):
		#Translators: Título del diálogo para seleccionar una carpeta del explorador.
		with wx.DirDialog(self, _("Selecciona una carpeta"), style=wx.DD_DEFAULT_STYLE) as dialog:
			if dialog.ShowModal() == wx.ID_OK:
				# Se extrae la ruta de la carpeta para configurar el valor en el cuadro self.path
				self.path.SetValue(dialog.GetPath())
				# extraemos solamente el nombre de la ruta y lo configuramos en el cuadro identifier por default
				self.identifier.SetValue(os.path.basename(dialog.GetPath()))
				self.identifier.SetFocus()  # ponemos el foco en el cuadro identifier

	def onAccept(self, event):
		"""
		Método que responde al evento de pulsar el botón aceptar.
		"""
		if any(value == "" for value in [self.path.GetValue(), self.identifier.GetValue()]): #Se verifica si no existe contenido en cualquiera de los dos campos de texto no para luego lanzar un mensaje de advertencia y enfocar el cuadro correspondiente.
			#Translators: Mensaje para indicar que la operación falló porque una o ambas áreas de texto están vacías.
			ui.message(_("Asegúrese de llenar correctamente los campos solicitados."))
			self.path.SetFocus() if self.path.GetValue() == "" else self.identifier.SetFocus() if self.identifier.GetValue() == "" else None
			return

		#Se obtienen los valores de los campos de texto para luego verificar si estos existen en el sistema de archivos y si su identificador no existe ya en la lista de la clave 'identifier' en el diccionario paths.
		pathValue, identifierValue = self.path.GetValue(), self.identifier.GetValue()
		pathValue = self.data.checkPath(pathValue)
		self.data.addPath(pathValue, identifierValue, 0)
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
		elif self.list.HasFocus() and event.GetKeyCode() == 13: # Si se presiona la tecla Enter, y si el foco está en la lista de rutas:
			if self.list.GetFocusedItem() != -1:
				self.onActions(None)  # Mostrar el menú contextual
		elif self.list.HasFocus() and event.GetKeyCode() == 127:  # Si se presiona la tecla suprimir y el foco está en la lista de rutas:
			self.onDeleteItem()  # se llama al método onDeleteItem para la confirmación de la eliminación de una ruta
		else: #Si la condición anterior no se cumple, se omite el evento interno del diálogo.
			event.Skip()

	def onDeleteItem(self):
		"""
		Método para solicitar la confirmación de eliminar una ruta al presionar la tecla suprimir
		"""
		if self.list.GetFocusedItem() == -1:  # Verifica si hay un elemento seleccionado
			#Translators: mensaje que indica que primero se tiene que seleccionar una ruta desde la lista de rutas para poder eliminarla de la misma.
			ui.message(_("Seleccione una ruta para eliminar."))
			return
		# se obtiene el texto del elemento seleccionado
		item = self.list.GetItemText(self.list.GetFocusedItem())
		if item.startswith("(Fijado)"):
			item = item.replace(f"{item.split(')')[0]}) ", "", 1).strip()

		identifier = item.split(',')[0].split(':')[1].strip()

		# Mostrar un cuadro de diálogo de confirmación
		#Translators: Mensaje que pregunta si realmente se desea eliminar la ruta, donde se adjunta el nombre de la misma para mayor claridad. también, el título del cuadro de diálogo.
		dlg = wx.MessageDialog(self,_("¿Realmente desea eliminar la ruta '{}'?".format(identifier)), _("Confirmación de eliminación"), style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

		if dlg.ShowModal() == wx.ID_YES:  # Si el usuario confirma, se elimina la ruta
			result = self.data.deletePath(identifier)
			if result:
				#Translators: Mensaje que indica que la ruta se eliminó correctamente
				wx.MessageBox(_("Ruta eliminada correctamente."), _("Información"), wx.ICON_INFORMATION)
				self.list.DeleteAllItems()
				self.addListItems()

		dlg.Destroy()

	def onCancel(self, event):
		"""
		Método que responde al evento de pulsar el botón cancelar.
		"""
		if self.IsModal(): #Si la ventana está abierta, se cierra.
			self.EndModal(wx.ID_CANCEL)
		else:
			self.Close()

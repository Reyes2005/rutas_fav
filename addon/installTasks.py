# -*- coding: utf-8 -*-

# Este archivo está cubierto por la Licencia Pública General de GNU.
# Última actualización 2024
# Derechos de autor (C) 2024 Marco Leija <marcomolinaleija@hotmail.com>

import webbrowser

import addonHandler
addonHandler.initTranslation()

class news:
	def open():
		webbrowser.open("https://marco-ml.com/rutas_fav_novedades.html")

	def request():
		import wx
		import gui
		
		# Translators: The title of the dialog requesting donations from users.
		title =_("Novedades, rutas_fav versión 1.1.")
		
		# Translators: The text of the donate dialog
		message = _("""rutas_fav:
		¿Te gustaría mirar las novedades de la versión 1.1 del complemento?
		""")
		
		name = addonHandler.getCodeAddon().manifest['summary']
		if gui.messageBox(message.format(name=name), title, style=wx.YES_NO|wx.ICON_QUESTION) == wx.YES:
			news.open()
			return True
		return False

def onInstall():
	import globalVars
	# This checks if NVDA is running in a secure mode (e.g., on the Windows login screen),
	# which would prevent the addon from performing certain actions.
	if not globalVars.appArgs.secure:
		news.request()
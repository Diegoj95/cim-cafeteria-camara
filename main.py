import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']


credenciales = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
cliente = gspread.authorize(credenciales)

sheet = cliente.create("DatosCasino")

sheet.share('practicacim@gmail.com', perm_type='user', role='writer')
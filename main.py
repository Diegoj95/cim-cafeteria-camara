import cv2
import gspread
import tkinter as tk
from oauth2client.service_account import ServiceAccountCredentials
import time
from PIL import Image
from PIL import ImageTk
import numpy as np

def credenciales():
    # Define las credenciales y autoriza el cliente
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credenciales = ServiceAccountCredentials.from_json_keyfile_name("cim-cafeteria-camara/gs_credentials.json", scope)
    cliente = gspread.authorize(credenciales)
    # Abre la hoja de cálculo
    hoja_calculo = cliente.open("DatosCafeteria")
    # Selecciona la hoja de cálculo en la que se escribirán los datos
    hoja = hoja_calculo.worksheet("Sheet1")
    return hoja

def cargar_imagen(intervalo, umbral):
    # Carga la imagen de la cámara
    #camara = cv2.VideoCapture(0)
    imagen = cv2.imread("imagen.PNG")

    # Convierte la imagen a escala de grises y aplica un filtro Gaussiano
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (5, 5), 0)

    # Aplica la umbralización para detectar los objetos blancos
    _, umbralizada = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)

    # Realiza una operación de dilatación para unir las áreas de píxeles blancos que puedan estar separados
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    umbralizada = cv2.dilate(umbralizada, kernel, iterations=2)
    md, mo = detectar_contornos(imagen, umbralizada, intervalo, umbral)
    return md, mo

def ordenar_puntos(puntos):
    n_puntos = np.concatenate([puntos[0], puntos[1], puntos[2], puntos[3]]).tolist()

    #Se ordenan los puntos respecto a el valor de la posición y 
    y_order = sorted(n_puntos, key=lambda n_puntos: n_puntos[1])

    # Tomamos las 2 primeras coordenadas y las ordenamos por la posición x
    x1_order = y_order[:2]
    x1_order = sorted(x1_order, key=lambda x1_order: x1_order[0])

    # Tomamos las ultimas 2 coordenadas y las ordenamos por la posición x
    x2_order = y_order[2:4]
    x2_order = sorted(x2_order, key=lambda x2_order: x2_order[0])

    return [x1_order[0], x1_order[1], x2_order[0], x2_order[1]]

def detectar_contornos(imagen, umbralizada, intervalo, umbral):

    # Encuentra los contornos de los objetos blancos en la imagen
    contornos, _ = cv2.findContours(umbralizada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contador = 0
    # Filtra los contornos por su forma para encontrar los contornos de mesas rectangulares
    mesas_ocupadas = 0
    mesas_disponibles = 0
    # Analizis de contornos rectangulares (posibles candidatos)
    for contorno in contornos:
        perimetro = cv2.arcLength(contorno, True)
        # Calculo de puntos en la imagen
        aprox = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)
        if len(aprox) == 4 and cv2.contourArea(aprox) > 500:
            # Calculo de areas
            rect_area = cv2.contourArea(contorno)
            x, y, w, h = cv2.boundingRect(contorno)
            # Ordenar coordenadas
            coordenadas = np.array(ordenar_puntos(aprox))
            crop = umbralizada[y:y+h, x:x+w]
            # Impresión de ubicación de mesas
            cv2.rectangle(imagen, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(imagen,str(rect_area),(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)
            
            #Impresión de puntos
            coordenadas = coordenadas.ravel()
            cv2.circle(imagen, (coordenadas[0], coordenadas[1]), 5, (255, 60, 51), -1) #Rojo
            cv2.circle(imagen, (coordenadas[2], coordenadas[3]), 5, (51, 51, 255), -1) #Azul
            cv2.circle(imagen, (coordenadas[4], coordenadas[5]), 5, (0, 243, 255), -1) #Celeste
            cv2.circle(imagen, (coordenadas[6], coordenadas[7]), 5, (0, 255, 0), -1) #Verde

            # recorte de las mesas
            recut(crop, rect_area, contador)
            contador+=1

            if rect_area < 40000:
                mesas_ocupadas += 1
            else:
                mesas_disponibles += 1

    # Mostrar en tkinter
    im = Image.fromarray(imagen)
    img = ImageTk.PhotoImage(image=im)
    lblOutputImage.configure(image=img)
    lblOutputImage.image = img
    return mesas_disponibles, mesas_ocupadas

def finalizar():
    # Boton agregado para rellenar
    pass

def capturar(mesas_disponibles, mesas_ocupadas):
    # Obtiene la fecha y hora actual
    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

    # Escribe los datos en la hoja de cálculo
    datos = [mesas_disponibles, mesas_ocupadas, fecha_hora]
    hoja = credenciales()
    hoja.append_row(datos)

def recut(imagen, area, nombre):
    cv2.imshow(str(nombre), imagen)


# Define el intervalo de tiempo en segundos para enviar los datos
intervalo = 10
# Define el umbral para la umbralización de la imagen
umbral = 200

#Ventana para el Tkinter
root = tk.Tk()
main = tk.Frame(root)
main.pack()
lblOutputImage = tk.Label(main)
lblOutputImage.grid(column=1, row=1, columnspan=2)

#Cargar el video
md, mo = cargar_imagen(intervalo, umbral)

# Botones
btnFinalizar = tk.Button(main, text="Finalizar", width=28, command=finalizar)
btnFinalizar.grid(column=1, row=0, padx=5, pady=5)

btnCapturar = tk.Button(main, text="Capturar imagen", width=28, command=capturar(md, mo))
btnCapturar.grid(column=2, row=0, padx=5, pady=5)


root.mainloop()



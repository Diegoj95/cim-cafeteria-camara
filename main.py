# Liberias necesarias
import cv2
import numpy as np
import tkinter as tk
from oauth2client.service_account import ServiceAccountCredentials
import time
import gspread
from PIL import Image, ImageTk
# Libreria para trabajar con hilos, para que la ventana 
# no se congele al desplegar la ventana secundaria
#import threading

# Ventana de tkinter
root = tk.Tk()
# Titulo de la ventana
root.title("Analizador de Mesas")
# Umbral que se implementará en el thresholding
umbral = 150
# Variable para el boton de encender/apagar camara
show_camera = True

# Función para activar y desactivar la camara
def toggle_camera():
    global show_camera
    show_camera = not show_camera
    if show_camera:
        camera_button.config(text="Apagar camara")
    else:
        camera_button.config(text="Mostrar camara")


# Definición del boton que activa y desactiva la camara
camera_button = tk.Button(root, text="Apagar Camara", command=toggle_camera)
# Poner el boton en la ventana
camera_button.pack()

# Función para conectar google sheets a través de credenciales
def credenciales():
    # Define las credenciales y autoriza el cliente
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # En caso de error, cambiar la ruta relativa del archivo .json
    credenciales = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
    cliente = gspread.authorize(credenciales)
    # Abre la hoja de cálculo
    hoja_calculo = cliente.open("DatosCafeteria")
    # Selecciona la hoja de cálculo en la que se escribirán los datos
    hoja = hoja_calculo.worksheet("Sheet1")
    return hoja

# Función para ordenar las esquinas de las mesas
def sort_points(puntos):
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

# Función donde se recorta cada mesa y se analiza dentro de estas si hay objetos encima de este
def recrop(imagen, th, area, a, b):
    # busqueda de cosas
    tarea = 0
    contours, hierarchy = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        s_area = cv2.contourArea(contour)
        # Si el area del objeto es menor que el area de la mesa
        if s_area < area:
            # Se suma el area del objeto encontrado y se le dibuja un contorno
            tarea = tarea + s_area
            cv2.rectangle(imagen, (x+a,y+b), (x+w+a, y+h+b), (0,255,0), 2)

    # Se ve si el area total de los objetos es menor al 10% del area de la mesa
    area = area*0.1
    if tarea < area:
        cv2.putText(imagen,f"Desocupada",(x+a,y+b),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
        return True, imagen
    else:   
        cv2.putText(imagen,f"Ocupado",(x+a,y+b),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
        return False, imagen

# Analisis de la imagen capturada
def capture():
    # Capturar el video actual
    ret, frame = cap.read()

    # Convertir el video a escala de grises y aplicar el filtro Canny
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Linea para aplicar un filtro de difuminación (opcional)
    #gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # Aplicación del threshold
    _, thresh = cv2.threshold(gray, umbral, 255, cv2.THRESH_BINARY)

    # Operación de dilatación para juntar bordes
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.dilate(thresh, kernel, iterations=2)

    # Buscar los contornos de los rectángulos en el video
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Crear una copia del video para dibujar los contornos
    output = frame.copy()

    # Variables que contienen el número de mesas ocupadas y desocupadas
    occupied_tables = 0
    unoccupied_tables = 0

    # Dibujar los contornos de los rectángulos en el video
    for contour in contours:
        perimiter = cv2.arcLength(contour, True)
        #Calculo de puntos en la imagen y area
        approx = cv2.approxPolyDP(contour, 0.02*perimiter, True)
        area = cv2.contourArea(contour)
        # Si hay un contorno de 4 lados y con un area superior a 1000 pixeles se considera mesa
        if len(approx) == 4 and area > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            # Ordenar coordenadas
            coordinates = np.array(sort_points(approx))
            # Extracción de la zona de las mesas en el frame
            table = frame[y:y+h, x:x+w]
            table_thresh = thresh[y:y+h, x:x+w]
            
            # mostrar mesas
            cv2.rectangle(output, (x, y), (x+w, y+h), (0,0,255), 2)
            cv2.putText(output,str(area),(x,y),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),3)

            #Impresión de puntos ya ordenados
            coordinates = coordinates.ravel()
            cv2.circle(output, (coordinates[0], coordinates[1]), 5, (255, 60, 51), -1) #Rojo
            cv2.circle(output, (coordinates[2], coordinates[3]), 5, (51, 51, 255), -1) #Azul
            cv2.circle(output, (coordinates[4], coordinates[5]), 5, (0, 243, 255), -1) #Celeste
            cv2.circle(output, (coordinates[6], coordinates[7]), 5, (0, 255, 0), -1) #Verde

            # Variable dispo es para ver la disponibilidad de la mesa y la variable output
            # es la actualización del frame con los dibujos de las manchas
            dispo, output = recrop(output, table_thresh, area, x, y)
            if dispo:
                unoccupied_tables += 1
            else:
                occupied_tables += 1

    # Obtiene la fecha y hora actual
    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

    # Escribe los datos en la hoja de cálculo
    datos = [unoccupied_tables, occupied_tables, fecha_hora]
    hoja = credenciales()
    hoja.append_row(datos)
    
    # Mostrar el video con los contornos de los rectángulos
    cv2.imshow("Mesa thresh", thresh)
    cv2.imshow("Mesa Analizada", output)
    cv2.waitKey(0)

    # Mostrar el número de mesas ocupadas y desocupadas
    print("Mesas Ocupadas: ", occupied_tables)
    print("Mesas Desocupadas: ", unoccupied_tables)

    # Lineas opcionales para el manejo de hilos
    # hilos
    # analysis_finished = True

# Boton para capturar el frame a analizar
capture_button = tk.Button(root, text="Capturar Video", command=capture)
capture_button.pack()

# Camara a utilizar, 0 es la camara default
cap = cv2.VideoCapture(0)

# Función para mostrar la camara en la ventana
def show_frame():
    global show_camera
    if show_camera:
        # Capturar el video actual
        ret, frame = cap.read()

        if ret:
            # Convertir el video de OpenCV a formato de imagen de PIL
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)

            # Mostrar la imagen en un label de tkinter
            label.config(image=photo)
            label.image = photo

    # Manejo de hilos (Opcional)
    #if capture_pressed:
    #    capture_pressed = False
    #    analysis_finished = False

        # Crear un nuevo hilo para ejecutar la función capture en segundo plano
    #    t = threading.Thread(target=capture)
    #    t.start()

    #if analysis_finished:
    #    analysis_finished = False

        # Abrir una nueva ventana para mostrar los resultados del análisis
    #    results_window = tk.Toplevel(root)
    #    results_window.title("Resultados del Análisis")

        # Mostrar el número de mesas ocupadas y desocupadas en un label de tkinter
    #    result_label = tk.Label(results_window, text="Mesas Ocupadas: " + str(occupied_tables) + "\nMesas Desocupadas: " + str(unoccupied_tables))
    #    result_label.pack()

    # Actualización del frame cada 10 milisegundos
    root.after(10, show_frame)

label = tk.Label(root)
label.pack()

show_frame()

root.mainloop()


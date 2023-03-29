import cv2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# Define las credenciales y autoriza el cliente
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credenciales = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
cliente = gspread.authorize(credenciales)

# Abre la hoja de cálculo
hoja_calculo = cliente.open("DatosCafeteria")

# Selecciona la hoja de cálculo en la que se escribirán los datos
hoja = hoja_calculo.worksheet("Sheet1")

# Define el intervalo de tiempo en segundos para enviar los datos
intervalo = 10

# Define el umbral para la umbralización de la imagen
umbral = 200

# Carga la imagen de la cámara
camara = cv2.VideoCapture(0)

while True:
    # Captura la imagen de la cámara
    ret, imagen = camara.read()

    # Convierte la imagen a escala de grises y aplica un filtro Gaussiano
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (5, 5), 0)

    # Aplica la umbralización para detectar los objetos blancos
    _, umbralizada = cv2.threshold(gris, umbral, 255, cv2.THRESH_BINARY)

    # Realiza una operación de dilatación para unir las áreas de píxeles blancos que puedan estar separados
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    umbralizada = cv2.dilate(umbralizada, kernel, iterations=2)

    # Encuentra los contornos de los objetos blancos en la imagen
    contornos, _ = cv2.findContours(umbralizada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filtra los contornos por su forma para encontrar los contornos de mesas rectangulares
    mesas = []
    for contorno in contornos:
        perimetro = cv2.arcLength(contorno, True)
        aprox = cv2.approxPolyDP(contorno, 0.02 * perimetro, True)
        if len(aprox) == 4 and cv2.contourArea(aprox) > 1000:
            mesas.append(aprox)

    # Dibuja un rectángulo alrededor de cada mesa y calcula su área para determinar si está ocupada o no
    mesas_ocupadas = 0
    mesas_disponibles = 0
    for mesa in mesas:
        x, y, w, h = cv2.boundingRect(mesa)
        cv2.rectangle(imagen, (x, y), (x + w, y + h), (0, 0, 255), 2)
        area = w * h
        if area > 10000:
            mesas_ocupadas += 1
        else:
            mesas_disponibles += 1

    # Obtiene la fecha y hora actual
    fecha_hora = time.strftime("%Y-%m-%d %H:%M:%S")

    # Escribe los datos en la hoja de cálculo
    datos = [mesas_disponibles, mesas_ocupadas, fecha_hora]
    hoja.append_row(datos)

    # Espera el tiempo definido en el intervalo antes de tomar la siguiente imagen
    time.sleep(intervalo)

    # Muestra la imagen con los rectángulos de las mesas
    cv2.imshow("Mesas de la cafetería", imagen)

    # Espera a que se presione la tecla 'q' para salir del bucle
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camara.release()
cv2.destroyAllWindows()






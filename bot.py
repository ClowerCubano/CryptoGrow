import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import uuid
import threading
import time
from flask import Flask, request

API_TOKEN = '7128943021:AAG1HAjOfS4K4mN_2IBynB-Jzqh1dpUQfts'
bot = telebot.TeleBot(API_TOKEN)

# Diccionario para almacenar las inversiones de los usuarios
inversiones = {}
pendientes = {}
retiros_pendientes = {}

# Función para aumentar el saldo de los usuarios cada 24 horas
def aumentar_saldo():
    while True:
        time.sleep(86400)  # Espera 24 horas
        for user_id in inversiones:
            if inversiones[user_id]['saldo'] >= 5:
                inversiones[user_id]['saldo'] *= 1.15

# Iniciar el hilo para aumentar el saldo
threading.Thread(target=aumentar_saldo).start()

# Comando de inicio
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.username if message.from_user.username else f"Usuario_{uuid.uuid4().hex[:8]}"
    inversiones[user_id] = {'nombre': user_name, 'saldo': 0, 'pendiente': 0}
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    invertir_btn = KeyboardButton('💰 Invertir')
    ver_inversiones_btn = KeyboardButton('📊 Ver Inversiones')
    retirar_btn = KeyboardButton('💸 Retirar')
    markup.add(invertir_btn, ver_inversiones_btn, retirar_btn)
    
    if user_id == 7507991049:
        bienvenida = (
            f"¡Bienvenido, Administrador {user_name}! 👑\n\n"
            "Tienes el poder total sobre este bot. Puedes gestionar inversiones, retiros y más. "
            "Selecciona una opción para continuar:"
        )
        bot.send_message(message.chat.id, bienvenida, reply_markup=markup)
        send_admin_panel(message)
    else:
        bienvenida = (
            f"¡Bienvenido, {user_name}! 🤖\n\n"
            "En este bot puedes invertir un mínimo de 5 USDT y recibir un 15% de ganancia diaria. "
            "Tu saldo se actualizará automáticamente cada 24 horas. 🔄\n\n"
            "Confianza y transparencia son nuestras prioridades. ¡Invierte con seguridad y observa cómo crecen tus ganancias! 💼📈"
        )
        bot.send_message(message.chat.id, bienvenida, reply_markup=markup)

# Comando para invertir
@bot.message_handler(func=lambda message: message.text == '💰 Invertir')
def invertir(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    retroceder_btn = KeyboardButton('🔙 Retroceder')
    markup.add(retroceder_btn)
    
    bot.send_message(message.chat.id, "Por favor, ingresa el monto que deseas invertir en el formato: /invertir [monto]", reply_markup=markup)

@bot.message_handler(commands=['invertir'])
def handle_invertir(message):
    user_id = message.from_user.id
    try:
        monto = float(message.text.split()[1])
        if monto >= 5:
            pendientes[user_id] = monto
            bot.reply_to(message, f"Has solicitado invertir {monto} USDT. Por favor, envía {monto} USDT a la siguiente dirección: TGg2AKwMxH552xQDFDriTafHb9cW4bsUUs\n\nTu inversión será revisada y aprobada por el administrador. ⏳")
            notify_admin(user_id, monto, "inversión")
        else:
            bot.reply_to(message, "El monto mínimo de inversión es 5 USDT. ❗")
    except (IndexError, ValueError):
        bot.reply_to(message, "Por favor, ingresa un monto válido. ❗")

# Comando para ver inversiones
@bot.message_handler(func=lambda message: message.text == '📊 Ver Inversiones')
def ver_inversiones(message):
    user_id = message.from_user.id
    if user_id in inversiones:
        saldo = inversiones[user_id]['saldo']
        pendiente = inversiones[user_id]['pendiente']
        bot.reply_to(message, f"Tu inversión actual es de {saldo} USDT. 💼\nInversiones pendientes: {pendiente} USDT. ⏳")
    else:
        bot.reply_to(message, "No tienes inversiones registradas. 📉")

# Comando para retirar
@bot.message_handler(func=lambda message: message.text == '💸 Retirar')
def retirar(message):
    user_id = message.from_user.id
    if user_id in inversiones and inversiones[user_id]['saldo'] > 0:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        retroceder_btn = KeyboardButton('🔙 Retroceder')
        markup.add(retroceder_btn)
        
        bot.send_message(message.chat.id, "Por favor, ingresa la cantidad que deseas retirar en el formato: /retirar [monto]", reply_markup=markup)
    else:
        bot.reply_to(message, "No tienes inversiones registradas para retirar. 📉")

@bot.message_handler(commands=['retirar'])
def handle_retirar(message):
    user_id = message.from_user.id
    try:
        monto = float(message.text.split()[1])
        if monto <= inversiones[user_id]['saldo']:
            retiros_pendientes[user_id] = {'monto': monto, 'direccion': None}
            bot.reply_to(message, "Por favor, ingresa tu dirección de retiro en el formato: /direccion [tu_direccion]")
        else:
            bot.reply_to(message, "El monto solicitado excede tu saldo disponible. ❗")
    except (IndexError, ValueError):
        bot.reply_to(message, "Por favor, ingresa un monto válido. ❗")

@bot.message_handler(commands=['direccion'])
def handle_direccion(message):
    user_id = message.from_user.id
    direccion = message.text.split()[1]
    if user_id in retiros_pendientes:
        retiros_pendientes[user_id]['direccion'] = direccion
        monto = retiros_pendientes[user_id]['monto']
        bot.reply_to(message, f"Solicitud de retiro de {monto} USDT enviada. Espera la aprobación del administrador. ⏳")
        notify_admin(user_id, monto, "retiro", direccion)
    else:
        bot.reply_to(message, "No tienes solicitudes de retiro pendientes. ❗")

# Panel de administración (solo para el administrador)
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        send_admin_panel(message)
    else:
        bot.reply_to(message, "No tienes permiso para acceder a este panel. 🚫")

def send_admin_panel(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    aceptar_btn = KeyboardButton('✅ Aceptar')
    rechazar_btn = KeyboardButton('❌ Rechazar')
    ver_pendientes_btn = KeyboardButton('📋 Ver Pendientes')
    markup.add(aceptar_btn, rechazar_btn, ver_pendientes_btn)
    
    bot.send_message(message.chat.id, "Panel de administración: Selecciona una opción para continuar:", reply_markup=markup)

# Aceptar transacciones
@bot.message_handler(func=lambda message: message.text == '✅ Aceptar')
def aceptar(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        bot.send_message(message.chat.id, "Por favor, ingresa el ID del usuario y el tipo de transacción (inversión/retiro) en el formato: /aceptar [user_id] [tipo]")
    else:
        bot.reply_to(message, "No tienes permiso para realizar esta acción. 🚫")

@bot.message_handler(commands=['aceptar'])
def handle_aceptar(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        try:
            user_id = int(message.text.split()[1])
            tipo = message.text.split()[2]
            if tipo == "inversión" and user_id in pendientes:
                monto = pendientes.pop(user_id)
                inversiones[user_id]['saldo'] += monto
                inversiones[user_id]['pendiente'] = 0
                bot.reply_to(message, f"Transacción de inversión de {user_id} aceptada. ✅")
                bot.send_message(user_id, f"Tu inversión de {monto} USDT ha sido aceptada. ✅")
            elif tipo == "retiro" and user_id in retiros_pendientes:
                direccion = retiros_pendientes[user_id]['direccion']
                monto = retiros_pendientes.pop(user_id)['monto']
                inversiones[user_id]['saldo'] -= monto
                bot.reply_to(message, f"Retiro de {user_id} aceptado. ✅\nDirección de retiro: {direccion}")
                bot.send_message(user_id, f"Tu retiro de {monto} USDT ha sido aceptado. ✅\nDirección de retiro: {direccion}")
            else:
                bot.reply_to(message, "Usuario no encontrado o tipo de transacción no válido. ❗")
        except (IndexError, ValueError):
            bot.reply_to(message, "Por favor, ingresa un ID de usuario y tipo de transacción válidos. ❗")
    else:
        bot.reply_to(message, "No tienes permiso para realizar esta acción. 🚫")

# Rechazar transacciones
@bot.message_handler(func=lambda message: message.text == '❌ Rechazar')
def rechazar(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        bot.send_message(message.chat.id, "Por favor, ingresa el ID del usuario y el tipo de transacción (inversión/retiro) en el formato: /rechazar [user_id] [tipo]")
    else:
        bot.reply_to(message, "No tienes permiso para realizar esta acción. 🚫")

@bot.message_handler(commands=['rechazar'])
def handle_rechazar(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        try:
            user_id = int(message.text.split()[1])
            tipo = message.text.split()[2]
            if tipo == "inversión" and user_id in pendientes:
                pendientes.pop(user_id)
                bot.reply_to(message, f"Transacción de inversión de {user_id} rechazada. ❌")
                bot.send_message(user_id, f"Tu solicitud de inversión de {monto} USDT ha sido rechazada. ❌")
            elif tipo == "retiro" and user_id in retiros_pendientes:
                retiros_pendientes.pop(user_id)
                bot.reply_to(message, f"Transacción de retiro de {user_id} rechazada. ❌")
                bot.send_message(user_id, f"Tu solicitud de retiro de {monto} USDT ha sido rechazada. ❌")
            else:
                bot.reply_to(message, "Usuario no encontrado o tipo de transacción no válido. ❗")
        except (IndexError, ValueError):
            bot.reply_to(message, "Por favor, ingresa un ID de usuario y tipo de transacción válidos. ❗")
    else:
        bot.reply_to(message, "No tienes permiso para realizar esta acción. 🚫")

# Ver transacciones pendientes
@bot.message_handler(func=lambda message: message.text == '📋 Ver Pendientes')
def ver_pendientes(message):
    admin_id = 7507991049
    if message.from_user.id == admin_id:
        pendientes_list = "\n".join([f"Usuario: {user_id}, Monto: {monto} USDT" for user_id, monto in pendientes.items()])
        if pendientes_list:
            bot.send_message(message.chat.id, f"Transacciones pendientes:\n{pendientes_list}")
        else:
            bot.send_message(message.chat.id, "No hay transacciones pendientes. ✅")
    else:
        bot.reply_to(message, "No tienes permiso para realizar esta acción. 🚫")

# Comando para retroceder
@bot.message_handler(func=lambda message: message.text == '🔙 Retroceder')
def retroceder(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    invertir_btn = KeyboardButton('💰 Invertir')
    ver_inversiones_btn = KeyboardButton('📊 Ver Inversiones')
    retirar_btn = KeyboardButton('💸 Retirar')
    markup.add(invertir_btn, ver_inversiones_btn, retirar_btn)
    
    bot.send_message(message.chat.id, "Selecciona una opción para continuar:", reply_markup=markup)

def notify_admin(user_id, monto, tipo, direccion=None):
    admin_id = 7507991049
    if tipo == "retiro" and direccion:
        bot.send_message(admin_id, f"Solicitud de {tipo} pendiente:\nUsuario: {user_id}\nMonto: {monto} USDT\nDirección: {direccion}\n\nUsa /aceptar {user_id} {tipo} o /rechazar {user_id} {tipo} para gestionar la solicitud.")
    else:
        bot.send_message(admin_id, f"Solicitud de {tipo} pendiente:\nUsuario: {user_id}\nMonto: {monto} USDT\n\nUsa /aceptar {user_id} {tipo} o /rechazar {user_id} {tipo} para gestionar la solicitud.")

# Configuración de Flask para webhooks
app = Flask(__name__)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://growoficial.onrender.com' + API_TOKEN)
    return 'Webhook set', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8443)
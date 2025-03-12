import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '7416714322:AAGXebv84pd7npdB_xs5BBUXjYT5IYWtRvs'
ADMIN_CHAT_ID = '1883277776'  # Replace with your admin's chat ID
bot = telebot.TeleBot(TOKEN)

# Sample car data with Uzbekistan-specific cars
cars = {
    'sedan': {
        '1': {'model': 'Chevrolet Cobalt', 'price': 15000, 'mileage': '18 km/l', 'fuel': 'Petrol', 'image_path': 'cobalt.jpeg'},
        '2': {'model': 'Hyundai Sonata', 'price': 25000, 'mileage': '20 km/l', 'fuel': 'Petrol', 'image_path': 'hy.jpeg'},
    },
    'suv': {
        '3': {'model': 'Chevrolet Captiva', 'price': 30000, 'mileage': '15 km/l', 'fuel': 'Diesel', 'image_path': 'captiva.jpeg'},
        '4': {'model': 'Toyota Land Cruiser Prado', 'price': 60000, 'mileage': '12 km/l', 'fuel': 'Diesel', 'image_path': 'toyota.jpeg'},
    },
    'sports': {
        '5': {'model': 'Lada Vesta Sport', 'price': 20000, 'mileage': '14 km/l', 'fuel': 'Petrol', 'image_path': 'lada.jpeg'},
        '6': {'model': 'BMW M5', 'price': 120000, 'mileage': '10 km/l', 'fuel': 'Petrol', 'image_path': 'bmw.jpeg'},
    },
}

user_likes = {}  # To store liked cars for each user
user_data = {}  # To store temporary user data for test drive booking

# Main menu keyboard
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton('🚗 Browse Cars'), KeyboardButton('❤️ Liked Cars'))
    markup.add(KeyboardButton('📅 Book Test Drive'), KeyboardButton('ℹ️ Help'))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🚗 Welcome to the Car Marketplace Bot! Use the buttons below or commands to navigate.", reply_markup=main_menu())

# Slash command for browsing cars
@bot.message_handler(commands=['products'])
def show_categories_command(message):
    show_categories(message)

# Slash command for viewing liked cars
@bot.message_handler(commands=['liked'])
def show_liked_cars_command(message):
    show_liked_cars(message)

# Slash command for booking a test drive
@bot.message_handler(commands=['testdrive'])
def book_test_drive_command(message):
    bot.send_message(message.chat.id, "📅 Please provide the car model you want to book a test drive for:")
    user_data[message.chat.id] = {'step': 'ask_car_model'}

# Slash command for help
@bot.message_handler(commands=['help'])
def send_help_command(message):
    send_help(message)

@bot.message_handler(func=lambda message: message.text == '🚗 Browse Cars')
def show_categories(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Sedan", callback_data='category_sedan'))
    markup.add(InlineKeyboardButton("SUV", callback_data='category_suv'))
    markup.add(InlineKeyboardButton("Sports", callback_data='category_sports'))
    bot.send_message(message.chat.id, "📂 Choose a car category:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def show_cars_in_category(call):
    category = call.data.split('_')[1]
    if category in cars:
        markup = InlineKeyboardMarkup()
        for car_id, car in cars[category].items():
            markup.add(InlineKeyboardButton(car['model'], callback_data=f'car_{car_id}'))
        markup.add(InlineKeyboardButton("⬅️ Back to Categories", callback_data='back_to_categories'))
        bot.send_message(call.message.chat.id, f"🚗 Cars in {category.capitalize()} category:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "❌ No cars found in this category.")

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_categories')
def back_to_categories(call):
    show_categories(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('car_'))
def car_details(call):
    car_id = call.data.split('_')[1]
    car = None
    for category in cars.values():
        if car_id in category:
            car = category[car_id]
            break
    if car:
        message = (
            f"🚗 *{car['model']}*\n"
            f"💵 *Price:* ${car['price']}\n"
            f"🛣️ *Mileage:* {car['mileage']}\n"
            f"⛽ *Fuel Type:* {car['fuel']}"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❤️ Like", callback_data=f'like_{car_id}'))
        markup.add(InlineKeyboardButton("📅 Book Test Drive", callback_data=f'testdrive_{car_id}'))
        markup.add(InlineKeyboardButton("⬅️ Back to Cars", callback_data='back_to_categories'))
        
        # Send the image along with the car details
        with open(car['image_path'], 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=message, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(call.message.chat.id, "❌ Car not found.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def like_car(call):
    car_id = call.data.split('_')[1]
    user_id = call.message.chat.id
    if user_id not in user_likes:
        user_likes[user_id] = []
    car = None
    for category in cars.values():
        if car_id in category:
            car = category[car_id]
            break
    if car and car not in user_likes[user_id]:
        user_likes[user_id].append(car)
        bot.answer_callback_query(call.id, "❤️ Car added to your liked list!")
        bot.send_message(user_id, f"❤️ You liked *{car['model']}*! It has been added to your liked list.", parse_mode='Markdown')
    else:
        bot.answer_callback_query(call.id, "✅ Car is already in your liked list.")

@bot.message_handler(func=lambda message: message.text == '❤️ Liked Cars')
def show_liked_cars(message):
    user_id = message.chat.id
    if user_id in user_likes and user_likes[user_id]:
        # Count the number of liked cars and group by category
        category_count = {}
        for car in user_likes[user_id]:
            category = next((cat for cat, cars_in_cat in cars.items() if car in cars_in_cat.values()), None)
            if category:
                category_count[category] = category_count.get(category, 0) + 1

        # Prepare the liked cars summary
        liked_summary = "❤️ *Your Liked Cars:*\n"
        liked_summary += f"📊 *Total Liked Cars:* {len(user_likes[user_id])}\n"
        for category, count in category_count.items():
            liked_summary += f"🚗 *{category.capitalize()} Cars:* {count}\n"

        bot.send_message(user_id, liked_summary, parse_mode='Markdown')

        # Resend the liked car posts (images and details)
        for car in user_likes[user_id]:
            message = (
                f"🚗 *{car['model']}*\n"
                f"💵 *Price:* ${car['price']}\n"
                f"🛣️ *Mileage:* {car['mileage']}\n"
                f"⛽ *Fuel Type:* {car['fuel']}"
            )
            with open(car['image_path'], 'rb') as photo:
                bot.send_photo(user_id, photo, caption=message, parse_mode='Markdown')
    else:
        bot.send_message(user_id, "❤️ You haven't liked any cars yet.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == 'ask_car_model')
def ask_car_model(message):
    user_id = message.chat.id
    car_model = message.text
    car = None
    for category in cars.values():
        for car_id, car_info in category.items():
            if car_info['model'].lower() == car_model.lower():
                car = car_info
                break
    if car:
        user_data[user_id] = {'step': 'ask_testdrive_date', 'car': car}
        bot.send_message(user_id, "📅 Please provide the date for your test drive (e.g., DD/MM/YYYY):")
    else:
        bot.send_message(user_id, "❌ Car not found. Please try again.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('testdrive_'))
def book_test_drive(call):
    car_id = call.data.split('_')[1]
    user_id = call.message.chat.id
    car = None
    for category in cars.values():
        if car_id in category:
            car = category[car_id]
            break
    if car:
        user_data[user_id] = {'step': 'ask_testdrive_date', 'car': car}
        bot.send_message(user_id, "📅 Please provide the date for your test drive (e.g., DD/MM/YYYY):")
    else:
        bot.send_message(user_id, "❌ Car not found.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == 'ask_testdrive_date')
def ask_testdrive_date(message):
    user_id = message.chat.id
    user_data[user_id]['testdrive_date'] = message.text
    user_data[user_id]['step'] = 'ask_contact'

    # Create a keyboard with a "Share Contact" button
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📞 Share Contact", request_contact=True))
    bot.send_message(user_id, "📞 Please provide your contact number or use the button below to share your Telegram contact:", reply_markup=markup)

@bot.message_handler(content_types=['contact', 'text'])
def ask_contact(message):
    user_id = message.chat.id

    # Check if the user is in the 'ask_contact' step
    if user_data.get(user_id, {}).get('step') != 'ask_contact':
        return  # Exit if the user is not in the correct step

    # Check if the user shared their contact via the "Share Contact" button
    if message.contact:
        contact = message.contact.phone_number
    else:
        # If the user typed their contact manually
        contact = message.text

    # Save the contact number
    user_data[user_id]['contact'] = contact
    car = user_data[user_id]['car']
    date = user_data[user_id]['testdrive_date']

    # Notify admin about the test drive booking
    admin_message = (
        f"📅 *New Test Drive Booking!*\n"
        f"👤 *User ID:* {user_id}\n"
        f"🚗 *Car:* {car['model']}\n"
        f"📅 *Date:* {date}\n"
        f"📞 *Contact:* {contact}"
    )
    bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode='Markdown')

    # Confirm to the user
    bot.send_message(user_id, f"✅ Your test drive for *{car['model']}* on *{date}* has been booked! We'll contact you at *{contact}*.", parse_mode='Markdown')

    # Clear temporary data
    user_data.pop(user_id, None)

    # Return to the main menu
    bot.send_message(user_id, "⬅️ Returning to the main menu...", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Help')
def send_help(message):
    help_message = (
        "ℹ️ *Available Commands:*\n"
        "🚗 /start - Start the bot\n"
        "🚗 /products - Browse cars by category\n"
        "❤️ /liked - View your liked cars\n"
        "📅 /testdrive - Book a test drive\n"
        "ℹ️ /help - Get help"
    )
    bot.send_message(message.chat.id, help_message, parse_mode='Markdown')

bot.polling(none_stop=True)
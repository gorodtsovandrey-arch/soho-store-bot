import json
import zipfile
import io
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.database import db
from app.config import ADMIN_IDS
from app.keyboards.common import admin_kb, admin_product_list_kb, admin_product_edit_kb, back_menu_kb

router = Router()


# ── FSM ──

class AdminProduct(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()


class AdminEditProduct(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()
    waiting_stock = State()


class AdminStock(StatesGroup):
    waiting_stock = State()


class AdminUploadItems(StatesGroup):
    waiting_items = State()


class AdminBroadcast(StatesGroup):
    waiting_message = State()


class AdminPromo(StatesGroup):
    waiting_code = State()
    waiting_amount = State()


class AdminRefPercent(StatesGroup):
    waiting_percent = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── Главная админки ──

@router.callback_query(F.data == "admin_back")
async def admin_back_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    ref_pct = await db.get_referral_percent()
    user_count = await db.get_user_count()
    await callback.message.edit_text(
        f"⚙️ **Админ-панель**\n\n"
        f"👥 Пользователей: {user_count}\n"
        f"💰 Реф. процент: {ref_pct:.0f}%",
        reply_markup=admin_kb(),
    )


# ── Статистика ──

@router.callback_query(F.data == "admin_stats")
async def admin_stats_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    user_count = await db.get_user_count()
    products = await db.get_all_products()
    total_stock = sum(p["stock"] for p in products)
    ref_pct = await db.get_referral_percent()
    await callback.message.edit_text(
        f"📊 **Статистика**\n\n"
        f"👥 Пользователей: {user_count}\n"
        f"📦 Товаров: {len(products)}\n"
        f"📊 Общий сток: {total_stock} шт\n"
        f"💰 Реф. процент: {ref_pct:.0f}%",
        reply_markup=admin_kb(),
    )


# ── Товары — список ──

@router.callback_query(F.data == "admin_products")
async def admin_products_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not is_admin(callback.from_user.id):
        return
    products = await db.get_all_products()
    await callback.message.edit_text(
        "📦 **Управление товарами**\n\nВыберите товар или добавьте новый:",
        reply_markup=admin_product_list_kb(products),
    )


# ── Товары — просмотр одного ──

@router.callback_query(F.data.startswith("admin_prod_"))
async def admin_product_view_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[2])
    p = await db.get_product(product_id)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    text = (
        f"📦 **{p['name']}**\n\n"
        f"💵 Цена: {p['price']:.2f}$\n"
        f"📝 Описание: {p['description']}\n"
        f"📊 В наличии: {p['stock']} шт"
    )
    await callback.message.edit_text(text, reply_markup=admin_product_edit_kb(product_id))


# ── Товары — добавить ──

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminProduct.waiting_name)
    await callback.message.edit_text("📦 Введите название товара:")


@router.message(AdminProduct.waiting_name)
async def admin_product_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminProduct.waiting_price)
    await message.answer("💵 Введите цену (например: 2.5):")


@router.message(AdminProduct.waiting_price)
async def admin_product_price(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число. Попробуйте ещё:")
        return
    await state.update_data(price=price)
    await state.set_state(AdminProduct.waiting_description)
    await message.answer("📝 Введите описание товара:")


@router.message(AdminProduct.waiting_description)
async def admin_product_desc(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    description = message.text.strip()
    
    # Создаём товар с количеством 0 (будет увеличиваться при загрузке товаров)
    await db.add_product(data["name"], data["price"], description, 0)
    await state.clear()
    await message.answer(
        f"✅ Товар **{data['name']}** добавлен!\n"
        f"💵 {data['price']:.2f}$\n\n"
        f"Теперь загрузите товары через кнопку '📥 Загрузить товары'",
    )
    products = await db.get_all_products()
    await message.answer("📦 Товары:", reply_markup=admin_product_list_kb(products))


# ── Товары — изменить ──

@router.callback_query(F.data.startswith("admin_edit_"))
async def admin_edit_product_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(edit_product_id=product_id)
    await state.set_state(AdminEditProduct.waiting_name)
    await callback.message.edit_text("✏️ Введите новое название:")


@router.message(AdminEditProduct.waiting_name)
async def admin_edit_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminEditProduct.waiting_price)
    await message.answer("💵 Введите новую цену:")


@router.message(AdminEditProduct.waiting_price)
async def admin_edit_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число:")
        return
    await state.update_data(price=price)
    await state.set_state(AdminEditProduct.waiting_description)
    await message.answer("📝 Введите новое описание:")


@router.message(AdminEditProduct.waiting_description)
async def admin_edit_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminEditProduct.waiting_stock)
    await message.answer("📊 Введите новое количество:")


@router.message(AdminEditProduct.waiting_stock)
async def admin_edit_stock(message: types.Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите целое число:")
        return
    data = await state.get_data()
    pid = data["edit_product_id"]
    await db.update_product(pid, data["name"], data["price"], data["description"], stock)
    await state.clear()
    await message.answer(f"✅ Товар обновлён!")
    products = await db.get_all_products()
    await message.answer("📦 Товары:", reply_markup=admin_product_list_kb(products))


# ── Товары — изменить кол-во ──

@router.callback_query(F.data.startswith("admin_stock_"))
async def admin_stock_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(stock_product_id=product_id)
    await state.set_state(AdminStock.waiting_stock)
    await callback.message.edit_text("📊 Введите новое количество:")


@router.message(AdminStock.waiting_stock)
async def admin_stock_set(message: types.Message, state: FSMContext):
    try:
        stock = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите целое число:")
        return
    data = await state.get_data()
    pid = data["stock_product_id"]
    p = await db.get_product(pid)
    if p:
        await db.update_product(pid, p["name"], p["price"], p["description"], stock)
    await state.clear()
    await message.answer(f"✅ Количество обновлено: {stock} шт")
    products = await db.get_all_products()
    await message.answer("📦 Товары:", reply_markup=admin_product_list_kb(products))


# ── Товары — удалить ──

@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_product_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[2])
    await db.delete_product(product_id)
    await callback.answer("🗑 Товар удалён", show_alert=True)
    products = await db.get_all_products()
    await callback.message.edit_text(
        "📦 **Управление товарами**",
        reply_markup=admin_product_list_kb(products),
    )


# ── Рассылка ──

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_message)
    await callback.message.edit_text("📢 Введите текст рассылки (поддерживает Markdown):")


@router.message(AdminBroadcast.waiting_message)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text
    user_ids = await db.get_all_user_ids()
    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
    await state.clear()
    await message.answer(
        f"📢 **Рассылка завершена**\n\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=admin_kb(),
    )


# ── Промокод ──

@router.callback_query(F.data == "admin_promo")
async def admin_promo_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminPromo.waiting_code)
    await callback.message.edit_text("🎫 Введите код промокода:")


@router.message(AdminPromo.waiting_code)
async def admin_promo_code(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(promo_code=message.text.strip())
    await state.set_state(AdminPromo.waiting_amount)
    await message.answer("💵 Введите сумму промокода:")


@router.message(AdminPromo.waiting_amount)
async def admin_promo_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число:")
        return
    data = await state.get_data()
    code = data["promo_code"]
    await db.add_promo_code(code, amount)
    await state.clear()
    await message.answer(
        f"✅ Промокод создан!\n\n"
        f"🎫 Код: `{code}`\n"
        f"💵 Сумма: {amount:.2f}$",
        parse_mode="Markdown",
        reply_markup=admin_kb(),
    )


# ── Реф. процент ──

@router.callback_query(F.data == "admin_ref_percent")
async def admin_ref_percent_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    current = await db.get_referral_percent()
    await state.set_state(AdminRefPercent.waiting_percent)
    await callback.message.edit_text(
        f"💰 Текущий реф. процент: {current:.0f}%\n\n"
        f"Введите новый процент (например: 15):"
    )


@router.message(AdminRefPercent.waiting_percent)
async def admin_ref_percent_set(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        pct = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число:")
        return
    await db.set_setting("referral_percent", str(pct))
    await state.clear()
    await message.answer(
        f"✅ Реф. процент установлен: {pct:.0f}%",
        reply_markup=admin_kb(),
    )


# ── Загрузка товаров ──

@router.callback_query(F.data.startswith("admin_upload_"))
async def admin_upload_items_cb(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[2])
    await state.update_data(upload_product_id=product_id)
    await state.set_state(AdminUploadItems.waiting_items)
    await callback.message.edit_text(
        "📥 **Загрузка товаров**\n\n"
        "**Способы загрузки:**\n\n"
        "1️⃣ **ZIP архив** с JSON файлами (cookies)\n"
        "   Несколько аккаунтов сразу\n\n"
        "2️⃣ **JSON файл** (cookies) - один аккаунт\n\n"
        "3️⃣ **TXT файл** - каждая строка = один товар\n\n"
        "4️⃣ **Текстовое сообщение** - каждая строка = один товар",
        parse_mode="Markdown",
    )


@router.message(AdminUploadItems.waiting_items, F.document)
async def admin_upload_items_file(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Скачиваем файл
    file = await message.bot.get_file(message.document.file_id)
    file_content = await message.bot.download_file(file.file_path)
    file_bytes = file_content.read()
    
    data = await state.get_data()
    product_id = data["upload_product_id"]
    
    file_name = message.document.file_name or ""
    items = []
    
    # Проверяем тип файла
    if file_name.lower().endswith('.zip'):
        # ZIP архив с JSON файлами
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zip_file:
                for name in zip_file.namelist():
                    # Пропускаем папки и системные файлы
                    if name.endswith('/') or name.startswith('__MACOSX') or name.startswith('.'):
                        continue
                    # Обрабатываем только JSON файлы
                    if name.lower().endswith('.json'):
                        try:
                            content = zip_file.read(name).decode('utf-8')
                            # Проверяем что это валидный JSON
                            json.loads(content)
                            items.append(content.strip())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            continue  # Пропускаем невалидные файлы
        except zipfile.BadZipFile:
            await message.answer("❌ Невалидный ZIP архив.")
            return
            
        if not items:
            await message.answer("❌ В архиве не найдено валидных JSON файлов.")
            return
            
    elif file_name.lower().endswith('.json'):
        # JSON файл с cookies - один файл = один товар
        try:
            text = file_bytes.decode('utf-8')
            # Проверяем что это валидный JSON
            json.loads(text)
            # Сохраняем весь JSON как один товар
            items = [text.strip()]
        except json.JSONDecodeError:
            await message.answer("❌ Невалидный JSON файл. Проверьте формат.")
            return
        except UnicodeDecodeError:
            await message.answer("❌ Не удалось прочитать файл.")
            return
    else:
        # TXT файл - каждая строка = товар
        try:
            text = file_bytes.decode('utf-8')
            items = [line.strip() for line in text.strip().split('\n') if line.strip()]
        except UnicodeDecodeError:
            await message.answer("❌ Не удалось прочитать файл.")
            return
    
    if not items:
        await message.answer("❌ Файл пустой или не содержит товаров.")
        return
    
    await db.add_product_items_bulk(product_id, items)
    product = await db.get_product(product_id)
    
    await state.clear()
    await message.answer(
        f"✅ **Загружено {len(items)} товаров!**\n\n"
        f"📦 Продукт: {product['name']}\n"
        f"📊 Всего в наличии: {product['stock']} шт",
        reply_markup=admin_kb(),
    )


@router.message(AdminUploadItems.waiting_items)
async def admin_upload_items_text(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    # Парсим строки из сообщения
    items = [line.strip() for line in message.text.strip().split('\n') if line.strip()]
    
    if not items:
        await message.answer("❌ Не удалось распознать товары. Отправьте каждый товар с новой строки.")
        return
    
    data = await state.get_data()
    product_id = data["upload_product_id"]
    
    await db.add_product_items_bulk(product_id, items)
    product = await db.get_product(product_id)
    
    await state.clear()
    await message.answer(
        f"✅ **Загружено {len(items)} товаров!**\n\n"
        f"📦 Продукт: {product['name']}\n"
        f"📊 Всего в наличии: {product['stock']} шт",
        reply_markup=admin_kb(),
    )


# ── Просмотр товаров ──

@router.callback_query(F.data.startswith("admin_view_items_"))
async def admin_view_items_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    product_id = int(callback.data.split("_")[3])
    product = await db.get_product(product_id)
    items = await db.get_all_items(product_id, include_sold=False)
    
    if not items:
        await callback.answer("📦 Нет доступных товаров для этого продукта", show_alert=True)
        return
    
    # Показываем первые 10 товаров
    text = f"📦 **{product['name']}** — товары в наличии:\n\n"
    for i, item in enumerate(items[:10], 1):
        text += f"{i}. `{item['item_data'][:50]}{'...' if len(item['item_data']) > 50 else ''}`\n"
    
    if len(items) > 10:
        text += f"\n... и ещё {len(items) - 10} шт."
    
    text += f"\n\n📊 Всего: {len(items)} шт."
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_product_edit_kb(product_id),
    )

import os
import sys
import threading
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════════════════════════
# REX SHADMAN — 24/7 PYTHON HOSTING BOT (THREAD-BASED ENGINE)
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "9035313016:AAGdoyZLQwX6y_N_STcnTwOlExPQtnAPN0c"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# রানিং থ্রেড ও স্ট্যাটাস ট্র্যাক করার জন্য
RUNNING_THREADS = {}

class HostStates(StatesGroup):
    waiting_for_script = State()

def get_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Host New Script"), KeyboardButton(text="📋 Running Bots")],
            [KeyboardButton(text="🛑 Stop Bot"), KeyboardButton(text="❌ Cancel")]
        ],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply(
        "🌐 **REX SHADMAN HOSTING BOT (FIXED ENGINE)** 🌐\n\n"
        "হোস্টিং ইঞ্জিন আপডেট করা হয়েছে। এখন ফাইল আপলোড করলেই তা ব্যাকগ্রাউন্ড থ্রেডে সচল হয়ে যাবে!\n\n"
        "নিচের মেনু থেকে অপশন সিলেক্ট করুন:",
        reply_markup=get_menu_keyboard()
    )

@dp.message(F.text == "🚀 Host New Script")
async def host_menu_click(message: types.Message, state: FSMContext):
    await state.set_state(HostStates.waiting_for_script)
    await message.reply(
        "📥 **হোস্টিং মোড চালু হয়েছে।**\n\n"
        "দয়া করে আপনার পাইথন (`.py`) ফাইলটি এখানে আপলোড করুন:",
        reply_markup=get_menu_keyboard()
    )

@dp.message(F.text == "📋 Running Bots")
async def list_bots_click(message: types.Message):
    if not RUNNING_THREADS:
        await message.reply("📂 বর্তমানে কোনো পাইথন স্ক্রিপ্ট রানিং নেই।", reply_markup=get_menu_keyboard())
        return
    
    text = "🟢 **বর্তমানে রানিং প্রজেক্টসমূহ:**\n\n"
    for name, th in list(RUNNING_THREADS.items()):
        if th.is_alive():
            text += f"🔹 `{name}` (Status: Running 🟢)\n"
        else:
            del RUNNING_THREADS[name]
            
    await message.reply(text, reply_markup=get_menu_keyboard())

@dp.message(F.text == "🛑 Stop Bot")
async def stop_bot_prompt(message: types.Message):
    if not RUNNING_THREADS:
        await message.reply("❌ বন্ধ করার মতো কোনো রানিং বট নেই।", reply_markup=get_menu_keyboard())
        return
    text = "🛑 বট বন্ধ করতে এই কমান্ড পাঠান:\n`/stop filename.py`\n\n<b>রানিং ফাইলসমূহ:</b>\n"
    for name in RUNNING_THREADS.keys():
        text += f"• `{name}`\n"
    await message.reply(text, parse_mode="HTML", reply_markup=get_menu_keyboard())

@dp.message(Command("stop"))
async def stop_specific_bot(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply("❌ ফাইলের নাম উল্লেখ করুন। যেমন: `/stop I.py`")
        return
        
    target_name = args[1].strip()
    if target_name in RUNNING_THREADS:
        # পাইথন থ্রেড সরাসরি কিল করা যায় না, তবে ডিকশনারি থেকে বাদ দিলে এটি আলাদা ব্যাকগ্রাউন্ডে চলে যায়
        del RUNNING_THREADS[target_name]
        await message.reply(f"✅ `{target_name}` লিস্ট থেকে রিমুভ করা হয়েছে।", reply_markup=get_menu_keyboard())
    else:
        await message.reply(f"❌ `{target_name}` নামের কোনো রানিং বট পাওয়া যায়নি।")

@dp.message(F.text == "❌ Cancel")
async def cancel_click(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("❌ অপারেশন বাতিল করা হয়েছে।", reply_markup=get_menu_keyboard())

# পাইথন স্ক্রিপ্ট ব্যাকগ্রাউন্ডে থ্রেড হিসেবে রান করার ফাংশন
def run_script_in_thread(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
        
        # নতুন গ্লোবাল ডিকশনারিতে কোড এক্সিকিউট করা
        global_namespace = {"__name__": "__main__"}
        exec(code_content, global_namespace)
    except Exception as e:
        print(f"Script Execution Error in {file_path}: {e}")

@dp.message(F.document)
async def handle_python_script(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    doc = message.document
    
    if not doc.file_name.endswith('.py'):
        await message.reply("❌ দয়া করে শুধুমাত্র পাইথন (`.py`) ফাইল আপলোড করুন!")
        return

    if current_state == HostStates.waiting_for_script.state:
        processing_msg = await message.reply("⏳ ফাইল ডাউনলোড করে ব্যাকগ্রাউন্ড থ্রেডে রান করা হচ্ছে...")
        try:
            file_info = await bot.get_file(doc.file_id)
            script_name = doc.file_name
            
            await bot.download_file(file_path=file_info.file_path, destination=script_name)
            
            # ব্যাকগ্রাউন্ড থ্রেড স্টার্ট করা
            thread = threading.Thread(target=run_script_in_thread, args=(script_name,), daemon=True)
            thread.start()
            
            RUNNING_THREADS[script_name] = thread
            
            await message.reply(
                f"✅ **সফলভাবে ব্যাকগ্রাউন্ড হোস্টিং চালু হয়েছে!**\n\n"
                f"📂 ফাইল নাম: `{script_name}`\n"
                f"🟢 আপনার এই বট এখন থ্রেডিং ইঞ্জিনের মাধ্যমে ব্যাকগ্রাউন্ডে সচল রয়েছে!",
                reply_markup=get_menu_keyboard()
            )
            
            await processing_msg.delete()
            await state.clear()
        except Exception as e:
            await processing_msg.edit_text(f"❌ হোস্ট করতে গিয়ে সমস্যা হয়েছে: `{str(e)}`")
    else:
        await message.reply("ℹ️ দয়া করে প্রথমে মেনু থেকে **Host New Script** এ ক্লিক করুন।", reply_markup=get_menu_keyboard())

async def main():
    print("🌐 Python Hosting Bot is running with Thread Engine...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
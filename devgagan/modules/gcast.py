import asyncio
import traceback
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid

from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users


# Optional: Predefined broadcast buttons
BROADCAST_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔥 Try Bot", url="https://t.me/Saverestrictedcontents01_bot")],
    [InlineKeyboardButton("💎 Upgrade Premium", url="https://t.me/arsh_beniwal")]
])


async def send_msg(user_id, content, is_text=True):
    try:
        if is_text:
            await app.send_message(
                chat_id=user_id,
                text=content,
                reply_markup=BROADCAST_BUTTONS,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            x = await content.copy(chat_id=user_id, reply_markup=BROADCAST_BUTTONS)
            try:
                await x.pin()
            except Exception:
                pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_msg(user_id, content, is_text)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        return False
    except Exception:
        print(traceback.format_exc())
        return False
    return True


@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    to_send = message.reply_to_message or (
        message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None
    )

    if not to_send:
        return await message.reply_text("❌ Reply to a message or add text after /gcast.")

    exmsg = await message.reply_text("📤 Starting broadcast with buttons...")

    all_users = await get_users() or []
    done_users = 0
    failed_users = 0

    for user in all_users:
        try:
            success = await send_msg(int(user), to_send, isinstance(to_send, str))
            if success:
                done_users += 1
            else:
                failed_users += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed_users += 1

    await exmsg.edit_text(
        f"✅ **Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(all_users)}`\n"
        f"📤 Sent to: `{done_users}` users\n"
        f"❌ Failed: `{failed_users}` users"
    )


@app.on_message(filters.command("acast") & filters.user(OWNER_ID))
async def announced(_, message):
    users = await get_users() or []
    done_users = 0
    failed_users = 0

    # Forward message if replied to
    if message.reply_to_message:
        msg_id = message.reply_to_message.id
        chat_id = message.chat.id
        exmsg = await message.reply_text("📣 Starting forward broadcast...")

        for user in users:
            try:
                await app.forward_messages(
                    chat_id=int(user),
                    from_chat_id=chat_id,
                    message_ids=msg_id
                )
                done_users += 1
                await asyncio.sleep(0.1)
            except Exception:
                failed_users += 1

    # Or send plain text
    elif len(message.text.split()) > 1:
        broadcast_text = message.text.split(None, 1)[1]
        exmsg = await message.reply_text("📤 Starting text forward broadcast...")

        for user in users:
            try:
                await app.send_message(
                    chat_id=int(user),
                    text=broadcast_text,
                    reply_markup=BROADCAST_BUTTONS,
                    parse_mode=ParseMode.MARKDOWN
                )
                done_users += 1
                await asyncio.sleep(0.1)
            except Exception:
                failed_users += 1

    else:
        return await message.reply_text("❌ Reply to a message or type a message after /acast.")

    await exmsg.edit_text(
        f"✅ **Acast Broadcast Completed**\n\n"
        f"👥 Total Users: `{len(users)}`\n"
        f"📤 Sent to: `{done_users}` users\n"
        f"❌ Failed: `{failed_users}` users"
    )

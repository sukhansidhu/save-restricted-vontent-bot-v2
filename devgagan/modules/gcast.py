# ---------------------------------------------------
# File Name: gcast.py
# Description: Broadcast & forward messages to users
# Author: Gagan (Updated by ChatGPT)
# ---------------------------------------------------

import asyncio
import traceback
from pyrogram import filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from config import OWNER_ID
from devgagan import app
from devgagan.core.mongo.users_db import get_users


# Function to copy and pin message (used in gcast)
async def send_msg(user_id, message):
    try:
        x = await message.copy(chat_id=user_id)
        try:
            await x.pin()
        except Exception:
            try:
                await x.pin(both_sides=True)
            except Exception:
                pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception:
        return 500, f"{user_id} : {traceback.format_exc()}\n"


# /gcast command: broadcast via copy (reply or text)
@app.on_message(filters.command("gcast") & filters.user(OWNER_ID))
async def broadcast(_, message):
    to_send = message.reply_to_message or (
        message.text.split(None, 1)[1] if len(message.text.split()) > 1 else None
    )

    if not to_send:
        return await message.reply_text("❌ Reply to a message or add text after /gcast.")

    exmsg = await message.reply_text("📤 Starting broadcast...")
    all_users = await get_users() or []
    done_users = 0
    failed_users = 0

    for user in all_users:
        try:
            if isinstance(to_send, str):
                await app.send_message(chat_id=int(user), text=to_send)
            else:
                await send_msg(int(user), to_send)
            done_users += 1
            await asyncio.sleep(0.1)
        except Exception:
            failed_users += 1

    await exmsg.edit_text(
        f"✅ **Broadcast Finished**\n\n"
        f"📤 Sent to: `{done_users}` users\n"
        f"❌ Failed: `{failed_users}` users"
    )


# /acast command: forward or text broadcast
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

    # Otherwise, broadcast as plain text
    elif len(message.text.split()) > 1:
        broadcast_text = message.text.split(None, 1)[1]
        exmsg = await message.reply_text("📤 Starting text broadcast...")

        for user in users:
            try:
                await app.send_message(chat_id=int(user), text=broadcast_text)
                done_users += 1
                await asyncio.sleep(0.1)
            except Exception:
                failed_users += 1

    else:
        return await message.reply_text("❌ Reply to a message or add text after /acast.")

    await exmsg.edit_text(
        f"✅ **Broadcast Finished**\n\n"
        f"📤 Sent to: `{done_users}` users\n"
        f"❌ Failed: `{failed_users}` users"
    )

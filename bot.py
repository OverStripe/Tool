import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters

# Configuration
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_username = "songindian16@gmail.com"
email_password = os.getenv("EMAIL_PASSWORD", "gxzk hegw vbks pavr")  # App Password
telegram_bot_token = "7512114938:AAGURK9wQFhr07zfE-vVl9N1tbHvs_KmfZk"
OWNER_ID = 7640331919  # Only the owner can approve users
APPROVED_USERS = {OWNER_ID}  # Store approved users, initially only the owner

# Default Message Template
default_report_message = """
Subject: Report: Channel Selling Illegal Contents

Dear Telegram Support Team,

I'm writing to report a channel that is selling illegal contents on your platform. The channel in question is: {}

This channel is explicitly advertising and promoting the sale of illicit and prohibited items, which is a clear violation of Telegram's terms of service and community guidelines.

I request that you take immediate action to address this issue and ensure that the channel is removed from the platform. The sale and promotion of illegal contents can have serious consequences for individuals and communities.

Please take the following actions:
1. Remove the channel from the platform.
2. Ban the channel's administrators and members from creating new channels or participating in existing ones.

I would appreciate it if you could provide me with an update on the actions taken regarding this report.

Thank you for your attention to this matter.

Sincerely, 
[shivam mishra]
"""

# Conversation states
CHAT_LINK, CUSTOM_MESSAGE = range(2)

# Global variables
chat_link = None
custom_message = None
auto_report = False


# Permission check
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


def is_approved(update: Update):
    return update.effective_user.id in APPROVED_USERS


# Function to send email
def send_email(message_body):
    try:
        recipient_email = "abuse@telegram.com"

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_username, email_password)

            msg = MIMEMultipart()
            msg['From'] = email_username
            msg['To'] = recipient_email
            msg['Subject'] = "Report: Channel Selling Illegal Contents"
            msg.attach(MIMEText(message_body, 'plain'))

            server.sendmail(email_username, recipient_email, msg.as_string())
            return f"✅ Report sent successfully to {recipient_email}!"
    except Exception as e:
        return f"❌ Failed to send report: {e}"


# Command Handlers
async def start(update: Update, context):
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    await update.message.reply_text("Welcome! Please send the chat/group/channel link you want to report.")
    return CHAT_LINK


async def chat_link_handler(update: Update, context):
    global chat_link
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    chat_link = update.message.text
    await update.message.reply_text(
        f"Got the chat link: {chat_link}\nYou can now enter a custom message for the report or type 'default' to use the standard message."
    )
    return CUSTOM_MESSAGE


async def custom_message_handler(update: Update, context):
    global custom_message, auto_report
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    custom_message = update.message.text
    if custom_message.lower() == 'default':
        # Replace placeholder with chat link in the default message
        message_body = default_report_message.format(chat_link)
    else:
        message_body = custom_message.strip()

    result = send_email(message_body)
    await update.message.reply_text(result)

    auto_report = True
    await update.message.reply_text("Auto-reporting every 2 minutes. Type /stop to cancel.")
    while auto_report:
        await asyncio.sleep(120)  # Wait for 2 minutes
        result = send_email(message_body)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)

    return ConversationHandler.END


async def stop(update: Update, context):
    global auto_report
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    auto_report = False
    await update.message.reply_text("Auto-reporting stopped. You can start again by typing /start.")
    return ConversationHandler.END


async def approve(update: Update, context):
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can approve users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Please provide a user ID to approve. Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
        APPROVED_USERS.add(user_id)
        await update.message.reply_text(f"✅ User ID {user_id} has been approved.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")


# Main function to run the bot
def main():
    application = ApplicationBuilder().token(telegram_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHAT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_link_handler)],
            CUSTOM_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, custom_message_handler)],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('approve', approve))

    application.run_polling()


if __name__ == '__main__':
    main()
      

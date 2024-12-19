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
telegram_bot_token = "7512114938:AAGrEGi-EjKKMyzPR6tJyP4BSAjq60HrwW4"
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
CHAT_LINK = range(1)

# Global variables
chat_link = None
auto_report = False


# Permission check
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


def is_approved(update: Update):
    return update.effective_user.id in APPROVED_USERS


# Function to send email
def send_email(chat_link):
    try:
        recipient_email = "abuse@telegram.org"
        message_body = default_report_message.format(chat_link)

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
    global chat_link, auto_report
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    chat_link = update.message.text
    await update.message.reply_text(f"Got the chat link: {chat_link}\nStarting auto-reporting every 2 minutes. Type /stop to cancel.")

    auto_report = True
    while auto_report:
        result = send_email(chat_link)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
        await asyncio.sleep(120)  # Wait for 2 minutes

    return ConversationHandler.END


async def stop(update: Update, context):
    global auto_report
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    if auto_report:
        auto_report = False
        await update.message.reply_text("✅ Auto-reporting has been stopped.")
    else:
        await update.message.reply_text("ℹ️ Auto-reporting is not currently active.")


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
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('approve', approve))

    application.run_polling()


if __name__ == '__main__':
    main()

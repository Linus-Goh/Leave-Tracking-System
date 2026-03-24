from email.mime import message
import sqlite3
import threading

import telebot
from datetime import date

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP, WYearTelegramCalendar

# Thread-local database connection
db_local = threading.local()

def get_db():
    if not hasattr(db_local, 'conn'):
        db_local.conn = sqlite3.connect('unapproved_leave_requests.db')
        db_local.cursor = db_local.conn.cursor()
        # Create the table if it doesn't exist
        db_local.cursor.execute("""CREATE TABLE IF NOT EXISTS leave_requests
                     (user_id INTEGER, 
                     first_name TEXT, 
                     last_name TEXT, 
                     username TEXT, 
                     request_date TEXT,
                     approval_status TEXT)""")
    return db_local.conn, db_local.cursor



admins = [1661394600]  # admin user IDs

class MyStyleCalendar(WYearTelegramCalendar): # Custom calendar class to define button labels and styles (v1.0)
    prev_button = "⬅️"
    next_button = "➡️"
    empty_month_button = ""
    empty_year_button = ""
    empty_day_button = ""
    pass

class AdminRights:
    pass


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.bot = telebot.TeleBot(self.token)

    def start_bot(self): # This method sets up the command handlers and starts the bot's polling loop.
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            self.bot.reply_to(message, "Welcome to the S1 Branch Leave Tracking System.\n\n"
                                "Commands:\n"
                                "/Leave_Request - Apply for Leave\n"
                                "/OFF_Request - Apply for OFF\n"
                                "/User_Info - View your information\n"
                                "/Approved_Leave - Approved leave requests\n"
                                "/Admin_Panel - Access admin functionalities (Admin only)\n"
                                "/Assign_Role - Assign roles (Admin only)\n"
                             )

        @self.bot.message_handler(commands=['OFF_Request']) # Command to start the OFF request process (v1.1)
        def start(m):
            calendar, step = MyStyleCalendar(min_date=date.today()).build()
            self.bot.send_message(
                m.chat.id,
                f"Select {LSTEP[step]}",
                reply_markup=calendar
            )
            
        @self.bot.callback_query_handler(func=MyStyleCalendar.func()) # This handler will be triggered for both OFF_Request and Leave_Request, you may want to differentiate them based on the callback data or use separate handlers.
        def cal(query):
            result, key, step = MyStyleCalendar(min_date=date.today()).process(query.data)
            if not result and key:
                self.bot.edit_message_text(f"Select {LSTEP[step]}",
                                           chat_id=query.message.chat.id,
                                           message_id=query.message.message_id,
                                           reply_markup=key)
            elif result:
                self.bot.edit_message_text(f"You selected {result}",
                                           chat_id=query.message.chat.id,
                                           message_id=query.message.message_id)
                user_id = query.from_user.id
                first_name = query.from_user.first_name
                last_name = query.from_user.last_name
                username = query.from_user.username
                result_input = result.strftime("%Y-%m-%d")
                approval_status = "Pending"
                conn, cursor = get_db()
                cursor.execute("INSERT INTO leave_requests (user_id, first_name, last_name, username, request_date, approval_status) VALUES (?, ?, ?, ?, ?, ?)", (user_id, first_name, last_name, username, result_input, approval_status))
                conn.commit()
                self.bot.send_message(query.message.chat.id, f"OFF request for {result_input} saved and pending approval.")

        @self.bot.message_handler(commands=['Leave_Request']) # Command to start the leave request process (v1.1)
        def start(m):
            calendar, step = MyStyleCalendar(min_date=date.today()).build()
            self.bot.send_message(
                m.chat.id,
                f"Select {LSTEP[step]}",
                reply_markup=calendar
            )
            
        @self.bot.callback_query_handler(func=MyStyleCalendar.func()) # This handler will be triggered for both OFF_Request and Leave_Request, you may want to differentiate them based on the callback data or use separate handlers.
        def cal(query):
            result, key, step = MyStyleCalendar(min_date=date.today()).process(query.data)
            if not result and key:
                self.bot.edit_message_text(f"Select {LSTEP[step]}",
                                           chat_id=query.message.chat.id,
                                           message_id=query.message.message_id,
                                           reply_markup=key)
            elif result:
                self.bot.edit_message_text(f"You selected {result}",
                                           chat_id=query.message.chat.id,
                                           message_id=query.message.message_id)
                user_id = query.from_user.id
                first_name = query.from_user.first_name
                last_name = query.from_user.last_name
                username = query.from_user.username
                result_input = result.strftime("%Y-%m-%d")
                approval_status = "Pending"
                conn, cursor = get_db()
                cursor.execute("INSERT INTO leave_requests (user_id, first_name, last_name, username, request_date, approval_status) VALUES (?, ?, ?, ?, ?, ?)", (user_id, first_name, last_name, username, result_input, approval_status))
                conn.commit()
                self.bot.send_message(query.message.chat.id, f"Leave request for {result_input} saved and pending approval.")

        @self.bot.message_handler(commands=['User_Info']) # Command to display user information (Update v1.1)
        def send_user_info(message):
            user_id = message.from_user.id
            first_name = message.from_user.first_name
            last_name = message.from_user.last_name
            username = message.from_user.username
            AdminRights = "Admin" if user_id in admins else "User"  # Example admin check
            info_message = f"User ID: {user_id}\nFirst Name: {first_name}\nLast Name: {last_name}\nUsername: @{username}\nRole: {AdminRights}"
            self.bot.reply_to(message, info_message)

        @self.bot.message_handler(commands=['Admin_Panel']) # New command for admin panel access (Admin only)
        def admin_panel(message):
            user_id = message.from_user.id
            if user_id in admins:
                self.bot.reply_to(message, "Welcome to the Admin Panel. Here you can manage leave requests and user roles.\n\n"
                                  "Commands:\n"
                                  "/View_Requests - View pending leave requests\n"
                                  "/Approve_Request - Approve a leave request\n"
                                  "/Reject_Request - Reject a leave request")
                # Add admin functionalities here
                
            else:
                self.bot.reply_to(message, "You do not have access to the Admin Panel.")

        @self.bot.message_handler(commands=['Assign_Role']) # New command for role assignment (Admin only)
        def assign_role(message):
            user_id = message.from_user.id
            if user_id in admins:
                self.bot.reply_to(message, "Please provide the user ID and role to assign (e.g., /Assign_Role 123456789 Admin).")
                # Add role assignment functionality here
            else:
                self.bot.reply_to(message, "You do not have permission to assign roles.")

        @self.bot.message_handler(commands=['View_Requests'])
        def view_requests(message):
            if message.from_user.id not in admins:
                return self.bot.reply_to(message, "You do not have access to view requests.")
            conn, cursor = get_db()
            cursor.execute("SELECT * FROM leave_requests WHERE approval_status = 'Pending'")
            requests = cursor.fetchall()
            if not requests:
                return self.bot.reply_to(message, "No pending requests at the moment.")
            for request in requests:
                self.bot.reply_to(message, f"User ID: {request[0]}\nRequest Date: {request[4]}\n"
                                "To Approve or Reject, use the following commands:\n"
                                f"/Approve_Request {request[0]} {request[4]} - Approve the request\n"
                                f"/Reject_Request {request[0]} {request[4]} - Reject the request")

        @self.bot.message_handler(commands=['Approve_Request'])
        def approve_request(message):
            if message.from_user.id not in admins:
                return self.bot.reply_to(message, "You do not have permission to approve requests.")
            try:
                _, user_id_str, request_date, username = message.text.split()
                user_id = int(user_id_str)
                conn, cursor = get_db()
                cursor.execute("UPDATE leave_requests SET approval_status = 'Approved' WHERE user_id = ? AND request_date = ? AND username = ?", (user_id, request_date, username))
                conn.commit()
                self.bot.reply_to(message, f"Leave request for User ID {user_id} on {request_date} has been approved.")
            except Exception:
                self.bot.reply_to(message, "Invalid command format. Please use /Approve_Request <user_id> <request_date> <username>.")

        @self.bot.message_handler(commands=['Reject_Request'])
        def reject_request(message):
            if message.from_user.id not in admins:
                return self.bot.reply_to(message, "You do not have permission to reject requests.")
            try:
                _, user_id, request_date, username = message.text.split()
                conn, cursor = get_db()
                cursor.execute("UPDATE leave_requests SET approval_status = 'Rejected' WHERE user_id = ? AND request_date = ? AND username = ?", (user_id, request_date, username))
                conn.commit()
                self.bot.reply_to(message, f"Leave request for User ID {user_id} on {request_date} has been rejected.")
            except Exception:
                self.bot.reply_to(message, "Invalid command format. Please use /Reject_Request <user_id> <request_date> <username>.")

        
        
        
        print("Bot is polling...")
        self.bot.polling()

if __name__ == "__main__":
    API_TOKEN = '8780277274:AAH6QcOsJBtiLWtaXZne5z23IXZHIJPbg78'
    telegram_bot = TelegramBot(API_TOKEN)
    telegram_bot.start_bot()

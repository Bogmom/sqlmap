import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# تعيين عنوان واجهة API الخاصة بـ SQLMap
SQLMAP_API_URL = 'http://127.0.0.1:8775/'

# تفعيل البوت باستخدام توكن البوت الخاص بك
updater = Updater(token='6573377226:AAEB7Qd7C_5uWQpIJj_hxc4xV_1Ki9QC1_E', use_context=True)
dispatcher = updater.dispatcher

# الدالة التي تقوم ببدء الفحص باستخدام SQLMapAPI
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f'Hi {user.mention_markdown_v2()}! Please send the URL you want to scan.')

# الدالة التي تقوم بمعالجة الرسائل وبدء الفحص
def receive_url(update: Update, context: CallbackContext):
    url = update.message.text

    # إنشاء مهمة جديدة للفحص
    response = requests.get(SQLMAP_API_URL + 'task/new')

    if response.status_code == 200:
        task_id = response.json().get('taskid')
        if task_id:
            # إرسال العنوان إلى مهمة الفحص
            response = requests.post(SQLMAP_API_URL + f'scan/{task_id}/start', json={'url': url})
            if response.status_code == 200:
                update.message.reply_text(f'Starting scan for URL: {url} with Task ID: {task_id}')
            else:
                update.message.reply_text('Failed to start the scan.')
        else:
            update.message.reply_text('Failed to create a new task for scanning.')
    else:
        update.message.reply_text(f'Error: {response.status_code} - {response.text}')

# الدالة التي تقوم بالتحقق من حالة الفحص الحالية وعرض النتائج (إذا توفرت)
def check_status(update: Update, context: CallbackContext):
    task_id = context.user_data.get('task_id')
    
    if task_id:
        response = requests.get(SQLMAP_API_URL + f'scan/{task_id}/status')
        if response.status_code == 200:
            status = response.json().get('status')
            return_code = response.json().get('returncode')
            update.message.reply_text(f'Scan status: {status}, Return code: {return_code}')
            
            # إذا كانت الفحوصات مكتملة وهناك نتائج، يمكنك استرداد البيانات وعرضها
            if status == 'terminated':
                response = requests.get(SQLMAP_API_URL + f'scan/{task_id}/data')
                if response.status_code == 200:
                    data = response.json().get('data')
                    if data:
                        # تحويل قائمة النتائج إلى سلسلة نصية وإرسالها
                        result_text = '\n'.join(data)
                        update.message.reply_text(f'Scan results:\n{result_text}')
        else:
            update.message.reply_text('Failed to check the scan status.')
    else:
        update.message.reply_text('No active scan.')

# الدالة التي تقوم بإيقاف الفحص الحالي (اختياري)
def stop_scan(update: Update, context: CallbackContext):
    task_id = context.user_data.get('task_id')
    
    if task_id:
        response = requests.get(SQLMAP_API_URL + f'scan/{task_id}/stop')
        if response.status_code == 200:
            update.message.reply_text('Scan has been stopped.')
        else:
            update.message.reply_text('Failed to stop the scan.')
    else:
        update.message.reply_text('No active scan.')

# إعداد المراقب لمتابعة الرسائل والأوامر
start_handler = CommandHandler('start', start)
url_handler = MessageHandler(Filters.text & ~Filters.command, receive_url)
status_handler = CommandHandler('status', check_status)
stop_handler = CommandHandler('stop', stop_scan)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(url_handler)
dispatcher.add_handler(status_handler)
dispatcher.add_handler(stop_handler)

# تشغيل البوت
updater.start_polling()

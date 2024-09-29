from Auxiliary.utils import *
from Model import llm_qa


# Custom functions for buttons
def delete_message(_, message_tg):
    Message.botDeleteMessage(message_tg)
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


def clear_next_step_handler(_, message_tg):
    bot.clear_step_handler_by_chat_id(
        message_tg.chat.id)  # просто очищаем step_handler
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


def delete_clear(*args):
    clear_next_step_handler(*args)
    delete_message(*args)
    # ничего не возращаем, чтобы дальше шло как с обычными кнопками


# Custom functions for messages
def ask_question(message_tg):
    clear_next_step_handler(None, message_tg)
    Message.botDeleteMessage(message_tg)

    botMessage = message_question_ask.line(message_tg, deleting_message=False)
    bot.register_next_step_handler(botMessage, answer_question(botMessage))
    return True


def answer_question(botMessage):
    def wrapper(message_tg):
        nonlocal botMessage
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        botMessage = message_answer_processing.line(botMessage)

        # ML
        try:
            question = message_tg.text.replace("_", "-")
            output = llm_qa.respond_question(question)

            answer = html.escape(output)
            answer = answer[:answer.index('СПИСОК ЛИТЕРАТУРЫ:')].strip()

            decryption = {
                'ИСТОЧНИКИ:': '<b>ИСТОЧНИКИ:</b>',
                "_": "-",
            }

            for key, value in decryption.items():
                answer = answer.replace(key, value)

            message = Message(get_text_question_answer(question, answer),
                              ((Button("Корректировать", f"{question}_correct"),),
                               (Button("Отправить", f"{question}_{answer}_send"),),))

            message.line(botMessage)
        except Exception as e:
            print(e)
            message_answer_error.line(botMessage)

    return wrapper


def send_answer(botMessage, data, message_history):
    def wrapper(message_tg):
        nonlocal botMessage, data, message_history
        Message.userSendLogger(message_tg)
        Message.botDeleteMessage(message_tg)

        question, answer = data

        if "<b>ИСТОЧНИКИ:</b>" in answer:
            idx = answer.index("<b>ИСТОЧНИКИ:</b>")
            answer = answer[:idx].strip().replace('\n', '<br>')

        email = message_tg.text
        try:
            html_content = f"""
<html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <p>Уважаемый пользователь,</p>
        <p>Благодарим вас за ваш запрос. Мы получили ваш вопрос:</p>
        <br>
        
        <h3 style="color: #333;">Вопрос:</h3>
        <blockquote style="border-left: 4px solid #ddd; margin-left: 10px; padding-left: 10px;">
            <strong>{question}</strong>
        </blockquote>
        
        <br>
        
        <h3 style="color: #333;">Ответ:</h3>
        <blockquote style="border-left: 4px solid #4CAF50; margin-left: 10px; padding-left: 10px; color: #333;">
            <strong>{answer}</strong>
        </blockquote>
        
        <br>
        <p>С уважением,</p>
        <p>Команда службы поддержки RUTUBE</p>
    </body>
</html>
"""
            botMessage = message_email_processing.line(botMessage)
            send_email(email, "Ответ от службы поддержки RUTUBE", html_content)

            message = Message(f"Сообщение на почту {email} отправлено!", ((button.close,),))
            message.line(botMessage)
        except Exception as _:
            message_email_error.line(botMessage)
        else:
            message = Message(f"{get_text_question_answer(*data)}\n\n"
                              f"<i>Ответ был отправлен на email: <u>{email}</u></i>", ((button.close,),))
            message.line(message_history)

    return wrapper


def correct_answer(botMessage, question, message_history):
    def wrapper(message_tg):
        nonlocal botMessage, question, message_history
        Message.userSendLogger(message_tg)

        Message.botDeleteMessage(message_tg)
        Message.botDeleteMessage(botMessage)

        answer = message_tg.text
        message = Message(get_text_question_answer(question, answer),
                          ((Button("Корректировать", f"{question}_correct"),),
                           (Button("Отправить", f"{question}_{answer}_send"),),))

        message.line(message_history)

    return wrapper


# Buttons
button = Button('', '')

# Question
Button("Задать вопрос", "question")

# Back
Button("🔙 Назад 🔙", "back_to_start")

# Cancel / close
Button("✖️ Отменить ✖️", "delete_clear", func=delete_clear)
Button("✖️ Отменить ✖️", "cancel_question", func=delete_clear)
Button("✖️ Закрыть ✖️", "close", func=delete_message)

# Messages

# Contacts
message_contacts = Message("<b>Создатели:</b>",
                           ((Button("Родионов Семён", "https://t.me/sefixnep", is_link=True),),
                            (Button("Андрей Глинский", "https://t.me/AI_glinsky", is_link=True),
                             Button("Рябов Денис", "https://t.me/denpower", is_link=True),),
                            (Button("Дементьев Эдуард", "https://t.me/SilaVelesa", is_link=True),
                             Button("Рябов Денис", "https://t.me/ozols_s", is_link=True),),
                            (button.close,),
                            ))

# Start
message_start = Message("<b>Здравствуйте, <USERNAME>!</b>\n"
                        "<b>Меня зовут</b> - <code>Рутубик</code>\n\n"
                        "<i>Чтобы скопировать текст ответа, нажмите на его выделенную часть\n"
                        "Учтите, при отправке ответа на Email, источники не прикрепляются!\n"
                        "<b>Чтобы задать вопрос, нажмите на кнопку в меню!</b></i>")

# Ask question
message_question_ask = Message("<b>Напишите пожалуйста вопрос одним сообщением!</b>",
                               ((button.cancel_question,),),
                               button.question,
                               func=ask_question)

# # Processing
message_answer_processing = Message("<b>Готовим ответ...</b>")

# # Error
message_answer_error = Message("<b>Ошибка генерации.</b>", ((button.close,),))

# Correct answer
message_correct_answer = Message("<b>Введите исправленный ответ:</b>", ((button.delete_clear,),))


# Get email
message_email_get = Message("<b>Напишите пожалуйста <u>Email</u> пользователя</b>",
                            ((button.delete_clear,),))

# # Sending
message_email_processing = Message("<b>Отправляем...</b>")

# # Error
message_email_error = Message("<b>Email не найден!</b>",
                              ((button.close,),))

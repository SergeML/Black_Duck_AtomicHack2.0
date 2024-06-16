import config, os, shutil

import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, FSInputFile
from aiogram.filters.command import Command
from lib import lib
import pyodbc



# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.BOT_TOKEN)
# Диспетчер
dp = Dispatcher()
# Данные
data = {}

# Хэндлер на команду старт
@dp.message(Command("start"))
async def start_message(message: Message):
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
        await message.reply(f'Рад знакомству, {message.from_user.full_name}!')
    else:
        await message.reply(f'Рад снова видеть тебя, {message.from_user.full_name}!')

# Хэндлер на режим ученика/специалиста ТК
@dp.message(Command("student"))
async def stud_mode(message: Message):
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    if data[message.from_user.id]['is_student']:
        data[message.from_user.id]['is_student'] = False
        await message.answer(f'''
Вижу, что имею дело со специалистом технического контроля. Я могу помочь тебе заполнять паспорта и журналы.
Для нового отчёта напиши мне в чат сообщение «/start_repo», затем отправляй фотографии или видео для формирования отчёта.
Для завершения отчёта напиши в чат сообщение «/end_repo».
''')
    else:
        data[message.from_user.id]['is_student'] = True
        await message.answer(f'''Всегда рад поделиться своим опытом с учениками и помочь советом.''')

# Хэндлер на команду запуска отчёта
@dp.message(Command("start_repo"))
async def start_repo(message: Message):
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    if not os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id))):
        os.mkdir(os.path.join(os.getcwd(), str(message.from_user.id)))
    if data[message.from_user.id]['is_student']:
        await message.answer('''
        Ученикам не нужно оформлять отчёты самостоятельно. Переключиться из режима ученика можно
отправив сообщение «/student» в чат.''')
    elif (len(os.listdir(os.path.join(os.getcwd(), str(message.from_user.id)))) != 0) or (data[message.from_user.id]['start']):
        await message.answer(f'''
        Вижу, что работа над прошлым отчётом не была завершена.
Прежде чем приступить к новому отчёту, отправь в чат сообщение «/end_repo» для выгрузки предыдущего отчёта.
Или сообщение «/del», чтобы сбросить предыдущий отчёт. После этого мы сможем приступить к новому отчёту.
        ''')
    else:
        data[message.from_user.id]['start'] = True
        await message.answer(f'''
        Я готов приступить к работе над отчётом. Отправляй фото или видео файлы в чат. Чтобы завершить отчёт,
пришли в чат сообщение «/end_repo».
                ''')

# Хэндлер на отправку отчёта
@dp.message(Command("end_repo"))
async def end_repo(message: Message):
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    if not os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id))):
        os.mkdir(os.path.join(os.getcwd(), str(message.from_user.id)))
    if data[message.from_user.id]['is_student']:
        await message.answer('''
        Ученикам не нужно оформлять отчёты самостоятельно. Переключиться из режима ученика можно
отправив сообщение «/student» в чат.''')
    elif data[message.from_user.id]['start'] != True:
        await message.answer(f'''
        Нет активных отчётов для выгрузки. Начать формировать новый отчёт можно, отправив в чат сообщение «/start_repo»
                ''')
    elif (not os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id)))) or (len(os.listdir(os.path.join(os.getcwd(), str(message.from_user.id)))) == 0):
        await message.answer(f'''
        Зугрузи фото или видео, прежде чем закончить отчёт. Сейчас я не вижу швов для отчёта.
        ''')
    else:
        pass # логика формирования отчёта
        try:
            connection = pyodbc.connect(
                f"DSN={config.DSN};UID={config.UID};PWD={config.PWD}"
            )
            INSERT = ("INSERT INTO TABLE (filename, class_id, rel_x, rel_y, width, height) VALUES ('%s', '%s', '%s', "
                      "'%s','%s');")
            cursor = connection.cursor()

            for file_path, values in report.items():
                file_name = os.path.basename(file_path)
                for bboxn, label in zip(values['bboxn'], values['class']):
                    bboxn_ = [str(item) for item in bboxn]
                    label_ = str(int(label))

                    data_ = [file_name] + bboxn_ + [label_]

                    QUERY = INSERT % data_
                    cursor.execute(QUERY)
                    data_ = cursor.fetchall()

            connection.close()
        except:
            await message.answer(f'''
Не удалось подключиться к БД. Проверьте доступность БД и конфигурацию подключения.
                            ''')



# Хэндлер на сброс старого отчёта
@dp.message(Command("del"))
async def del_repo(message: Message):
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    if not data[message.from_user.id]['is_student']:
        if os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id))):
            shutil.rmtree(os.path.join(os.getcwd(), str(message.from_user.id)))
        data[message.from_user.id]['start'] = False
        await message.reply('Старые отчёты сброшены, мы готовы приступить к новым.')
    else:
        await message.answer('''
                Ученикам не нужно оформлять отчёты самостоятельно. Переключиться из режима ученика можно
        отправив сообщение «/student» в чат.''')


# Хэндлер на отправку фото
@dp.message(F.photo)
async def photo_message(message: Message, bot: Bot):
    if not os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id))):
        os.mkdir(os.path.join(os.getcwd(), str(message.from_user.id)))
        count = 0
    else:
        count = len(os.listdir(os.path.join(os.getcwd(), str(message.from_user.id))))
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    await bot.download(message.photo[-1], destination=os.path.join(os.getcwd(), str(message.from_user.id), f'{count}.jpg'))
    await message.reply_photo(
        FSInputFile(os.path.join(os.getcwd(), str(message.from_user.id), f'{count}.jpg'))
    )
    ans = 0
    # Подсказка для студента, возможно, стоит добавить цикл по всем меткам
    if data[message.from_user.id]['is_student']:
        await message.reply(lib[ans])

# Хэндлер на работу с видео
@dp.message(F.photo)
async def video_message(message: Message, bot: Bot):
    if not os.path.isdir(os.path.join(os.getcwd(), str(message.from_user.id))):
        os.mkdir(os.path.join(os.getcwd(), str(message.from_user.id)))
        count = 0
    else:
        count = len(os.listdir(os.path.join(os.getcwd(), str(message.from_user.id))))
    if message.from_user.id not in data.keys():
        data[message.from_user.id] = {'is_student': True,
                                      'start': False,
                                      'end': False,
                                      'frames': []
                                      }
    await bot.download(message.photo[-1], destination=os.path.join(os.getcwd(), str(message.from_user.id), f'{count}.jpg'))
    await message.reply_photo(
        FSInputFile(os.path.join(os.getcwd(), str(message.from_user.id), f'{count}.jpg'))
    )
    ans = 0
    # Подсказка для студента, возможно, стоит добавить цикл по всем меткам
    if data[message.from_user.id]['is_student']:
        await message.reply(lib[ans])

# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

#pipreqs C:\Users\Сергей\PycharmProjects\bot_petrovich
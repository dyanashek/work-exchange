import os
import uuid

import django
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, InputMediaPhoto
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from filer.models import Image, Folder

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'work_exchange.settings')
django.setup()

from config import ADMIN_CHAT_ID, MAX_LEN
from middlewares.change_username import UpdateUsernameMiddleware
from core.models import Worker, Text, Occupation, ObjectPhoto
from states.create_worker import CreateWorker
from keyboards import keyboards
from utils import validate_phone, validate_salary, escape_markdown
from keyboards.callbacks import (OccupationCallbackFactory, PhotoCallbackFactory, 
                                 WorkerNotificationCallbackFactory,
                                 WorkerProfileConfirmationCallbackFactory,
                                )


router = Router()
router.callback_query.middleware(UpdateUsernameMiddleware())
router.message.middleware(UpdateUsernameMiddleware())


@router.message(F.text, CreateWorker.input_name)
async def worker_name(message: Message, state: FSMContext):
    name = await escape_markdown(message.text)

    await state.update_data(name=name)
    await state.set_state(CreateWorker.input_phone)

    reply_text = await sync_to_async(Text.objects.get)(slug='input_phone')
    try:
        await message.answer(
            text=reply_text.rus,
            reply_markup=await keyboards.request_phone_keyboard('rus'),
        )
    except:
        pass


@router.message(F.contact, CreateWorker.input_phone)
async def worker_contact(message: Message, state: FSMContext):
    phone = await validate_phone(phone = message.contact.phone_number)

    if phone:
        await state.update_data(phone=phone)
        await state.set_state(CreateWorker.input_passport_photo)

        reply_text = await sync_to_async(Text.objects.get)(slug='worker_passport_photo')
        try:
            await message.answer(
                text=reply_text.rus,
                reply_markup=ReplyKeyboardRemove(),
            )
        except:
            pass

    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='wrong_phone')
        try:
            await message.reply(text=reply_text.rus)
        except:
            pass


@router.message(F.text, CreateWorker.input_phone)
async def worker_phone(message: Message, state: FSMContext):
    phone = await validate_phone(message.text)

    if phone:
        await state.update_data(phone=phone)
        await state.set_state(CreateWorker.input_passport_photo)

        reply_text = await sync_to_async(Text.objects.get)(slug='worker_passport_photo')
        try:
            await message.answer(
                text=reply_text.rus,
                reply_markup=ReplyKeyboardRemove(),
            )
        except:
            pass

    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='wrong_phone')
        try:
            await message.reply(text=reply_text.rus)
        except:
            pass


@router.message(F.photo, CreateWorker.input_passport_photo)
async def worker_passport_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    try:
        file_info = await message.bot.get_file(photo_id)
    except:
        file_info = None
    
    if file_info:
        await state.update_data(passport_photo_id=photo_id)
        await state.update_data(passport_photo_path=file_info.file_path)
        await state.set_state(CreateWorker.input_occupations)

    reply_text = await sync_to_async(Text.objects.get)(slug='worker_occupations')
    try:
        await message.answer(
            text=reply_text.rus,
            reply_markup=await keyboards.occupations_keyboard('rus', state),
        )
    except:
        pass


@router.callback_query(OccupationCallbackFactory.filter(F.occupation != "confirm"), CreateWorker.input_occupations)
async def worker_change_occupations(callback: CallbackQuery, callback_data: OccupationCallbackFactory, state: FSMContext):
    state_data = await state.get_data()
    curr_occupations = state_data.get('occupations', False)
    if not curr_occupations:
        curr_occupations = []

    if callback_data.occupation in curr_occupations:
        curr_occupations.remove(callback_data.occupation)
    else:
        curr_occupations.append(callback_data.occupation)
    
    await state.update_data(occupations=curr_occupations)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=await keyboards.occupations_keyboard('rus', state),
            )
    except:
        pass


@router.callback_query(OccupationCallbackFactory.filter(F.occupation == "confirm"), CreateWorker.input_occupations)
async def worker_confirm_occupations(callback: CallbackQuery, callback_data: OccupationCallbackFactory, state: FSMContext):
    state_data = await state.get_data()
    occupations = state_data.get('occupations', False)

    if occupations:
        await state.set_state(CreateWorker.input_about)
        reply_text = await sync_to_async(Text.objects.get)(slug='worker_about')
        try:
            await callback.message.edit_text(
                text=reply_text.rus,
                reply_markup=InlineKeyboardBuilder().as_markup(),
            )
        except:
            pass

    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='need_occupations')
        try:
            await callback.bot.answer_callback_query(
                callback_query_id=callback.id,
                text=reply_text.rus,
                show_alert=True,
            )
        except:
            pass


@router.message(F.text, CreateWorker.input_about)
async def worker_about(message: Message, state: FSMContext):
    about = await escape_markdown(message.text)
    about = about[:MAX_LEN]

    await state.update_data(about=about)
    await state.set_state(CreateWorker.input_min_salary)

    reply_text = await sync_to_async(Text.objects.get)(slug='worker_min_salary')
    try:
        await message.answer(
            text=reply_text.rus,
        )
    except:
        pass


@router.message(F.text, CreateWorker.input_min_salary)
async def worker_min_salary(message: Message, state: FSMContext):
    min_salary = await validate_salary(message.text)

    if min_salary:
        await state.update_data(salary=min_salary)
        await state.set_state(CreateWorker.input_objects_photo_confirmation)

        reply_text = await sync_to_async(Text.objects.get)(slug='need_objects_photo')
        try:
            await message.answer(
                text=reply_text.rus,
                reply_markup=await keyboards.object_photo_keyboard(),
            )
        except:
            pass

    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='wrong_min_salary')
        try:
            await message.reply(text=reply_text.rus)
        except:
            pass


@router.callback_query(PhotoCallbackFactory.filter(F.action == "add"), CreateWorker.input_objects_photo_confirmation)
async def worker_add_object_photo(callback: CallbackQuery, callback_data: PhotoCallbackFactory, state: FSMContext):
    await state.set_state(CreateWorker.input_objects_photo)
    state_data = await state.get_data()
    objects_photos = state_data.get('objects_photos', False)
    if not objects_photos:
        objects_photos = []

    if objects_photos:
        reply_text = await sync_to_async(Text.objects.get)(slug='worker_more_objects_photo')
        try:
            await callback.message.edit_text(
                text=f'{reply_text.rus} {len(objects_photos)}',
                reply_markup=InlineKeyboardBuilder().as_markup(),
            )
        except:
            pass
    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='worker_objects_photo')
        try:
            await callback.message.edit_text(
                text=reply_text.rus,
                reply_markup=InlineKeyboardBuilder().as_markup(),
            )
        except:
            pass


@router.message(F.photo, CreateWorker.input_objects_photo)
async def worker_send_object_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    
    state_data = await state.get_data()
    objects_photos = state_data.get('objects_photos', False)
    if not objects_photos:
        objects_photos = []

    objects_photos.append(photo_id)
    await state.update_data(objects_photos=objects_photos)

    if len(objects_photos) < 9:
        await state.set_state(CreateWorker.input_objects_photo_confirmation)

        reply_text = await sync_to_async(Text.objects.get)(slug='need_more_objects_photo')
        try:
            await message.answer(
                text=reply_text.rus,
                reply_markup=await keyboards.object_photo_keyboard(),
            )
        except:
            pass
    else:
        await state.set_state(CreateWorker.input_notifications)

        reply_text = await sync_to_async(Text.objects.get)(slug='worker_notifications')
        try:
            await message.answer(
                text=reply_text.rus,
                reply_markup=await keyboards.worker_notification_keyboard(),
            )
        except:
            pass


@router.callback_query(PhotoCallbackFactory.filter(F.action == "next"), CreateWorker.input_objects_photo_confirmation)
async def worker_next_step(callback: CallbackQuery, callback_data: PhotoCallbackFactory, state: FSMContext):
    await state.set_state(CreateWorker.input_notifications)

    reply_text = await sync_to_async(Text.objects.get)(slug='worker_notifications')
    try:
        await callback.message.edit_text(
            text=reply_text.rus,
            reply_markup=await keyboards.worker_notification_keyboard(),
        )
    except:
        pass


@router.callback_query(WorkerNotificationCallbackFactory.filter(), CreateWorker.input_notifications)
async def worker_notifications(callback: CallbackQuery, callback_data: WorkerNotificationCallbackFactory, state: FSMContext):
    if callback_data.action == 'yes':
        await state.update_data(notifications=True)
        notifications = 'включены'
    else:
        await state.update_data(notifications=False)
        notifications = 'отключены'

    await state.set_state(CreateWorker.confirmation)
    state_data = await state.get_data()

    recheck_text = await sync_to_async(Text.objects.get)(slug='worker_confirmation')
    name_text = await sync_to_async(Text.objects.get)(slug='name')
    phone_text = await sync_to_async(Text.objects.get)(slug='phone')
    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    about_text = await sync_to_async(Text.objects.get)(slug='about')
    notification_text = await sync_to_async(Text.objects.get)(slug='notifications')

    curr_occupations = state_data.get('occupations', False)
    if not curr_occupations:
        curr_occupations = []

    occupations_readable = []
    for curr_occupation in curr_occupations:
        occupation = await sync_to_async(Occupation.objects.filter(slug=curr_occupation).first)()
        if occupation:
            occupations_readable.append(occupation.rus)
    
    occupations_readable = ', '.join(occupations_readable)

    reply_text = f'''
                *{recheck_text.rus}*\
                \n\
                \n*{name_text.rus}* {state_data.get('name', 'не указано')}\
                \n*{phone_text.rus}* {state_data.get('phone', 'не указан')}\
                \n*{occupations_text.rus}* {occupations_readable}\
                \n*{min_salary_text.rus}* {state_data.get('salary', 'не указана')} ₪/час\
                \n*{about_text.rus}* {state_data.get('about', 'не заполнено')}\
                \n*{notification_text.rus}* {notifications}\
                '''

    all_photos = []
    passport_photo = state_data.get('passport_photo_id', False)
    if passport_photo:
        all_photos.append(InputMediaPhoto(media=passport_photo))
    
    objects_photos = state_data.get('objects_photos', False)
    if objects_photos:
        for object_photo in objects_photos:
            all_photos.append(InputMediaPhoto(media=object_photo))

    if all_photos:
        try:
            await callback.message.answer_media_group(media=all_photos)
        except:
            pass
    
    try:
        await callback.message.answer(
            text=reply_text,
            reply_markup=await keyboards.worker_profile_confirmation_keyboard(),
            parse_mode='Markdown',
        )
        await callback.message.delete()
    except:
        pass


@router.callback_query(WorkerProfileConfirmationCallbackFactory.filter(), CreateWorker.confirmation)
async def worker_confirmation(callback: CallbackQuery, callback_data: WorkerProfileConfirmationCallbackFactory, state: FSMContext):
    if callback_data.action == 'retype':
        await state.clear()
        await state.set_state(CreateWorker.input_name)

        reply_text = await sync_to_async(Text.objects.get)(slug='worker_name')
        try:
            await callback.message.edit_text(
                                    text=reply_text.rus,
                                    reply_markup=InlineKeyboardBuilder().as_markup(),
                                    )
        except:
            pass

    elif callback_data.action == 'confirm':
        state_data = await state.get_data()

        name = state_data.get('name')
        phone = state_data.get('phone')
        min_salary = state_data.get('salary')
        about = state_data.get('about')
        passport_photo_id = state_data.get('passport_photo_id')
        passport_photo_path = state_data.get('passport_photo_path')
        notifications = state_data.get('notifications')

        passport_photo = None
        try:
            downloaded_file = await callback.bot.download_file(passport_photo_path)
            folder, _ = await sync_to_async(Folder.objects.get_or_create)(name="Паспорта")
            passport_photo = Image(
                folder=folder,
                original_filename=f"{callback.from_user.id}_{uuid.uuid4()}.{passport_photo_path.split('.')[-1]}",
            )
            await sync_to_async(passport_photo.file.save)(passport_photo.original_filename, downloaded_file)
            await sync_to_async(passport_photo.save)()
        except:
            pass

        curr_occupations = state_data.get('occupations')
        if not curr_occupations:
            curr_occupations = []
        
        occupations_objects = []
        for occupation in curr_occupations:
            occupation = await sync_to_async(Occupation.objects.filter(slug=occupation).first)()
            if occupation:
                occupations_objects.append(occupation)

        objects_photos = state_data.get('objects_photos')
        if not objects_photos:
            objects_photos = []
        
        real_objects_photos = []
        for object_photo in objects_photos:
            object_photo, _ = await sync_to_async(ObjectPhoto.objects.get_or_create)(photo_id=object_photo)
            real_objects_photos.append(object_photo)
        
        worker = await sync_to_async(Worker.objects.filter(tg_id=callback.from_user.id).first)()

        if worker:
            worker.name = name
            worker.phone = phone
            worker.passport_photo = passport_photo
            worker.passport_photo_tg_id = passport_photo_id
            await sync_to_async(worker.occupations.clear)()
            worker.about = about
            worker.min_salary = min_salary
            await sync_to_async(worker.objects_photos.clear)()
            worker.notifications = notifications

        else:
            worker = await sync_to_async(Worker.objects.create)(
                tg_id=callback.from_user.id,
                name=name,
                phone=phone,
                passport_photo=passport_photo,
                passport_photo_tg_id=passport_photo_id,
                about=about,
                min_salary=min_salary,
                notifications=notifications,
            )

        for occupation in occupations_objects:
            await sync_to_async(worker.occupations.add)(occupation)

        for object_photo in real_objects_photos:
            await sync_to_async(worker.objects_photos.add)(object_photo)
        
        await sync_to_async(worker.save)()
        
        readable_approved_status = await sync_to_async(lambda: worker.readable_approved_status)()
        readable_search_status = await sync_to_async(lambda: worker.readable_search_status)()
        readable_notifications_status = await sync_to_async(lambda: worker.readable_notifications_status)()
        readable_occupations = await sync_to_async(lambda: worker.readable_rus_occupations)()

        name_text = await sync_to_async(Text.objects.get)(slug='name')
        phone_text = await sync_to_async(Text.objects.get)(slug='phone')
        occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
        min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
        about_text = await sync_to_async(Text.objects.get)(slug='about')
        notification_text = await sync_to_async(Text.objects.get)(slug='notifications')
        worker_approved = await sync_to_async(Text.objects.get)(slug='worker_approved')
        search_status = await sync_to_async(Text.objects.get)(slug='search_status')
        your_profile = await sync_to_async(Text.objects.get)(slug='your_profile')

        input_media_photos = []
        for object_photo in real_objects_photos:
            input_media_photos.append(InputMediaPhoto(media=object_photo.photo_id))
        
        reply_text = f'''
                *{your_profile.rus}*\
                \n\
                \n*{worker_approved.rus}* {readable_approved_status}\
                \n*{search_status.rus}* {readable_search_status}\
                \n*{notification_text.rus}* {readable_notifications_status}\
                \n\
                \n*{name_text.rus}* {name}\
                \n*{phone_text.rus}* {phone}\
                \n*{occupations_text.rus}* {readable_occupations}\
                \n*{min_salary_text.rus}* {min_salary} ₪/час\
                \n*{about_text.rus}* {about}\
                '''

        if input_media_photos:
            try:
                await callback.message.answer_media_group(media=input_media_photos)
            except:
                pass
        
        try:
            await callback.message.answer(
                text=reply_text,
                reply_markup=await keyboards.worker_profile_keyboard(worker.id),
                parse_mode='Markdown',
            )
        except:
            pass

        admin_reply_text = f'''
                *Заявка на размещение резюме:*\
                \n\
                \n*{name_text.rus}* {name}\
                \n*{phone_text.rus}* {phone}\
                \n*{occupations_text.rus}* {readable_occupations}\
                \n*{min_salary_text.rus}* {min_salary} ₪/час\
                \n*{about_text.rus}* {about}\
                \n*{notification_text.rus}* {readable_notifications_status}\
                '''
        
        input_media_photos.insert(0, InputMediaPhoto(media=worker.passport_photo_tg_id))

        try:
            await callback.bot.send_media_group(
                chat_id=ADMIN_CHAT_ID,
                media=input_media_photos,
            )

            await callback.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_reply_text,
                parse_mode='Markdown',
                reply_markup=await keyboards.admin_worker_keyboard('worker', worker.id),
            )

            await callback.message.delete()
        except:
            pass

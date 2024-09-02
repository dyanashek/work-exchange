import os

import django
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'work_exchange.settings')
django.setup()

from middlewares.change_username import UpdateUsernameMiddleware
from middlewares.worker_active_profile import IsActiveProfileMiddleware
from core.models import Worker, Text
from keyboards import keyboards
from keyboards.callbacks import WorkerMainSectionsCallBackFactory


router = Router()
router.callback_query.middleware(UpdateUsernameMiddleware())
router.callback_query.middleware(IsActiveProfileMiddleware())

profile_router = Router()
profile_router.callback_query.middleware(UpdateUsernameMiddleware())


@profile_router.callback_query(WorkerMainSectionsCallBackFactory.filter(F.destination == 'profile'))
async def handle_profile_menu(callback: CallbackQuery, callback_data: WorkerMainSectionsCallBackFactory, state: FSMContext):
    await state.clear()
    worker = await sync_to_async(Worker.objects.filter(tg_id=callback.from_user.id).first)()
    if worker:
        readable_approved_status = await sync_to_async(lambda: worker.readable_approved_status)()
        readable_search_status = await sync_to_async(lambda: worker.readable_search_status)()
        readable_notifications_status = await sync_to_async(lambda: worker.readable_notifications_status)()
        readable_occupations = await sync_to_async(lambda: worker.readable_rus_occupations)()
        rating = await sync_to_async(lambda: worker.rating_rus)()

        rating_text = await sync_to_async(Text.objects.get)(slug='rating')
        name_text = await sync_to_async(Text.objects.get)(slug='name')
        phone_text = await sync_to_async(Text.objects.get)(slug='phone')
        occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
        min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
        about_text = await sync_to_async(Text.objects.get)(slug='about')
        notification_text = await sync_to_async(Text.objects.get)(slug='notifications')
        worker_approved = await sync_to_async(Text.objects.get)(slug='worker_approved')
        search_status = await sync_to_async(Text.objects.get)(slug='search_status')
        your_profile = await sync_to_async(Text.objects.get)(slug='your_profile')
        

        reply_text = f'''
                *{your_profile.rus}*\
                \n\
                \n*{worker_approved.rus}* {readable_approved_status}\
                \n*{search_status.rus}* {readable_search_status}\
                \n*{notification_text.rus}* {readable_notifications_status}\
                \n\
                \n*{rating_text.rus}* {rating}\
                \n*{name_text.rus}* {worker.name}\
                \n*{phone_text.rus}* {worker.phone}\
                \n*{occupations_text.rus}* {readable_occupations}\
                \n*{min_salary_text.rus}* {worker.min_salary} ₪/час\
                \n*{about_text.rus}* {worker.about}\
                '''

        objects_photos = await sync_to_async(lambda: list(worker.objects_photos.all()))()

        input_media_photos = []
        for object_photo in objects_photos:
            input_media_photos.append(InputMediaPhoto(media=object_photo.photo_id))

        if input_media_photos:
            try:
                await callback.message.answer_media_group(media=input_media_photos)
                await callback.message.answer(
                    text=reply_text,
                    reply_markup=await keyboards.worker_profile_keyboard(worker.id),
                    parse_mode='Markdown',
                )
                await callback.message.delete()
            except:
                pass
        else:
            try:
                await callback.message.edit_text(
                    text=reply_text,
                    reply_markup=await keyboards.worker_profile_keyboard(worker.id),
                    parse_mode='Markdown',
                )
            except:
                pass


@router.callback_query(WorkerMainSectionsCallBackFactory.filter(F.destination == 'jobs'))
async def handle_jobs_menu(callback: CallbackQuery, callback_data: WorkerMainSectionsCallBackFactory, state: FSMContext):
    await state.clear()

    choose_jobs_type = await sync_to_async(Text.objects.get)(slug='choose_jobs_type')

    try:
        await callback.message.edit_text(
            text=choose_jobs_type.rus,
            reply_markup=await keyboards.worker_jobs_menu_keyboard(),
        )
    except:
        pass


@router.callback_query(WorkerMainSectionsCallBackFactory.filter(F.destination == 'proposals'))
async def handle_proposals_menu(callback: CallbackQuery, callback_data: WorkerMainSectionsCallBackFactory, state: FSMContext):
    await state.clear()

    choose_proposals_type = await sync_to_async(Text.objects.get)(slug='choose_proposals_type')

    try:
        await callback.message.edit_text(
            text=choose_proposals_type.rus,
            reply_markup=await keyboards.worker_proposals_menu_keyboard(),
        )
    except:
        pass


@router.callback_query(WorkerMainSectionsCallBackFactory.filter(F.destination == 'reviews'))
async def handle_notifications_controls(callback: CallbackQuery, callback_data: WorkerMainSectionsCallBackFactory, state: FSMContext):
    await state.clear()

    choose_reviews_type = await sync_to_async(Text.objects.get)(slug='choose_reviews_type')

    try:
        await callback.message.edit_text(
            text=choose_reviews_type.rus,
            reply_markup=await keyboards.worker_reviews_menu_keyboard(),
        )
    except:
        pass

import os
import uuid

import django
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'work_exchange.settings')
django.setup()

from config import ADMIN_CHAT_ID, MAX_LEN
from middlewares.change_username import UpdateUsernameMiddleware
from core.models import Employer, Text, Occupation, Job
from states.create_job import CreateJob
from states.pages_navigation import PageNavigation
from keyboards import keyboards
from utils import validate_salary, escape_markdown, translate_to_rus
from keyboards.callbacks import (EmployerControlsCallBackFactory, 
                                OccupationCallbackFactory,
                                )


router = Router()
router.callback_query.middleware(UpdateUsernameMiddleware())
router.message.middleware(UpdateUsernameMiddleware())


@router.callback_query(EmployerControlsCallBackFactory.filter((F.control == 'jobs') & (F.action == 'add')))
async def employer_add_job(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    await state.clear()
    await state.set_state(CreateJob.input_occupations)

    reply_text = await sync_to_async(Text.objects.get)(slug='employer_occupations')
    try:
        await callback.message.edit_text(
            text=f'\u202B{reply_text.heb}',
            reply_markup=await keyboards.occupations_keyboard('heb', state),
        )
    except:
        pass


@router.callback_query(OccupationCallbackFactory.filter(F.occupation != "confirm"), CreateJob.input_occupations)
async def employer_choose_occupations(callback: CallbackQuery, callback_data: OccupationCallbackFactory, state: FSMContext):
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
            reply_markup=await keyboards.occupations_keyboard('heb', state),
            )
    except:
        pass


@router.callback_query(OccupationCallbackFactory.filter(F.occupation == "confirm"), CreateJob.input_occupations)
async def employer_confirm_occupations(callback: CallbackQuery, callback_data: OccupationCallbackFactory, state: FSMContext):
    state_data = await state.get_data()
    occupations = state_data.get('occupations', False)

    if occupations:
        await state.set_state(CreateJob.input_min_salary)
        reply_text = await sync_to_async(Text.objects.get)(slug='employer_min_salary')
        try:
            await callback.message.edit_text(
                text=f'\u202B{reply_text.heb}',
                reply_markup=InlineKeyboardBuilder().as_markup(),
            )
        except:
            pass

    else:
        reply_text = await sync_to_async(Text.objects.get)(slug='need_occupations')
        try:
            await callback.bot.answer_callback_query(
                callback_query_id=callback.id,
                text=f'\u202B{reply_text.heb}',
                show_alert=True,
            )
        except:
            pass


@router.message(F.text, CreateJob.input_min_salary)
async def employer_input_min_salary(message: Message, state: FSMContext):
    min_salary = await validate_salary(message.text)

    if min_salary:
        await state.update_data(salary=min_salary)
        await state.set_state(CreateJob.input_description)

        reply_text = await sync_to_async(Text.objects.get)(slug='job_description')
        try:
            await message.answer(
                text=f'\u202B{reply_text.heb}',
            )
        except:
            pass

    else:
        try:
            reply_text = await sync_to_async(Text.objects.get)(slug='wrong_min_salary')
            await message.reply(text=f'\u202B{reply_text.heb}')
        except:
            pass


@router.message(F.text, CreateJob.input_description)
async def employer_job_description(message: Message, state: FSMContext):
    description = await escape_markdown(message.text)
    description = description[:MAX_LEN]

    await state.update_data(description=description)
    await state.set_state(CreateJob.input_notifications)

    reply_text = await sync_to_async(Text.objects.get)(slug='employer_notifications')
    try:
        await message.answer(
            text=f'\u202B{reply_text.heb}',
            reply_markup=await keyboards.employer_job_notification_keyboard(),
        )
    except:
        pass


@router.callback_query(EmployerControlsCallBackFactory.filter(F.control == "notifications"), CreateJob.input_notifications)
async def employer_job_notifications(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    if callback_data.action == 'yes':
        await state.update_data(notifications=True)
        notifications = 'מופעל'
    else:
        await state.update_data(notifications=False)
        notifications = 'כבוי'

    await state.set_state(CreateJob.input_confirmation)
    state_data = await state.get_data()

    recheck_text = await sync_to_async(Text.objects.get)(slug='employer_confirmation')

    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    salary_hourly = await sync_to_async(Text.objects.get)(slug='salary_hourly')
    
    description_text = await sync_to_async(Text.objects.get)(slug='description')
    notification_text = await sync_to_async(Text.objects.get)(slug='notifications')

    curr_occupations = state_data.get('occupations', False)
    if not curr_occupations:
        curr_occupations = []

    occupations_readable = []
    for curr_occupation in curr_occupations:
        occupation = await sync_to_async(Occupation.objects.filter(slug=curr_occupation).first)()
        if occupation:
            occupations_readable.append(occupation.heb)
    
    occupations_readable = ', '.join(occupations_readable)
    occupations_readable = f'\u202B{occupations_readable}'

    reply_text = f'''\u202B*{recheck_text.heb}*\
                \n\
                \n*{occupations_text.heb}* {occupations_readable}\
                \n*{min_salary_text.heb}* {state_data.get('salary', 'לא מולא')} {salary_hourly.heb}\
                \n*{description_text.heb}* {state_data.get('description', 'לא מולא')}\
                \n*{notification_text.heb}* {notifications}'''

    try:
        await callback.message.edit_text(
            text=reply_text,
            reply_markup=await keyboards.employer_job_confirmation_keyboard(),
            parse_mode='Markdown',
        )
    except:
        pass


@router.callback_query(EmployerControlsCallBackFactory.filter((F.control == "job") & (F.action == 'retype')), CreateJob.input_confirmation)
async def employer_job_retype(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    await state.clear()
    await state.set_state(CreateJob.input_occupations)

    reply_text = await sync_to_async(Text.objects.get)(slug='employer_occupations')
    try:
        await callback.message.edit_text(
            text=f'\u202B{reply_text.heb}',
            reply_markup=await keyboards.occupations_keyboard('heb', state),
        )
    except:
        pass


@router.callback_query(EmployerControlsCallBackFactory.filter((F.control == "job") & (F.action == 'confirm')), CreateJob.input_confirmation)
async def employer_job_confirm(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    employer = await sync_to_async(Employer.objects.filter(tg_id=callback.from_user.id).first)()

    if employer:
        state_data = await state.get_data()

        min_salary = state_data.get('salary')
        description = state_data.get('description')
        notifications = state_data.get('notifications')

        curr_occupations = state_data.get('occupations')
        if not curr_occupations:
            curr_occupations = []
        
        occupations_objects = []
        for occupation in curr_occupations:
            occupation = await sync_to_async(Occupation.objects.filter(slug=occupation).first)()
            if occupation:
                occupations_objects.append(occupation)
        
        job = await sync_to_async(Job.objects.create)(
            employer=employer,
            min_salary=min_salary,
            description=description,
            notifications=notifications,
        )
        
        for occupation in occupations_objects:
            await sync_to_async(job.occupations.add)(occupation)
        
        reply_text = await sync_to_async(Text.objects.get)(slug='job_wait_check')
        try:
            await callback.message.edit_text(
                text=f'\u202B{reply_text.heb}',
                reply_markup=await keyboards.employer_to_main_menu_keyboard(),
            )
        except:
            pass

        occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
        min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
        description_text = await sync_to_async(Text.objects.get)(slug='description')

        readable_occupations = await sync_to_async(lambda: job.readable_rus_occupations)()
        description_rus = await translate_to_rus(description)
        if description_rus:
            description_rus = await escape_markdown(description_rus)

            job.description_rus = description_rus
            await sync_to_async(job.save)()

        admin_reply_text = f'''*Заявка на размещение вакансии:*\
                \n\
                \n*{occupations_text.rus}* {readable_occupations}\
                \n*{min_salary_text.rus}* {min_salary} ₪/час\
                \n*{description_text.rus}* {description_rus}'''

        try:
            await callback.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_reply_text,
                parse_mode='Markdown',
                reply_markup=await keyboards.admin_worker_keyboard('job', job.id),
            )
        except:
            pass

    await state.clear()


@router.callback_query(EmployerControlsCallBackFactory.filter(F.control == "notification"))
async def employer_job_detail_notifications(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    job_id = callback_data.object_id
    job = await sync_to_async(Job.objects.filter(id=job_id).first)()

    if job:
        if callback_data.action == 'enable':
            job.notifications = True
        elif callback_data.action == 'disable':
            job.notifications = False
        
        await sync_to_async(job.save)()

        readable_approve_status = await sync_to_async(lambda: job.readable_approved_status)()
        readable_active_status = await sync_to_async(lambda: job.readable_active_status)()
        readable_notifications_status = await sync_to_async(lambda: job.readable_notifications_heb_status)()
        readable_occupations = await sync_to_async(lambda: job.readable_heb_occupations)()

        job_approved_text = await sync_to_async(Text.objects.get)(slug='job_approved_text')
        job_active_text = await sync_to_async(Text.objects.get)(slug='is_job_active')
        notifications_text = await sync_to_async(Text.objects.get)(slug='notifications')
        
        min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
        salary_hourly_text = await sync_to_async(Text.objects.get)(slug='salary_hourly')
        occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
        description_text = await sync_to_async(Text.objects.get)(slug='description')

        reply_text = f'''\u202B*{job_approved_text.heb}* {readable_approve_status}\
                      \n*{job_active_text.heb}* {readable_active_status}\
                      \n*{notifications_text.heb}* {readable_notifications_status}\
                      \n\
                      \n*{occupations_text.heb}* {readable_occupations}\
                      \n*{min_salary_text.heb}* {job.min_salary} {salary_hourly_text.heb}\
                      \n*{description_text.heb}* {job.description}'''

        try:
            await callback.message.edit_text(
                text=reply_text,
                reply_markup=await keyboards.employer_jobs_edit_keyboard(job.id),
                parse_mode='Markdown',
            )
        except:
            pass


@router.callback_query(EmployerControlsCallBackFactory.filter(F.control == "active"))
async def employer_job_detail_active(callback: CallbackQuery, callback_data: EmployerControlsCallBackFactory, state: FSMContext):
    job_id = callback_data.object_id
    job = await sync_to_async(Job.objects.filter(id=job_id).first)()

    if job:
        if callback_data.action == 'yes':
            if job.is_active is False:
                await state.clear()
                await state.set_state(PageNavigation.page_navigation)
                await state.set_data({'destination': 'jobs-active', 'page': 1})

            job.is_active = True
        elif callback_data.action == 'no':
            if job.is_active is True:
                await state.clear()
                await state.set_state(PageNavigation.page_navigation)
                await state.set_data({'destination': 'jobs-archive', 'page': 1})

            job.is_active = False
        
        await sync_to_async(job.save)()

        readable_approve_status = await sync_to_async(lambda: job.readable_approved_status)()
        readable_active_status = await sync_to_async(lambda: job.readable_active_status)()
        readable_notifications_status = await sync_to_async(lambda: job.readable_notifications_heb_status)()
        readable_occupations = await sync_to_async(lambda: job.readable_heb_occupations)()

        job_approved_text = await sync_to_async(Text.objects.get)(slug='job_approved_text')
        job_active_text = await sync_to_async(Text.objects.get)(slug='is_job_active')
        notifications_text = await sync_to_async(Text.objects.get)(slug='notifications')
        
        min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
        salary_hourly_text = await sync_to_async(Text.objects.get)(slug='salary_hourly')
        occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
        description_text = await sync_to_async(Text.objects.get)(slug='description')

        reply_text = f'''\u202B*{job_approved_text.heb}* {readable_approve_status}\
                      \n*{job_active_text.heb}* {readable_active_status}\
                      \n*{notifications_text.heb}* {readable_notifications_status}\
                      \n\
                      \n*{occupations_text.heb}* {readable_occupations}\
                      \n*{min_salary_text.heb}* {job.min_salary} {salary_hourly_text.heb}\
                      \n*{description_text.heb}* {job.description}'''

        try:
            await callback.message.edit_text(
                text=reply_text,
                reply_markup=await keyboards.employer_jobs_edit_keyboard(job.id),
                parse_mode='Markdown',
            )
        except:
            pass
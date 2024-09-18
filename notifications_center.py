import os
import asyncio

import django
from django.db.models import Q
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'work_exchange.settings')
django.setup()

from config import ADMIN_CHAT_PROPOSALS_ID, ADMIN_CHAT_REVIEWS_ID
from core.models import (Text, Worker, ChannelForEmployers, ChannelForWorkers, 
                         Employer, Job, WorkerCooperationProposal, EmployerCooperationProposal,
                         EmployerReview, WorkerReview)
from keyboards import keyboards
from utils import escape_markdown


async def new_worker_to_employers_channels(bot: Bot, worker: Worker, about_heb: str):
    target_channels = await sync_to_async(lambda: list(ChannelForEmployers.objects.all()))()
    readable_occupations = await sync_to_async(lambda: worker.readable_heb_occupations)()

    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    about_text = await sync_to_async(Text.objects.get)(slug='about')
    new_worker = await sync_to_async(Text.objects.get)(slug='new_worker')
    salary_hourly = await sync_to_async(Text.objects.get)(slug='salary_hourly')
    objects_photos = await sync_to_async(lambda: list(worker.objects_photos.all()))()

    input_media_photos = []
    for object_photo in objects_photos:
        input_media_photos.append(InputMediaPhoto(media=object_photo.photo_id))
    
    reply_text = f'''\u202B*{new_worker.heb}*\
            \n\
            \n*{occupations_text.heb}* {readable_occupations}\
            \n*{min_salary_text.heb}* {worker.min_salary} {salary_hourly.heb}\
            \n*{about_text.heb}* {about_heb}'''

    for channel in target_channels:
        if input_media_photos:
            try:
                await bot.send_media_group(
                    chat_id=channel.tg_id,
                    media=input_media_photos,
                    )
            except:
                pass
        
        try:
            await bot.send_message(
                chat_id=channel.tg_id,
                text=reply_text,
                reply_markup=await keyboards.more_workers_channel_keyboard(),
                parse_mode='Markdown',
            )
        except:
            pass
        await asyncio.sleep(10)


async def new_jobs_to_workers_channels(bot: Bot, job: Job):
    target_channels = await sync_to_async(lambda: list(ChannelForWorkers.objects.all()))()

    readable_occupations = await sync_to_async(lambda: job.readable_rus_occupations)()

    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    description_text = await sync_to_async(Text.objects.get)(slug='description')
    new_job = await sync_to_async(Text.objects.get)(slug='new_job')
    salary_hourly = await sync_to_async(Text.objects.get)(slug='salary_hourly')

    reply_text = f'''
            *{new_job.rus}*\
            \n\
            \n*{occupations_text.rus}* {readable_occupations}\
            \n*{min_salary_text.rus}* {job.min_salary} {salary_hourly.rus}\
            \n*{description_text.rus}* {job.description_rus}\
            '''

    for channel in target_channels:        
        try:
            await bot.send_message(
                chat_id=channel.tg_id,
                text=reply_text,
                reply_markup=await keyboards.more_jobs_channel_keyboard(),
                parse_mode='Markdown',
            )
        except:
            pass
        await asyncio.sleep(10)


async def new_worker_to_employers(bot: Bot, worker: Worker, about_heb: str):
    worker_occupations = await sync_to_async(lambda: list(worker.occupations.all()))()
    employers = await sync_to_async(lambda: list(Employer.objects.filter(
        Q(jobs__occupations__in=worker_occupations) &
        Q(jobs__min_salary__gte=worker.min_salary) &
        Q(jobs__notifications=True) &
        Q(jobs__is_approved=True) &
        Q(jobs__is_active=True)).distinct()))()

    readable_occupations = await sync_to_async(lambda: worker.readable_heb_occupations)()

    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    about_text = await sync_to_async(Text.objects.get)(slug='about')
    new_worker = await sync_to_async(Text.objects.get)(slug='new_worker_interesting')
    salary_hourly = await sync_to_async(Text.objects.get)(slug='salary_hourly')
    objects_photos = await sync_to_async(lambda: list(worker.objects_photos.all()))()

    input_media_photos = []
    for object_photo in objects_photos:
        input_media_photos.append(InputMediaPhoto(media=object_photo.photo_id))
    
    reply_text = f'''\u202B*{new_worker.heb}*\
            \n\
            \n*{occupations_text.heb}* {readable_occupations}\
            \n*{min_salary_text.heb}* {worker.min_salary} {salary_hourly.heb}\
            \n*{about_text.heb}* {about_heb}'''
    
    for employer in employers:
        if input_media_photos:
            try:
                await bot.send_media_group(
                    chat_id=employer.tg_id,
                    media=input_media_photos,
                    )
            except:
                pass
        
        try:
            await bot.send_message(
                chat_id=employer.tg_id,
                text=reply_text,
                reply_markup=await keyboards.employer_worker_detail_redirect('workers-suitable', worker.id),
                parse_mode='Markdown',
            )
        except:
            pass
        await asyncio.sleep(3)


async def new_job_to_workers(bot: Bot, job: Job):
    job_occupations = await sync_to_async(lambda: list(job.occupations.all()))()
    workers = await sync_to_async(lambda: list(Worker.objects.filter(
        Q(occupations__in=job_occupations) &
        Q(min_salary__lte=job.min_salary) &
        Q(notifications=True) &
        Q(is_approved=True) &
        Q(is_searching=True)).distinct()))()

    readable_occupations = await sync_to_async(lambda: job.readable_rus_occupations)()

    occupations_text = await sync_to_async(Text.objects.get)(slug='occupations')
    min_salary_text = await sync_to_async(Text.objects.get)(slug='min_salary')
    description_text = await sync_to_async(Text.objects.get)(slug='description')
    new_job = await sync_to_async(Text.objects.get)(slug='new_job_interesting')
    salary_hourly = await sync_to_async(Text.objects.get)(slug='salary_hourly')

    reply_text = f'''
            *{new_job.rus}*\
            \n\
            \n*{occupations_text.rus}* {readable_occupations}\
            \n*{min_salary_text.rus}* {job.min_salary} {salary_hourly.rus}\
            \n*{description_text.rus}* {job.description_rus}\
            '''
    
    for worker in workers:
        try:
            await bot.send_message(
                chat_id=worker.tg_id,
                text=reply_text,
                reply_markup=await keyboards.worker_job_detail_redirect('suitable-jobs', job.id),
                parse_mode='Markdown',
            )
        except:
            pass
        await asyncio.sleep(3)


async def worker_proposal_accepted(bot: Bot, proposal_id):
    proposal = await sync_to_async(WorkerCooperationProposal.objects.filter(id=proposal_id).first)()
    if proposal:
        worker = await sync_to_async(lambda: proposal.worker)()
        employer = await sync_to_async(lambda: proposal.employer)()
        job = await sync_to_async(lambda: proposal.job)()

        worker_occupations = await sync_to_async(lambda: worker.readable_rus_occupations)()
        job_occupations = await sync_to_async(lambda: job.readable_rus_occupations)()

        worker_username = worker.username
        employer_username = employer.username

        if worker_username:
            worker_username = await escape_markdown(f'@{worker_username}')
        else:
            worker_username = 'не указан'
        
        if employer_username:
            employer_username = await escape_markdown(f'@{employer_username}')
        else:
            employer_username = 'не указан'

        reply_text = f'''*Предложение о сотрудничестве от работника принято работодателем:*\
                    \n\
                    \n*Работник:*\
                    \n*Id tg:* {worker.tg_id}\
                    \n*Имя*: {worker.name}\
                    \n*Ник tg*: {worker_username}\
                    \n*Номер телефона*: {worker.phone}\
                    \n*Профессии*: {worker_occupations}\
                    \n*Ставка от*: {worker.min_salary} ₪/час\
                    \n\
                    \n*Работодатель:*\
                    \n*Id tg:* {employer.tg_id}\
                    \n*Название компании:* {employer.name}\
                    \n*Ник tg*: {employer_username}\
                    \n*Номер телефона*: {employer.phone}\
                    \n\
                    \n*Вакансия:*\
                    \n*Специальности:* {job_occupations}\
                    \n*Ставка от*: {job.min_salary} ₪/час\
                    '''

        another_worker_proposals = await sync_to_async(WorkerCooperationProposal.objects.filter(
            Q(employer=employer) &
            Q(worker=worker) &
            ~Q(id=proposal_id) &
            Q(is_accepted=True) &
            Q(is_proceeded=True)
        ).first)()
        another_employer_proposals = await sync_to_async(EmployerCooperationProposal.objects.filter(
            Q(worker=worker) &
            Q(employer=employer) &
            Q(is_accepted=True) &
            Q(is_proceeded=True)
        ).first)()

        if another_employer_proposals or another_worker_proposals:
            reply_text = '❗️*ПОВТОРНО ПРИНЯТОЕ ПРЕДЛОЖЕНИЕ О СОТРУДНИЧЕСТВЕ МЕЖДУ РАБОТНИКОМ И РАБОТОДАТЕЛЕМ*❗️\n\n' + reply_text

        try:
            await bot.send_message(
                chat_id=ADMIN_CHAT_PROPOSALS_ID,
                text=reply_text,
                parse_mode='Markdown',
            )
            proposal.is_proceeded = True
            await sync_to_async(proposal.save)()
        except:
            pass


async def employer_proposal_accepted(bot: Bot, proposal_id):
    proposal = await sync_to_async(EmployerCooperationProposal.objects.filter(id=proposal_id).first)()
    if proposal:
        worker = await sync_to_async(lambda: proposal.worker)()
        employer = await sync_to_async(lambda: proposal.employer)()

        worker_occupations = await sync_to_async(lambda: worker.readable_rus_occupations)()

        worker_username = worker.username
        employer_username = employer.username

        if worker_username:
            worker_username = await escape_markdown(f'@{worker_username}')
        else:
            worker_username = 'не указан'
        
        if employer_username:
            employer_username = await escape_markdown(f'@{employer_username}')
        else:
            employer_username = 'не указан'

        reply_text = f'''*Предложение о сотрудничестве от работодателя принято работником:*\
                    \n\
                    \n*Работник:*\
                    \n*Id tg:* {worker.tg_id}\
                    \n*Имя:* {worker.name}\
                    \n*Ник tg:* {worker_username}\
                    \n*Номер телефона:* {worker.phone}\
                    \n*Профессии:* {worker_occupations}\
                    \n*Ставка от:* {worker.min_salary} ₪/час\
                    \n\
                    \n*Работодатель:*\
                    \n*Id tg:* {employer.tg_id}\
                    \n*Название компании:* {employer.name}\
                    \n*Ник tg:* {employer_username}\
                    \n*Номер телефона:* {employer.phone}\
                    '''
        
        another_employer_proposals = await sync_to_async(EmployerCooperationProposal.objects.filter(
            Q(employer=employer) &
            Q(worker=worker) &
            ~Q(id=proposal_id) &
            Q(is_accepted=True) &
            Q(is_proceeded=True)
        ).first)()
        another_worker_proposals = await sync_to_async(WorkerCooperationProposal.objects.filter(
            Q(worker=worker) &
            Q(employer=employer) &
            Q(is_accepted=True) &
            Q(is_proceeded=True)
        ).first)()

        if another_employer_proposals or another_worker_proposals:
            reply_text = '❗️*ПОВТОРНО ПРИНЯТОЕ ПРЕДЛОЖЕНИЕ О СОТРУДНИЧЕСТВЕ МЕЖДУ РАБОТНИКОМ И РАБОТОДАТЕЛЕМ*❗️\n\n' + reply_text

        try:
            await bot.send_message(
                chat_id=ADMIN_CHAT_PROPOSALS_ID,
                text=reply_text,
                parse_mode='Markdown',
            )
            proposal.is_proceeded = True
            await sync_to_async(proposal.save)()
        except:
            pass


async def new_employer_review(bot: Bot, review_id):
    review = await sync_to_async(EmployerReview.objects.filter(id=review_id).first)()
    if review:
        worker = await sync_to_async(lambda: review.worker)()
        employer = await sync_to_async(lambda: review.employer)()

        worker_username = worker.username
        employer_username = employer.username

        if worker_username:
            worker_username = await escape_markdown(f'@{worker_username}')
        else:
            worker_username = 'не указан'
        
        if employer_username:
            employer_username = await escape_markdown(f'@{employer_username}')
        else:
            employer_username = 'не указан'
        
        comment = review.review_rus
        if not comment:
            comment = 'не указан'

        reply_text = f'''*Новый отзыв от работодателя на работника:*
                    \n\
                    \n*Работодатель:*\
                    \n*Id tg:* {employer.tg_id}\
                    \n*Ник tg:* {employer_username}\
                    \n*Номер телефона:* {employer.phone}\
                    \n\
                    \n*Работник:*\
                    \n*Id tg:* {worker.tg_id}\
                    \n*Имя:* {worker.name}\
                    \n*Ник tg:* {worker_username}\
                    \n*Номер телефона:* {worker.phone}\
                    \n\
                    \n*Отзыв:*\
                    \n*Оценка:* {review.rate} ⭐️\
                    \n*Комментарий:* {comment}\
                    '''
        
        try:
            await bot.send_message(
                chat_id=ADMIN_CHAT_REVIEWS_ID,
                text=reply_text,
                reply_markup=await keyboards.admin_worker_keyboard('employer-review', review.id),
                parse_mode='Markdown',
            )
        except:
            pass
        

async def new_worker_review(bot: Bot, review_id):
    review = await sync_to_async(WorkerReview.objects.filter(id=review_id).first)()
    if review:
        worker = await sync_to_async(lambda: review.worker)()
        employer = await sync_to_async(lambda: review.employer)()

        worker_username = worker.username
        employer_username = employer.username

        if worker_username:
            worker_username = await escape_markdown(f'@{worker_username}')
        else:
            worker_username = 'не указан'
        
        if employer_username:
            employer_username = await escape_markdown(f'@{employer_username}')
        else:
            employer_username = 'не указан'
        
        comment = review.review
        if not comment:
            comment = 'не указан'

        reply_text = f'''*Новый отзыв от работника на работодателя:*
                    \n\
                    \n*Работник:*\
                    \n*Id tg:* {worker.tg_id}\
                    \n*Имя:* {worker.name}\
                    \n*Ник tg:* {worker_username}\
                    \n*Номер телефона:* {worker.phone}\
                    \n\
                    \n*Работодатель:*\
                    \n*Id tg:* {employer.tg_id}\
                    \n*Ник tg:* {employer_username}\
                    \n*Номер телефона:* {employer.phone}\
                    \n\
                    \n*Отзыв:*\
                    \n*Оценка:* {review.rate} ⭐️\
                    \n*Комментарий:* {comment}\
                    '''
        
        try:
            await bot.send_message(
                chat_id=ADMIN_CHAT_REVIEWS_ID,
                text=reply_text,
                reply_markup=await keyboards.admin_worker_keyboard('worker-review', review.id),
                parse_mode='Markdown',
            )
        except:
            pass
        
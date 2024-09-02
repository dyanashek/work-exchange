from django.core.management import BaseCommand

from core.models import Occupation


class Command(BaseCommand):
    def handle(self, *args, **options):
        buttons = [
            ['concrete', 'Бетонщик', 'עובד בטון'],
            ['armature', 'Арматурщик', 'עובד זיון'],
            ['painter', 'Маляр', 'צַבָּע'],
            ['plaster', 'Штукатурщик', 'טייח'],
            ['tile', 'Плиточник', 'רַצָף'],
            ['plasterboard', 'Гипсокартонщик', 'עובד גבס'],
            ['welding', 'Сварщик', 'רתך'],
            ['electricity', 'Электрик', 'חשמלאי'],
        ]
        for item in buttons:
            slug = item[0]
            text_rus = item[1]
            text_heb = item[2]

            prev_text = Occupation.objects.filter(slug=slug).first()
            if not prev_text:
                my_order = Occupation.objects.count()
                new_text = Occupation(slug=slug, rus=text_rus, heb=text_heb, my_order=my_order)
                new_text.save()
                print(f'Создан текст {slug}: {text_rus}\n{text_heb}')
            else:
                if prev_text.rus != text_rus:
                    prev_text.rus = text_rus
                    prev_text.save()
                    print(f'{slug}: заменен русский текст')

                if prev_text.heb != text_heb:
                    prev_text.heb = text_heb
                    prev_text.save()
                    print(f'{slug}: заменен текст на иврите')
        
        print('done')


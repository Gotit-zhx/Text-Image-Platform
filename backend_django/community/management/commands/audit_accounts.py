from collections import defaultdict
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = '只读检查规范化邮箱冲突；只输出账号ID，不修改或合并任何数据'

    def handle(self, *args, **options):
        emails, invalid, empty = defaultdict(list), [], []
        for user in User.objects.only('id', 'email').iterator():
            email = user.email.strip().lower()
            if not email:
                empty.append(user.id)
                continue
            emails[email].append(user.id)
            try:
                validate_email(email)
            except ValidationError:
                invalid.append(user.id)
        conflicts = [ids for ids in emails.values() if len(ids) > 1]
        self.stdout.write(f'重复邮箱账号组：{conflicts}；非法邮箱账号ID：{invalid}；空邮箱账号ID：{empty}')
        self.stdout.write('只读完成。冲突须人工核实邮箱归属、更换并验证，不自动合并或删除账号。')

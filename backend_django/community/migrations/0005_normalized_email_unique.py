from django.db import migrations


def normalize_accounts(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('community', 'Profile')
    seen, conflicts = {}, []
    for user in User.objects.all().order_by('id').iterator():
        email = user.email.strip().lower()
        if email:
            if email in seen:
                conflicts.extend([seen[email], user.id])
            seen[email] = user.id
    if conflicts:
        raise RuntimeError('规范化邮箱存在冲突，账号ID：' + ','.join(map(str, sorted(set(conflicts)))) + '；请先运行 audit_accounts 并人工核实，迁移未修改任何账号。')
    for user in User.objects.all().iterator():
        User.objects.filter(pk=user.pk).update(email=user.email.strip().lower())
        Profile.objects.get_or_create(user_id=user.pk, defaults={'nickname': user.username})
    schema_editor.execute("CREATE UNIQUE INDEX community_user_normalized_email ON auth_user (LOWER(TRIM(email))) WHERE TRIM(email) <> ''")


def reverse_index(apps, schema_editor):
    schema_editor.execute('DROP INDEX IF EXISTS community_user_normalized_email')


class Migration(migrations.Migration):
    dependencies = [('community', '0004_authattempt_profile_email_verified_profile_nickname_and_more'), ('auth', '0012_alter_user_first_name_max_length')]
    operations = [migrations.RunPython(normalize_accounts, reverse_index)]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_comment_is_hidden_post_moderation_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='postinteraction',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='postinteraction',
            name='is_shared',
            field=models.BooleanField(default=False),
        ),
    ]

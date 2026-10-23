from django.db import migrations


def migrate_notifications(apps,schema_editor):
    Log=apps.get_model('community','AuditLog');Notice=apps.get_model('community','Notification')
    Post=apps.get_model('community','Post');Comment=apps.get_model('community','Comment');User=apps.get_model('auth','User')
    for log in Log.objects.filter(action__in=['post.review','comment.hide','comment.restore','comment.delete','user.roles.update']).iterator():
        recipient_id=None;post_id=None;comment_id=None
        if log.target_type=='post':
            post=Post.objects.filter(pk=log.target_id).first()
            if post:recipient_id=post.author_id;post_id=post.pk
        elif log.target_type=='comment':
            comment=Comment.objects.filter(pk=log.target_id).first()
            if comment:recipient_id=comment.author_id;post_id=comment.post_id;comment_id=comment.pk
        elif log.target_type=='user' and User.objects.filter(pk=log.target_id).exists():recipient_id=log.target_id
        if recipient_id and recipient_id!=log.actor_id:
            item,created=Notice.objects.get_or_create(dedup_key=f'audit:{log.pk}',defaults={'recipient_id':recipient_id,'actor_id':log.actor_id,'event':'post.review' if log.action=='post.review' else 'user.roles' if log.target_type=='user' else 'comment.moderation','target_type':log.target_type,'target_id':log.target_id,'post_id':post_id,'comment_id':comment_id,'snapshot':log.detail})
            if created:Notice.objects.filter(pk=item.pk).update(created_at=log.created_at)


class Migration(migrations.Migration):
    dependencies=[('community','0009_profile_avatar_media')]
    operations=[migrations.RunPython(migrate_notifications,migrations.RunPython.noop)]

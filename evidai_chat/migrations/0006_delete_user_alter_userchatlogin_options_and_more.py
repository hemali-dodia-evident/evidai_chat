# Generated by Django 5.1.2 on 2024-12-06 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evidai_chat', '0005_remove_basicprompts_embedding_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
        migrations.AlterModelOptions(
            name='userchatlogin',
            options={'managed': True},
        ),
        migrations.RemoveField(
            model_name='conversation',
            name='prompt_id',
        ),
        migrations.AddField(
            model_name='conversation',
            name='is_asset',
            field=models.BooleanField(default=False, null=True),
        ),
    ]

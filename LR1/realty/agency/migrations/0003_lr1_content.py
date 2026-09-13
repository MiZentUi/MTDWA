from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agency", "0002_alter_userprofile_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="companyinfo",
            name="audio_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="companyinfo",
            name="certificate_html",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="companyinfo",
            name="document_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="companyinfo",
            name="logo_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="companyinfo",
            name="video_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="newsarticle",
            name="image_path",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.CreateModel(
            name="PartnerCompany",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("website_url", models.URLField()),
                ("logo_path", models.CharField(max_length=255)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Компания-партнёр",
                "verbose_name_plural": "Компании-партнёры",
                "ordering": ("sort_order", "name"),
            },
        ),
    ]

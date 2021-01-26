# Generated by Django 3.1.3 on 2020-12-14 17:57
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("reporting", "0156_auto_20201208_2029")]

    operations = [
        migrations.RunSQL(
            """
            UPDATE reporting_ocpawscostlineitem_daily_summary SET uuid = uuid_generate_v4();
            UPDATE reporting_ocpawscostlineitem_project_daily_summary SET uuid = uuid_generate_v4();
            UPDATE reporting_ocpazurecostlineitem_daily_summary SET uuid = uuid_generate_v4();
            UPDATE reporting_ocpazurecostlineitem_project_daily_summary SET uuid = uuid_generate_v4();
            """
        )
    ]
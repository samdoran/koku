# Generated by Django 3.2.19 on 2023-09-12 14:57
# Generated by Django 3.2.19 on 2023-09-08 12:10
import django.contrib.postgres.indexes
from django.contrib.postgres.fields import JSONField
from django.db import migrations
from django.db import models
from django.db.models.expressions import CombinedExpression
from django.db.models.expressions import F


def copy_field(apps, schema_editor):
    OCPUsageLineItemDailySummary = apps.get_model("reporting", "OCPUsageLineItemDailySummary")
    db_alias = schema_editor.connection.alias

    OCPUsageLineItemDailySummary.objects.using(db_alias).all().update(
        all_labels=CombinedExpression(F("pod_labels"), "||", F("volume_labels"), JSONField())
    )


class Migration(migrations.Migration):

    dependencies = [
        ("reporting", "0307_ingressreports_customer"),
    ]

    operations = [
        migrations.AddField(
            model_name="ocpusagelineitemdailysummary",
            name="all_labels",
            field=models.JSONField(null=True),
        ),
        migrations.AddIndex(
            model_name="ocpusagelineitemdailysummary",
            index=django.contrib.postgres.indexes.GinIndex(fields=["all_labels"], name="all_labels_idx"),
        ),
        migrations.AddIndex(
            model_name="ocpusagelineitemdailysummary",
            index=django.contrib.postgres.indexes.GinIndex(fields=["volume_labels"], name="volume_labels_idx"),
        ),
        migrations.RunPython(copy_field),
    ]

# Generated by Django 3.2.17 on 2023-02-14 09:21

import django.db.models.deletion
import django.utils.timezone
import migrate_sql.operations
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0060_alter_project_storage_size_mb"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectcollaborator",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="projectcollaborator",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.person",
            ),
        ),
        migrations.AddField(
            model_name="projectcollaborator",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="projectcollaborator",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.person",
            ),
        ),
        migrations.AddField(
            model_name="projectcollaborator",
            name="is_incognito",
            field=models.BooleanField(
                default=False,
                help_text="If a collaborator is marked as incognito, they will work as normal, but will not be listed in the UI or accounted in the subscription as active users. Used to add OPENGIS.ch support members to projects.",
            ),
        ),
        migrate_sql.operations.ReverseAlterSQL(
            name="projects_with_roles_vw",
            sql="\n            DROP VIEW projects_with_roles_vw;\n        ",
            reverse_sql='\n            CREATE OR REPLACE VIEW projects_with_roles_vw AS\n\n            WITH project_owner AS (\n                SELECT\n                    1 AS rank,\n                    P1."id" AS "project_id",\n                    P1."owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'project_owner\' AS "origin"\n                FROM\n                    "core_project" P1\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n                WHERE\n                    U1."type" = 1\n            ),\n            organization_owner AS (\n                SELECT\n                    2 AS rank,\n                    P1."id" AS "project_id",\n                    O1."organization_owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_owner\' AS "origin"\n                FROM\n                    "core_organization" O1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = O1."user_ptr_id")\n            ),\n            organization_admin AS (\n                SELECT\n                    3 AS rank,\n                    P1."id" AS "project_id",\n                    OM1."member_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_admin\' AS "origin"\n                FROM\n                    "core_organizationmember" OM1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = OM1."organization_id")\n                WHERE\n                    (\n                        OM1."role" = \'admin\'\n                    )\n            ),\n            project_collaborator AS (\n                SELECT\n                    4 AS rank,\n                    C1."project_id",\n                    C1."collaborator_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'collaborator\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n            ),\n            project_collaborator_team AS (\n                SELECT\n                    5 AS rank,\n                    C1."project_id",\n                    TM1."member_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'team_member\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_user" U1 ON (C1."collaborator_id" = U1."id")\n                    INNER JOIN "core_team" T1 ON (U1."id" = T1."user_ptr_id")\n                    INNER JOIN "core_teammember" TM1 ON (T1."user_ptr_id" = TM1."team_id")\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n            ),\n            public_project AS (\n                SELECT\n                    6 AS rank,\n                    P1."id" AS "project_id",\n                    U1."id" AS "user_id",\n                    \'reader\' AS "name",\n                    \'public\' AS "origin"\n                FROM\n                    "core_project" P1\n                    CROSS JOIN "core_user" U1\n                WHERE\n                    is_public = TRUE\n            )\n            SELECT DISTINCT ON(project_id, user_id)\n                nextval(\'projects_with_roles_vw_seq\') id,\n                R1.*\n            FROM (\n                SELECT * FROM project_owner\n                UNION\n                SELECT * FROM organization_owner\n                UNION\n                SELECT * FROM organization_admin\n                UNION\n                SELECT * FROM project_collaborator\n                UNION\n                SELECT * FROM project_collaborator_team\n                UNION\n                SELECT * FROM public_project\n            ) R1\n            ORDER BY project_id, user_id, rank\n        ',
        ),
        migrate_sql.operations.AlterSQL(
            name="projects_with_roles_vw",
            sql='\n            CREATE OR REPLACE VIEW projects_with_roles_vw AS\n\n            WITH project_owner AS (\n                SELECT\n                    1 AS rank,\n                    P1."id" AS "project_id",\n                    P1."owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    FALSE AS "is_incognito",\n                    \'project_owner\' AS "origin"\n                FROM\n                    "core_project" P1\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n                WHERE\n                    U1."type" = 1\n            ),\n            organization_owner AS (\n                SELECT\n                    2 AS rank,\n                    P1."id" AS "project_id",\n                    O1."organization_owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    FALSE AS "is_incognito",\n                    \'organization_owner\' AS "origin"\n                FROM\n                    "core_organization" O1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = O1."user_ptr_id")\n            ),\n            organization_admin AS (\n                SELECT\n                    3 AS rank,\n                    P1."id" AS "project_id",\n                    OM1."member_id" AS "user_id",\n                    \'admin\' AS "name",\n                    FALSE AS "is_incognito",\n                    \'organization_admin\' AS "origin"\n                FROM\n                    "core_organizationmember" OM1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = OM1."organization_id")\n                WHERE\n                    (\n                        OM1."role" = \'admin\'\n                    )\n            ),\n            project_collaborator AS (\n                SELECT\n                    4 AS rank,\n                    C1."project_id",\n                    C1."collaborator_id" AS "user_id",\n                    C1."role" AS "name",\n                    C1."is_incognito" AS "is_incognito",\n                    \'collaborator\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n            ),\n            project_collaborator_team AS (\n                SELECT\n                    5 AS rank,\n                    C1."project_id",\n                    TM1."member_id" AS "user_id",\n                    C1."role" AS "name",\n                    C1."is_incognito" AS "is_incognito",\n                    \'team_member\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_user" U1 ON (C1."collaborator_id" = U1."id")\n                    INNER JOIN "core_team" T1 ON (U1."id" = T1."user_ptr_id")\n                    INNER JOIN "core_teammember" TM1 ON (T1."user_ptr_id" = TM1."team_id")\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n            ),\n            public_project AS (\n                SELECT\n                    6 AS rank,\n                    P1."id" AS "project_id",\n                    U1."id" AS "user_id",\n                    \'reader\' AS "name",\n                    FALSE AS "is_incognito",\n                    \'public\' AS "origin"\n                FROM\n                    "core_project" P1\n                    CROSS JOIN "core_user" U1\n                WHERE\n                    is_public = TRUE\n            )\n            SELECT DISTINCT ON(project_id, user_id)\n                nextval(\'projects_with_roles_vw_seq\') id,\n                R1.*\n            FROM (\n                SELECT * FROM project_owner\n                UNION\n                SELECT * FROM organization_owner\n                UNION\n                SELECT * FROM organization_admin\n                UNION\n                SELECT * FROM project_collaborator\n                UNION\n                SELECT * FROM project_collaborator_team\n                UNION\n                SELECT * FROM public_project\n            ) R1\n            ORDER BY project_id, user_id, rank\n        ',
            reverse_sql="\n            DROP VIEW projects_with_roles_vw;\n        ",
        ),
    ]

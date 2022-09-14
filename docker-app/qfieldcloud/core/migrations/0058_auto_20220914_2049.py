# Generated by Django 3.2.15 on 2022-09-14 18:49

import django.db.models.deletion
import migrate_sql.operations
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0057_auto_20220701_2140"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Person"), (2, "Organization"), (3, "Team")],
                default=1,
                editable=False,
            ),
        ),
        migrations.RenameField(
            model_name="user",
            old_name="user_type",
            new_name="type",
        ),
        migrations.AlterField(
            model_name="organization",
            name="organization_owner",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type", 1)),
                on_delete=django.db.models.deletion.CASCADE,
                related_name="owner",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="organizationmember",
            name="member",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type", 1)),
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="organizationmember",
            name="organization",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type", 2)),
                on_delete=django.db.models.deletion.CASCADE,
                related_name="members",
                to="core.organization",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="owner",
            field=models.ForeignKey(
                help_text="The project owner can be either you or any of the organization you are member of.",
                limit_choices_to=models.Q(("type__in", [1, 2])),
                on_delete=django.db.models.deletion.CASCADE,
                related_name="projects",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="projectcollaborator",
            name="collaborator",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type__in", [1, 3])),
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="teammember",
            name="member",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type", 1)),
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="teammember",
            name="team",
            field=models.ForeignKey(
                limit_choices_to=models.Q(("type", 3)),
                on_delete=django.db.models.deletion.CASCADE,
                related_name="members",
                to="core.team",
            ),
        ),
        migrate_sql.operations.ReverseAlterSQL(
            name="projects_with_roles_vw",
            sql="\n            DROP VIEW projects_with_roles_vw;\n        ",
            reverse_sql='\n            CREATE OR REPLACE VIEW projects_with_roles_vw AS\n\n            WITH project_owner AS (\n                SELECT\n                    1 AS rank,\n                    P1."id" AS "project_id",\n                    P1."owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'project_owner\' AS "origin"\n                FROM\n                    "core_project" P1\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n                WHERE\n                    U1."user_type" = 1\n            ),\n            organization_owner AS (\n                SELECT\n                    2 AS rank,\n                    P1."id" AS "project_id",\n                    O1."organization_owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_owner\' AS "origin"\n                FROM\n                    "core_organization" O1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = O1."user_ptr_id")\n            ),\n            organization_admin AS (\n                SELECT\n                    3 AS rank,\n                    P1."id" AS "project_id",\n                    OM1."member_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_admin\' AS "origin"\n                FROM\n                    "core_organizationmember" OM1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = OM1."organization_id")\n                WHERE\n                    (\n                        OM1."role" = \'admin\'\n                    )\n            ),\n            project_collaborator AS (\n                SELECT\n                    4 AS rank,\n                    C1."project_id",\n                    C1."collaborator_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'collaborator\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n            ),\n            project_collaborator_team AS (\n                SELECT\n                    5 AS rank,\n                    C1."project_id",\n                    TM1."member_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'team_member\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_user" U1 ON (C1."collaborator_id" = U1."id")\n                    INNER JOIN "core_team" T1 ON (U1."id" = T1."user_ptr_id")\n                    INNER JOIN "core_teammember" TM1 ON (T1."user_ptr_id" = TM1."team_id")\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n            ),\n            public_project AS (\n                SELECT\n                    6 AS rank,\n                    P1."id" AS "project_id",\n                    U1."id" AS "user_id",\n                    \'reader\' AS "name",\n                    \'public\' AS "origin"\n                FROM\n                    "core_project" P1\n                    CROSS JOIN "core_user" U1\n                WHERE\n                    is_public = TRUE\n            )\n            SELECT DISTINCT ON(project_id, user_id)\n                nextval(\'projects_with_roles_vw_seq\') id,\n                R1.*\n            FROM (\n                SELECT * FROM project_owner\n                UNION\n                SELECT * FROM organization_owner\n                UNION\n                SELECT * FROM organization_admin\n                UNION\n                SELECT * FROM project_collaborator\n                UNION\n                SELECT * FROM project_collaborator_team\n                UNION\n                SELECT * FROM public_project\n            ) R1\n            ORDER BY project_id, user_id, rank\n        ',
        ),
        migrate_sql.operations.ReverseAlterSQL(
            name="core_user_email_partial_uniq",
            sql="\n            DROP TRIGGER IF EXISTS core_delta_geom_insert_trigger ON core_delta\n        ",
            reverse_sql="\n            CREATE UNIQUE INDEX IF NOT EXISTS core_user_email_partial_uniq ON core_user (email)\n            WHERE user_type = 1 AND email IS NOT NULL AND email != ''\n        ",
        ),
        migrate_sql.operations.AlterSQL(
            name="core_user_email_partial_uniq",
            sql="\n            CREATE UNIQUE INDEX IF NOT EXISTS core_user_email_partial_uniq ON core_user (email)\n            WHERE type = 1 AND email IS NOT NULL AND email != ''\n        ",
            reverse_sql="\n            DROP INDEX IF EXISTS core_user_email_partial_uniq\n        ",
        ),
        migrate_sql.operations.AlterSQL(
            name="projects_with_roles_vw",
            sql='\n            CREATE OR REPLACE VIEW projects_with_roles_vw AS\n\n            WITH project_owner AS (\n                SELECT\n                    1 AS rank,\n                    P1."id" AS "project_id",\n                    P1."owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'project_owner\' AS "origin"\n                FROM\n                    "core_project" P1\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n                WHERE\n                    U1."type" = 1\n            ),\n            organization_owner AS (\n                SELECT\n                    2 AS rank,\n                    P1."id" AS "project_id",\n                    O1."organization_owner_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_owner\' AS "origin"\n                FROM\n                    "core_organization" O1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = O1."user_ptr_id")\n            ),\n            organization_admin AS (\n                SELECT\n                    3 AS rank,\n                    P1."id" AS "project_id",\n                    OM1."member_id" AS "user_id",\n                    \'admin\' AS "name",\n                    \'organization_admin\' AS "origin"\n                FROM\n                    "core_organizationmember" OM1\n                    INNER JOIN "core_project" P1 ON (P1."owner_id" = OM1."organization_id")\n                WHERE\n                    (\n                        OM1."role" = \'admin\'\n                    )\n            ),\n            project_collaborator AS (\n                SELECT\n                    4 AS rank,\n                    C1."project_id",\n                    C1."collaborator_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'collaborator\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n                    INNER JOIN "core_user" U1 ON (P1."owner_id" = U1."id")\n            ),\n            project_collaborator_team AS (\n                SELECT\n                    5 AS rank,\n                    C1."project_id",\n                    TM1."member_id" AS "user_id",\n                    C1."role" AS "name",\n                    \'team_member\' AS "origin"\n                FROM\n                    "core_projectcollaborator" C1\n                    INNER JOIN "core_user" U1 ON (C1."collaborator_id" = U1."id")\n                    INNER JOIN "core_team" T1 ON (U1."id" = T1."user_ptr_id")\n                    INNER JOIN "core_teammember" TM1 ON (T1."user_ptr_id" = TM1."team_id")\n                    INNER JOIN "core_project" P1 ON (P1."id" = C1."project_id")\n            ),\n            public_project AS (\n                SELECT\n                    6 AS rank,\n                    P1."id" AS "project_id",\n                    U1."id" AS "user_id",\n                    \'reader\' AS "name",\n                    \'public\' AS "origin"\n                FROM\n                    "core_project" P1\n                    CROSS JOIN "core_user" U1\n                WHERE\n                    is_public = TRUE\n            )\n            SELECT DISTINCT ON(project_id, user_id)\n                nextval(\'projects_with_roles_vw_seq\') id,\n                R1.*\n            FROM (\n                SELECT * FROM project_owner\n                UNION\n                SELECT * FROM organization_owner\n                UNION\n                SELECT * FROM organization_admin\n                UNION\n                SELECT * FROM project_collaborator\n                UNION\n                SELECT * FROM project_collaborator_team\n                UNION\n                SELECT * FROM public_project\n            ) R1\n            ORDER BY project_id, user_id, rank\n        ',
            reverse_sql="\n            DROP VIEW projects_with_roles_vw;\n        ",
        ),
    ]

from django.db import migrations, models


DEFAULT_SPECIALTIES = (
    ('general', 'General Medicine',
     'fever, cough, cold, flu, infection, fatigue, general checkup, body pain, nausea, vomiting', 0),
    ('cardiology', 'Cardiology',
     'chest pain, heart, palpitation, blood pressure, hypertension, cardiac, cholesterol', 1),
    ('dermatology', 'Dermatology',
     'rash, skin, itch, acne, eczema, mole, hair loss, wound', 2),
    ('pediatrics', 'Pediatrics',
     'child, baby, infant, toddler, kid, newborn, vaccination', 3),
    ('orthopedics', 'Orthopedics',
     'bone, fracture, joint, knee, back pain, sprain, shoulder, neck pain, sports injury', 4),
    ('gynecology', 'Gynecology',
     'pregnan, period, menstrual, vaginal, pelvic, prenatal, contraception', 5),
    ('neurology', 'Neurology',
     'headache, migraine, seizure, numbness, dizzy, fainting, tremor, memory', 6),
    ('psychiatry', 'Psychiatry',
     'anxiety, depress, panic, insomnia, mood, stress, suicidal, hearing voices', 7),
)


def seed_specialties(apps, schema_editor):
    Specialty = apps.get_model('doctors', 'Specialty')
    for slug, name, keywords, order in DEFAULT_SPECIALTIES:
        Specialty.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'keywords': keywords,
                'order': order,
                'is_active': True,
            },
        )


def backfill_specialty_fk(apps, schema_editor):
    """Point every existing doctor at the matching (or a newly created) specialty."""
    DoctorProfile = apps.get_model('doctors', 'DoctorProfile')
    Specialty = apps.get_model('doctors', 'Specialty')

    for doctor in DoctorProfile.objects.all():
        old_value = doctor.specialization
        specialty = Specialty.objects.filter(slug=old_value).first()
        if specialty is None:
            slug = old_value or 'general'
            specialty, _ = Specialty.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': (old_value or 'General Medicine').replace('-', ' ').title(),
                    'order': 99,
                },
            )
        doctor.specialty = specialty
        doctor.save(update_fields=['specialty'])


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '0002_doctorprofile_doctor_fee_non_negative'),
    ]

    operations = [
        migrations.CreateModel(
            name='Specialty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('keywords', models.TextField(
                    blank=True,
                    help_text='Comma-separated words the Health Assistant uses to route symptoms here.',
                )),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'Specialties',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.RunPython(seed_specialties, migrations.RunPython.noop),
        migrations.AddField(
            model_name='doctorprofile',
            name='specialty',
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name='doctors',
                to='doctors.specialty',
            ),
        ),
        migrations.RunPython(backfill_specialty_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='doctorprofile',
            name='specialization',
        ),
        migrations.RenameField(
            model_name='doctorprofile',
            old_name='specialty',
            new_name='specialization',
        ),
        migrations.AlterField(
            model_name='doctorprofile',
            name='specialization',
            field=models.ForeignKey(
                on_delete=models.deletion.PROTECT,
                related_name='doctors',
                to='doctors.specialty',
            ),
        ),
    ]

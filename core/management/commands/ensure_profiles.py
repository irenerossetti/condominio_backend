# EN: core/management/commands/ensure_profiles.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Asegura que cada usuario en el sistema tenga un perfil asociado.'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        count = 0
        
        if not users_without_profile.exists():
            self.stdout.write(self.style.SUCCESS('¡Excelente! Todos los usuarios ya tienen un perfil.'))
            return

        self.stdout.write(f'Encontrados {users_without_profile.count()} usuarios sin perfil. Creando perfiles ahora...')

        for user in users_without_profile:
            Profile.objects.create(user=user)
            count += 1
            self.stdout.write(f'  - Perfil creado para el usuario: {user.username}')
            
        self.stdout.write(self.style.SUCCESS(f'\nProceso completado. Se crearon {count} perfiles nuevos.'))
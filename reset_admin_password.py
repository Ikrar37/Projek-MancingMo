"""
Script untuk reset password superuser Django
Jalankan dengan: python reset_admin_password.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User

def reset_admin_password():
    print("=" * 50)
    print("RESET PASSWORD ADMIN")
    print("=" * 50)
    
    # Cari semua superuser
    superusers = User.objects.filter(is_superuser=True)
    
    if not superusers.exists():
        print("\n❌ TIDAK ADA SUPERUSER!")
        print("Buat superuser baru dengan: python manage.py createsuperuser")
        return
    
    print(f"\nDitemukan {superusers.count()} superuser:")
    for idx, user in enumerate(superusers, 1):
        print(f"{idx}. Username: {user.username} | Email: {user.email}")
    
    # Pilih user yang ingin direset
    if superusers.count() == 1:
        selected_user = superusers.first()
        print(f"\n✅ Akan reset password untuk: {selected_user.username}")
    else:
        try:
            choice = int(input("\nPilih nomor user yang ingin direset (1-{}): ".format(superusers.count())))
            selected_user = list(superusers)[choice - 1]
        except (ValueError, IndexError):
            print("❌ Pilihan tidak valid!")
            return
    
    # Input password baru
    password = input("\nMasukkan password baru: ")
    confirm_password = input("Konfirmasi password baru: ")
    
    if password != confirm_password:
        print("\n❌ Password tidak cocok!")
        return
    
    if len(password) < 4:
        print("\n❌ Password terlalu pendek! Minimal 4 karakter.")
        return
    
    # Reset password
    selected_user.set_password(password)
    selected_user.save()
    
    print("\n" + "=" * 50)
    print("✅ PASSWORD BERHASIL DIRESET!")
    print("=" * 50)
    print(f"Username: {selected_user.username}")
    print(f"Password baru: {password}")
    print("\nSilakan login ke admin dengan kredensial di atas.")
    print("=" * 50)

if __name__ == "__main__":
    try:
        reset_admin_password()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPastikan Anda menjalankan script ini dari folder project yang sama dengan manage.py")
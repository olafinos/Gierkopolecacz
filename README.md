# Gierkopolecacz

Gierkopolecacz pomaga wybrać gry planszowe, które mogą nam się spodobać.
Robi to na podstawie gier, które wskażemy w aplikacji.

# Setup
Aby uruchomić aplikację potrzebujemy:
 - Python w wersji 3.9
 - Pip w wersji 21
 - PostgreSQL 14

Przed wykonaniem następujących kroków zaleca się, stworzenie osobnego wirtualnego środowiska.
1. Instalacja zależności aplikacji:
   1. `pip install -r requirements.txt`
2. Konfiguracja bazy danych
   1. Z poziomu CLI PostgreSQL
      1. `CREATE DATABASE gierkopolecacz;`
      2. `CREATE USER gierkopolecaczuser WITH PASSWORD 'gierkopol';`
      3. `ALTER ROLE gierkopolecaczuser SET client_encoding TO 'utf8';`
      4. `ALTER ROLE gierkopolecaczuser SET default_transaction_isolation TO 'read committed';`
      5. `ALTER ROLE gierkopolecaczuser SET timezone TO 'UTC';`
      6. `GRANT ALL PRIVILEGES ON DATABASE myproject TO gierkopolecaczuser;`
3. Wykonanie migracji projektu
   1. `python manage.py migrate`
4. Wczytanie gotowych danych
   1. `python manage.py loaddata dump.json`
5. Zebranie plików statycznych
   1. `python manage.py collectstatic`
6. Stworzenie super-użytkownika
   1. `python manage.py createsuperuser`
   2. Podanie swoich danych dla super-użytkownika
7. Dodanie do zmiennych środowiskowych klucza dla skrzynki SMTP
   1. nazwa zmiennej: `EMAIL_HOST_PASSWORD`
   2. wartość zmiennej: `hisexoazuyyyivcq`
8. Uruchomienie aplikacji
   1. `python manage.py runserver`
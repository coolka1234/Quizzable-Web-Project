# Interaktywny Quiz Webowy (Kahoot-like)

## 1. Opis projektu

Projekt polega na stworzeniu webowej aplikacji typu Kahoot, umożliwiającej prowadzenie interaktywnych quizów w czasie rzeczywistym. Funkcje aplikacji:

- Logowanie przez Google (OAuth)
- Tworzenie pokojów gier z pytaniami jednokrotnego wyboru (A, B, C, D)
- Dołączanie do gry poprzez kod
- Udział w quizie i odpowiadanie na pytania w czasie rzeczywistym
- Przechowywanie i udostępnianie baz pytań

### Problemy do rozwiązania:

- Logowanie SSO (OAuth)
- Tworzenie i zarządzanie pokojami
- Obsługa pytań zamkniętych
- Generacja unikalnych kodów
- Komunikacja w czasie rzeczywistym
- Przechowywanie wyników i odpowiedzi

## 2. Zakres funkcjonalny

### Logowanie
- Autoryzacja przez Google (OAuth 2.0)

### Panel użytkownika
- Tworzenie pokoju
- Zarządzanie pytaniami (dodawanie/edycja/usuwanie)
- Przeglądanie innych baz pytań

### Interfejs gracza
- Dołączanie po kodzie
- Odpowiadanie w czasie rzeczywistym
- Wyniki po zakończeniu quizu


## 3. Opis systemu i diagram UML

*(Do uzupełnienia: opis + diagram UML)*


## 4. Architektura aplikacji

**Model-View-Controller (MVC)**

### Uzasadnienie:
- Łatwa rozbudowa o nowe funkcje
- Obsługa interakcji i spójność danych w czasie rzeczywistym
- Porządek i klarowność kodu
- Dobrze udokumentowany wzorzec


## 5. Proponowany stos technologiczny

### Backend
- **Flask** – lekkie API
- **Flask-SocketIO** – real-time
- **Google OAuth** – logowanie

### Frontend
- **HTML + JS** – interfejs użytkownika
- **Tailwind CSS** – stylowanie

### Baza danych
- **PostgreSQL (AWS Aurora)** – skalowalność i niezależność

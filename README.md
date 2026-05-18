# Excercise-Validator
python excercise validator with gui and voice interface that synchronizes and processes video from two cameras
supports 3 excercises : barbell row, bicep curl, lateral raises
body landmark detection implemented using mediapipe library

more info and screens in raport.pdf file

Łódź University of Technology project 2025  
Authors:  
Stanisław Jaworski  
Krzysztof Wojtal  
Kacper Orkwiszewski  
Miłosz Grabowski  

# 📖 Instrukcja użytkowania

# 1. Instalacja wymaganych bibliotek:
pip install -r requirements.txt
wymagane biblioteki:
- numpy
- opencv-python
- mediapipe
- PySide6
- SpeechRecognition
- pyttsx3
- fuzzywuzzy
- python-Levenshtein
- pyaudio
# 2. Uruchomienie programu
Aplikacja wymaga podłączenia dwóch kamer.
Kamera przednia (Frontal): Domyślnie urządzenie o indeksie 0.
Kamera boczna (Lateral): Domyślnie urządzenie o indeksie 1.
Aby zmienić źródła obrazu, należy edytować plik Controller.py (linie 11-12):
```
FRONTAL_CAMERA = 0 # Indeks lub adres kamery przedniej
LATERAL_CAMERA = 1 # Indeks lub adres kamery bocznej
```
Aplikacje należy uruchamiać z poziomu katalogu kod.
Plik uruchamiający program: Controller.py
# 3. Przewodnik po aplikacji
## 3.1 Menu Główne
ROZPOCZNIJ: Przechodzi do trybu treningowego (ekran oczekiwania).
RAPORTY: Biblioteka nagranych i przeanalizowanych ćwiczeń. (Może nie aktualizować się poprawnie)
DOKUMENTACJA: (Nie zaimplementowano)
WYJDŹ: Zamyka aplikację i zatrzymuje procesy kamer.
## 3.2 Zapis raportów i nagrań
czyste nagrania pobrane podczas ćwiczenia zapisywane są w katalogu camera_recordings
raporty wideo utworzone na podstawie wykonywanych powtórzeń zapisywane są w katalogu
video_reports
## 3.3 Wykonywanie ćwiczeń:
Aby przejść do treningu należy wybrać po kolei opcje: rozpocznij -> wybierz ćwiczenie -> (wybór ćwiczenia)
Jeżeli w trakcie treningu system wykrył powtórzenia, po wybraniu opcji „zakończ ćwiczenie”, raporty
zostaną zapisane w katalogu video_reports.
***
Po menu można poruszać się za pomocą komend głosowych, obsługiwane komendy:
"OK Trener" – trener rozpoczyna nasłuch komendy. jeżeli przez jakiś czas komenda nie zostanie wykryta
trener ponownie przejdzie w stan uśpienia.
"Zakończ trening"
"Wybierz ćwiczenie"
 "Uginanie ramion z hantlami"
 "Wznosy bokiem"
 "Wiosłowanie sztangą"
"Zakończ ćwiczenie"
***
## 3.4 Czytanie raportu
Zielone punkty: Wykryte stawy.  
Stawy migające na czerwono: Wykryto niewłaściwy ruch (np. bujanie tułowiem przy uginaniu ramion).  
Czerwone okręgi: Kąt w stawie jest nieprawidłowy (np. ugięte łokcie, zbyt wysoko podniesione ramiona).  
Ikona Zegarka (znacznik tempa w fazie):  
 Tarcza zielona: Tempo ruchu jest idealne.  
 Tarcza pomarańczowa (sugerująca zwolnienie): Wykonujesz ruch zbyt szybko (ew. pauza zbyt krótka).  
 Tarcza niebieska (sugerująca przyspieszenie): Ruch jest zbyt powolny (ew. pauza zbyt długa).  
Oznaczenia Fazy:  
 LIFT: Faza wznoszenia ciężaru (ruch koncentryczny).  
 LOWER: Faza opuszczania (ruch ekscentryczny).  
 PAUSE: Pauza w punkcie szczytowym lub końcowym.  
Statystyki Liczbowe:  
 Liczba w prawym dolnym rogu: Aktualny numer powtórzenia (w danej serii).  
Liczba w prawym górnym rogu: Wskaźnik dopasowania pozy do wzorca w ostatnim kluczowym
momencie ruchu (od 0.00 do 1.00).

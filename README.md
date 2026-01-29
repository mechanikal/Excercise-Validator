# Not-Fortnite-Dances
Repository without any fortnite dances

Installing dependencies:
```
pip install -r requirements.txt
```
## 📖 Instrukcja użytkowania

### 1. Konfiguracja sprzętowa
Aplikacja domyślnie wymaga podłączenia **dwóch kamer** do poprawnej analizy postawy (widok z przodu i z boku).
* **Kamera przednia (Frontal)**: Domyślnie urządzenie o indeksie `0` (np. wbudowana kamera w laptopie lub pierwsza kamera USB).
* **Kamera boczna (Lateral)**: W kodzie zdefiniowana jako strumień sieciowy IP (domyślnie `http://192.168.138.221:8080/video`).

> **Uwaga:** Aby zmienić źródła obrazu, edytuj plik `Controller.py` (linie 11-12):
> ```python
> FRONTAL_CAMERA = 0  # Zmień na indeks swojej kamery lub ścieżkę do pliku wideo
> LATERAL_CAMERA = "twoj_adres_ip_kamery" # Lub indeks innej kamery USB (np. 1)
> ```

### 2. Uruchomienie aplikacji
Upewnij się, że jesteś w głównym katalogu projektu i masz aktywowane środowisko wirtualne. Uruchom plik główny:
```bash
python Controller.py
```

## 🕹️ Przewodnik po aplikacji

### 1. Menu Główne
Po uruchomieniu programu zobaczysz ekran startowy z następującymi opcjami:
* **ROZPOCZNIJ**: Przechodzi do trybu treningowego (ekran oczekiwania).
* **RAPORTY**: Biblioteka nagranych i przeanalizowanych ćwiczeń.
* **DOKUMENTACJA**: (Opcja w budowie)
* **WYJDŹ**: Zamyka aplikację i zatrzymuje procesy kamer.

### 2. Wykonywanie Treningu
Proces treningowy został zaprojektowany tak, aby minimalizować potrzebę interakcji z klawiaturą/myszką (obsługa głosowa).

1.  **Wybór ćwiczenia**: W menu treningowym wybierz jedno z dostępnych ćwiczeń (np. "Wznosy w bok").
2.  **Nagrywanie i Instruktaż**:
    * Po wyborze ćwiczenia, system **automatycznie rozpoczyna nagrywanie** z obu kamer.
    * Na ekranie wyświetlana jest animacja (GIF) pokazująca poprawną technikę ruchu.
    * *Uwaga: W trakcie ćwiczenia nie widzisz podglądu z kamery – skup się na poprawności ruchu. Trener (głos) będzie liczył powtórzenia.*
3.  **Feedback Głosowy**:
    * System na bieżąco analizuje ruch. Usłyszysz licznik powtórzeń (np. "Jeden", "Dwa").
    * Jeśli wykonasz serię, usłyszysz komunikat o numerze serii.
4.  **Zakończenie**:
    * Wybierz przycisk **"ZAKOŃCZ ĆWICZENIE"** lub wydaj komendę głosową.
    * System przejdzie do ekranu "ŁADOWANIE..." – w tym czasie przetwarza nagranie wideo, nanosi analizę biometryczną i zapisuje raport.

### 3. Analiza Wideo (Raporty)
Najważniejszą funkcją programu jest wizualna analiza techniki dostępna w sekcji **RAPORTY**. Po otwarciu nagrania zobaczysz nałożone na obraz elementy diagnostyczne:

#### 📉 Oznaczenia Graficzne
Na ciele ćwiczącego rysowany jest szkielet, który wskazuje błędy w czasie rzeczywistym:
* 🟢 **Zielone punkty**: Staw znajduje się w poprawnej pozycji lub pozostaje nieruchomy (zgodnie z wzorcem).
* 🔴 **Czerwone punkty**:
    * Wykryto niepożądany ruch (np. bujanie tułowiem przy uginaniu ramion).
    * Kąt w stawie jest nieprawidłowy (np. niepełny wyprost).

#### ⏱️ Wskaźniki Tempa i Fazy
W rogu ekranu wyświetlane są ikony i napisy informujące o dynamice ruchu:
* **Ikona Zegarka**:
    * ✅ **Tarcza zielona/normalna**: Tempo ruchu jest idealne.
    * 🐢 **Ikona "Wolniej"** (sugerująca zwolnienie): Wykonujesz ruch zbyt gwałtownie/szybko.
    * 🐇 **Ikona "Szybciej"** (sugerująca przyspieszenie): Ruch jest zbyt powolny.
* **Napisy Fazy**:
    * `LIFT`: Faza wznoszenia ciężaru (ruch koncentryczny).
    * `LOWER`: Faza opuszczania (ruch ekscentryczny).
    * `PAUSE`: Pauza w punkcie szczytowym lub końcowym.

#### 📊 Statystyki Liczbowe
* **Duża liczba na dole**: Aktualny numer powtórzenia.
* **Liczba procentowa (np. 0.85)**: Wskaźnik dopasowania twojej pozy do wzorca idealnego w kluczowym momencie ruchu (1.00 = ideał).

### 4. Wskazówki Techniczne
* **Ustawienie kamer**: Dla najlepszych wyników kamera przednia powinna widzieć całą sylwetkę, a kamera boczna powinna być ustawiona pod kątem 90 stopni do ćwiczącego.
* **Oświetlenie**: Zadbaj o dobre oświetlenie pomieszczenia, aby system `MediaPipe` mógł precyzyjnie wykryć stawy.

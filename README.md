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

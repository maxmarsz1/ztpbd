# 1. Cel i zakres pracy

Głównym celem niniejszego projektu jest przeprowadzenie zaawansowanej, wielobszarowej analizy wydajności operacji bazodanowych na czterech wiodących systemach zarządzania bazami danych (SZBD). Badanie ma na celu wyłonienie różnic i prawidłowości wynikających z odmiennych architektur przechowywania danych – klasycznego podejścia relacyjnego względem systemów nierelacyjnych z rodziny NoSQL.

### Zakres prac analitycznych:
1. Projekt i przygotowanie złożonego środowiska testowego, operującego na wykreowanych 12 tabelach tematycznych ustrukturyzowanych wokół logiki silników gier wideo.
2. Zastosowanie dwóch radykalnie odmiennych modeli danych implementujących spójne struktury encji:
    * **Model Relacyjny** (dla środowisk PostgreSQL oraz MySQL) 
    * **Model Dokumentowy i Klucz-Wartość** (dla środowisk MongoDB i Redis)
3. Implementacja generatora produkującego profile wolumenowe danych: mały (do 10 000 rekordów), średni (rozłożony na poziomie 100 000 rekordów) i duży (sięgający milionów / ~10 000 000 rekordów).
4. Opracowanie i wykonanie zautomatyzowanych testów w klasyfikacji CRUD obejmujących w sumie 24 unikalne scenariusze testowe – badające zachowania narzędzi m.in. przy bulk operacjach, zapytaniach zagnieżdżonych, agregacjach i sortowaniach.
5. Dogłębna analiza mechanizmów silnika na podstawie uzyskanych planów zapytania (komenda EXPLAIN) oraz demonstracja różnic wykonawczych po autorskim zaaplikowaniu specjalistycznych indeksów B-Tree i Hasz na kolumny poszczególnych systemów.
6. Wizualizacja rzetelnych danych pomiarowych ze szczególnym uwzględnieniem obciążeniowych uwarunkowań operacyjnych.

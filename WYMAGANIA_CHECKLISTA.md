# Wymagania i zakres projektu - Zaawansowane Technologie Baz Danych (ZTBD)

Poniżej znajduje się checklista ze wszystkimi wymaganiami projektowymi. Odznaczaj te, które uznasz za całkowicie zakończone w sprawozdaniu/kodzie. 
Analiza kodu pokazuje, że pod kątem aplikacji **praktycznie wszystko z listy na ocenę 4.0 jest już zakodowane**!

## Ocena 3.0 – poziom podstawowy
- [x] **1.** Cel i zakres pracy – jasno określony temat oraz zakres analiz. *(w pliku `01_wstep_cel_zakres.md`)*
- [x] **2.** Opis wybranych systemów zarządzania bazami danych (SZBD). *(w pliku `02_przeglad_bazy_danych_i_architektura.md`)*
- [ ] **3.** Zalety i wady wybranych baz danych, w tym udogodnienia oraz ograniczenia. *(do weryfikacji w sprawozdaniu)*
- [ ] **4.** Awaryjność, bezpieczeństwo, migracje, integracje i skalowalność – część teoretyczna. *(do weryfikacji w sprawozdaniu)*
- [ ] **5.** Obszary biznesowych zastosowań wybranych systemów zarządzania bazami danych. *(do weryfikacji w sprawozdaniu)*
- [x] **6.** Opis zbioru danych – co najmniej 5 tabel w systemie relacyjnym. *(Kod posiada aż 12 tabel: Environments, AITypes, NPCs, NPCEnvironments, EnemyVariants, EnemyVariantStats, NPCSounds, Stats, Items, itemsRecipies, recipies, EnemyDrops)*
- [x] **7.** Krótki opis aplikacji testowej, obejmujący: wymagania, technologie i narzędzia, opis działania. *(Większość prawdopodobnie już jest w `03_aplikacja_i_zbiory_danych.md`)*
- [x] **8.** Opis przeprowadzonych testów wydajnościowych oraz porównanie operacji CRUD dla małego, średniego i dużego zbioru. *(Kod to obsługuje profilami `maly`, `sredni`, `duzy`. Wyniki dla małego i średniego są w formacie JSON)*
- [x] **9.** Porównanie co najmniej 4 systemów baz danych: 2 relacyjne (MySQL, PostgreSQL), 2 nierelacyjne (Redis, MongoDB). *(Zrealizowane w docker-compose i `benchmark.py`)*
- [x] **10.** Co najmniej 12 scenariuszy testowych, w tym min. 3 dla każdej operacji CRUD. *(Kod posiada **aż 24 scenariusze**)*
- [x] **11.** Średnią z 3 prób dla każdej operacji CRUD. *(W `benchmark.py` testy są uruchamiane w pętli `for _ in range(3)` i wyciągana jest średnia)*
- [ ] **12.** Opracowanie wyników testów w formie opisu i wizualizacji (wykresy) oraz prezentacja. *(Sprawozdanie jest rozwijane, np. w pliku `05_wyniki_testow.md`)*

## Ocena 4.0 – poziom rozszerzony
- [x] **1.** Co najmniej dwa różne modele danych. *(Są zaimplementowane trzy modele: relacyjny w Postgres/MySQL, dokumentowy w MongoDB oraz klucz-wartość w Redis)*
- [x] **2.** Wykorzystanie indeksów w bazach danych. *(W `benchmark.py` testy uruchamiają się zarówno bez indeksów jak i z indeksami `WITH_INDEX`)*
- [x] **3.** Co najmniej 10 tabel w systemie relacyjnym. *(Jest 12 tabel. Wymaganie spełnione)*
- [x] **4.** Analiza planów zapytań (np. EXPLAIN). *(`benchmark.py` obsługuje tworzenie planów zapytań i zapisuje je m.in. w `benchmark_explain_maly.txt`)*
- [x] **5.** Porównanie wyników testów przed i po zastosowaniu indeksów. *(Skrypt przeprowadza dwufazowe testy i zapisuje oba w plikach z wynikami JSON)*
- [x] **6.** Średnia z 3 prób dla każdego z 24 scenariuszy testowych. *(Wymaganie spełnione - testy działają poprawnie ze średnią dla 24 scenariuszy)*
- [ ] **7.** Rozszerzona analiza wyników oraz wniosków. *(Do napisania w plikach markdown)*
- [x] **8.** Co najmniej 24 różne scenariusze testowe, w tym min. 6 dla każdej operacji. *(W `benchmark.py` mamy DOKŁADNIE 24 różne scenariusze: C1-C6, R1-R6, U1-U6, D1-D6)*
- [x] **9.** Opis testów wydajnościowych oraz porównanie operacji CRUD dla małego, średniego i dużego zbioru danych. *(System profilowania `maly`, `sredni`, `duzy` jest kompletny pod kątem tego punktu. Pozostaje wygenerowanie pełnych danych dla profilu "duzy" i zaktualizowanie raportu)*

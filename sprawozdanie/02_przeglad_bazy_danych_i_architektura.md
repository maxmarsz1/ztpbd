# 2. Wybrane Systemy Zarządzania Bazami Danych (SZBD)

Do weryfikacji testowej celów badawczych tego projektu posłużył zdefiniowany koszyk czterech kluczowych technologii rynkowych umieszczonych w systemie kontenerowym Docker.  

### 2.1 Pula systemów Relacyjnych (RDBMS)

#### PostgreSQL (wersja 17)
Najpopularniejsza, otwartoźródłowa obiektowo-relacyjna baza danych uchodząca za wyznacznik rynkowego bezpieczeństwa. 
* **Zalety:** Ogromne możliwości tworzenia rozszerzeń, fenomenalne wsparcie dla transakcyjności (w pełni ACID), zdolność indeksowania wielowymiarowego (GIST/GIN), idealna dla hurtowni danych i zapytań złożonych z wielu JOIN.
* **Wady:** Wymaga stosunkowo dużych zasobów konfiguracyjnych i odczuwalnie zużywa więcej pamięci przy prostych zapytaniach od strony architektury procesów dla każdego zapytania. Spowolniałe zapisy w przypadku bardzo ciężkich obciążeń transakcyjnych "Write".

#### MySQL
Powszechnie wdrażany na świecie system DBMS ukierunkowany na odczyt. Architektura bazuje na wątkach działających w ramach jednego procesu w przeciwieństwie do tworzenia sub-procesów (jak w PG). Podstawowym nowoczesnym silnikiem jest w nim `InnoDB`.
* **Zalety:** Doskonała wydajność operacji read-owych, popularność zapewniająca rozpiętą integrację, stosunkowo prosta optymalizacja na sprzęt.
* **Wady:** Nie jest tak rygorystyczny przy sprawdzaniu zgodności typów danych, mniejsze pole obsługi operacji Full/Left Outer-Join i analiz okienkowych w odniesieniu do bogactw PostgreSQL.

### 2.2 Pula systemów Nierelacyjnych (NoSQL)

#### MongoDB
Nierelacyjny, wieloplatformowy system DBMS oparty na modelu dokumentowym (`BSON`). Posiada formę pozbawioną z góry narzuconych schematów (schemaless), gdzie relacje budowane są w oparciu o modelowanie i agregację.
* **Zalety:** Naturalna strukturyzacja obieków mapująca kod aplikacji z danymi. Ekstremalnie rozbudowana skalowalność pozioma w modelu Shardingu i replikach (Replica Sets). Olbrzymia przydatność do prototypowania struktur w czasie rzeczywistym.
* **Wady:** Nie wspiera efektywnie deklaratywnych join-ów rodem z baz relacyjnych, powielenia i dublowanie dokumentów mogą pochłaniać bezwzględne gigabajty dodatkowej przestrzeni pamięci na dużych wolumenach.

#### Redis (Remote Dictionary Server)
Platforma typowana jako baza "Klucz-Wartość" operująca wyłącznie lub docelowo całkowicie w głównej pamięci RAM serwera - zachowując gigantyczną przepustowość odczytów i zapisów, używana z założenia jako bufor / wdrożenie cachownia.
* **Zalety:** Ekstremalnie niskie opóźnienia i brak narzutu I/O operowanego dysku (microseconds). Uproszczenie modeli algorytmicznych przez wprowadzane bezpośrednio proste struktury list/setów prosto z pamięci.
* **Wady:** Architektura jednoobrotowa – limitowana do wielkości uwarunkowanego RAM u gospodarza (częsta bolączka przy zapychaniu systemów). Konieczność wybiórczej utraty małych interwałów danych w ramach modeli utrwalających dysku.

## 3. Aspekty Teoretyczne: Bezpieczeństwo i Architektura

* **Awaryjność:** MongoDB dysponuje naturalnymi Replika Setami z wbudowaną dążnością do minimalizacji przerw. Systemy relacyjne wykorzystują podejście Primary-Standby na opóźnieniowych logach, podczas gdy Redis bazuje na Snapshotach (RDB) lub rzadziej zapisach AOF, przez co uszkodzenie RAM często powoduje pewne widoczne dla biznesu luki pamięciowe.
* **Migracje:** PostgreSQL chwali zjawiskowo dojrzały ekosystem pod aplikacje migracyjne (Alembic/Flyway). MongoDB nie wymaga stricte narzucania schematu, więc migracja zazwyczaj odbywa się przy kodzie aplikacji adaptującym nowsze zasoby.
* **Skalowalność:** RDBMS (PostgreSQL, MySQL) są głównie zaprojektowane do pionowej skalowalności na drodze udoskonaleń sprzętu maszyny (Vertical). Opcje shardingowe rodzą problemy klastrowe. MongoDB i Redis naturalnie wspierają Partycjonowanie - ich domeną jest "Skalowalność Skrośnia/Horyzontalna", pozwalająca dorzucać serwery obok poprzednich w klastrze dla proporcjonalnych wzrostów mocy odczytu.
* **Obszary biznesowych zastosowań:** Bazy relacyjne doskonale pełnią kluczowe warstwy logiczne na potrzeby systemów ubezpieczeniowych, giełd (rozliczenia), i ERP, w których absolutnie każdorazowo transakcja musi przebiegać w normie ACID. Baza Dokumentowa - w e-commerce w katalogach produktowych. Baza In-Memory – w systemach IoT, cache i przyśpieszania renderowania widoków webowych.

# Wnioski z Analizy Wydajności Baz Danych w Środowisku Testowym (10 mln rekordów)

W trakcie testowania, profilowania oraz optymalizowania skryptów benchmarkowych dla PostgreSQL, MySQL, Redis oraz MongoDB na zbiorze danych przekraczającym 10 milionów wierszy, wyciągnięto następujące kluczowe wnioski dotyczące architektury silników, sterowników i specyfiki operacji I/O.

## 1. PostgreSQL Hash Join vs MongoDB Aggregation Pipeline w zapytaniach złożonych (N-M)
Wykres **R6_ComplexQuery**, będący zaawansowanym zapytaniem grupującym połączonym z dwoma potężnymi `JOIN`ami na tabelach liczących po 620 tysięcy wierszy, doskonale zarysował granicę zastosowań relacyjnych i nierelacyjnych baz danych:
* **PostgreSQL (~0.24 sekundy):** Dzięki swojemu zaawansowanemu optymalizatorowi analitycznemu (Query Planner), silnik zdecydował się na użycie algorytmu `Hash Join`. Baza zbudowała zoptymalizowaną strukturę pamięciową (Hash Table) w C, co pozwoliło na wykonanie łączenia w niesamowicie krótkim czasie.
* **MongoDB (~14 sekund):** MongoDB jako nierelacyjna, dokumentowa baza danych bardzo źle radzi sobie z naturalnymi złączeniami. Operatory `$lookup` oraz `$unwind` w potoku agregacji wymuszają budowanie, zagnieżdżanie i "rozpakowywanie" gigantycznych struktur BSON obiekt po obiekcie w pamięci serwera.
* **Wniosek:** Skomplikowane zapytania analityczne na setkach tysięcy połączonych rekordów powinny być domeną relacyjnego SQL. Symulowanie skomplikowanych łączeń (JOIN) za pomocą potoku agregacji w bazach NoSQL to antywzorzec wydajnościowy.

## 2. Ukryty narzut sieciowy i narzut sterownika aplikacji (Bulk Insert)
Początkowe wyniki wskazywały, że wstawianie 1000 rekordów naraz (`C3_BulkInsert1000`) trwa w MySQL ponad 170 ms, podczas gdy Postgres robi to w 10 ms. Optymalizacja skryptu dowiodła, że problem nie leżał w bazie danych, lecz w Pythonie:
* **Postgres (`psycopg2.extras`):** Sterownik przed wysłaniem polecenia formował jedno gigantyczne zapytanie z wieloma krotkami `VALUES (1,2), (3,4)...` wysyłając do bazy tylko jedną paczkę sieciową.
* **MySQL (`mysql-connector-python`):** Domyślna metoda `.executemany()` w naiwny sposób iteruje przez zapytania w pętli, wysyłając 1000 osobnych wywołań przez gniazdo TCP, co sumuje gigantyczny narzut komunikacji wewnątrzsieciowej.
* **Wniosek:** Budowa zapytań masowych z poziomu kodu aplikacji (tzw. String Compilation), która uderza do bazy danych jedną dużą paczką TCP, całkowicie ujednoliciła wydajność (redukując czas z 0.17s do 0.01s). Wąskim gardłem w benchmarkowaniu i rzeczywistych aplikacjach bywa często nie silnik DB, lecz narzut sieci i implementacja sterownika językowego.

## 3. Zjawisko "Cache Eviction" i opóźnień I/O po tworzeniu indeksów w Mongo
Na wykresach fazy drugiej (z indeksami) prosta operacja wstawienia jednego rekordu (`C1_SingleInsert`) tuż po uruchomieniu komend `CREATE INDEX` była w Mongo 40-krotnie wolniejsza (z 1 ms skakała na ok. 40 ms - a w ekstremalnych bez buforowania nawet do 160 ms). 
* Różnica ta wynikała ze stanu zwanego "*Dirty Cache / High I/O Aftermath*". Generowanie indeksów dla 10 milionów wierszy pochłania 100% obciążenia dysku oraz RAM.
* O ile bazy relacyjne (Postgres, MySQL) twardo blokują zwrot komendy aż do w 100% czystego zamknięcia zrzutu pamięci, o tyle silnik WiredTiger w MongoDB zwraca sukces do aplikacji szybciej, wykonując "sprzątanie" wątków w tle (Eviction Threads, punkty kontrolne).
## 5. Brakujące rekordy i pełne skanowanie tabeli (D4_DeleteSubquery)
W teście `D4` usuwaliśmy wpisy z `NPCEnvironments`, gdzie `typeID = 999`. Taki typ (999) w naszej generowanej bazie nie istnieje (mamy tylko 62 typy AI).
* **Faza bez indeksów:** Skoro rekord nie istnieje, baza musi o tym wiedzieć. Aby z całą pewnością stwierdzić "Znalazłem 0 wierszy", Postgres, MySQL i Mongo musiały brutalnie przeskanować ("Sequential Scan") całe 620 tysięcy rekordów w tabeli `NPCs` do samego końca pliku! Dla Postgresa zajęło to 0.029s, ale dla MySQL i Mongo aż ~0.24s. Zwykłe puste zapytanie wymusiło ciężką pracę dyskową.
* **Faza z indeksami:** Czasy spadły w każdym silniku do ok. **0.0009s**. Optymalizator sprawdził w B-Tree, że liść dla `typeID=999` nie istnieje i zakończył zapytanie w ułamek milisekundy bez dotykania ani jednej strony z danymi.
* **Wniosek:** Indeksy są absolutnie krytyczne nie tylko do szybkiego znajdowania danych, ale przede wszystkim do natychmiastowego ucinania wyszukiwań, gdy szukane wartości w bazie nie występują.

## 6. Szybkość czyszczenia tabel (TRUNCATE) i narzut DDL w MySQL (D6_DeleteAllTruncate)
W teście `D6` opróżnialiśmy całą tabelę `recipies`. Użyto tu komendy `TRUNCATE` (lub `delete_many({})` w Mongo).
* Zarówno **Postgres (0.0019s)** jak i **Mongo (0.0013s)** rozpoznały komendę usunięcia wszystkiego i zamiast iterować po wierszach i usuwać je pojedynczo, po prostu usunęły i na nowo utworzyły pusty plik z danymi na twardym dysku. Jest to najszybsza możliwa operacja na plikach, trwająca ledwie 1 milisekundę.
* Zaskoczeniem może być **MySQL (0.045s)**, który był aż 40-krotnie wolniejszy od reszty. Mogłoby się wydawać, że to wina weryfikacji kluczy obcych lub narzutu sieci. Jednak pomiary bezpośrednie pokazały, że to sam silnik **InnoDB** tyle potrzebuje! W MySQL komenda `TRUNCATE TABLE` działa jako ekstremalnie "ciężka" instrukcja DDL: zdejmuje ekskluzywną blokadę metadanych, całkowicie usuwa tabelę ze słownika bazy danych (Data Dictionary), niszczy pliki `.ibd` i tworzy struktury systemowe od absolutnego zera.
* **Wniosek:** Postgres potrafi "odciąć" stary plik i podpiąć nowy w pamięci niemal bezboleśnie (2 ms). Z kolei archaiczna budowa metadanych w MySQL InnoDB sprawia, że nawet najprostsze operacje DDL takie jak `TRUNCATE` wiążą się z twardym opóźnieniem dyskowym rzędu 40-50 milisekund na usunięcie i rejestrację nowej tabeli w systemie plików serwera.

## 7. Koszt pełnego skanowania tabeli i urok autogeneracji indeksów (U5_UpdateWithJoinSubq)
Zapytanie `U5` miało na celu zaktualizowanie tabeli `Items` w oparciu o listę identyfikatorów wyciągniętych z tabeli `Stats` (`WHERE statsID IN ...`). W fazie bez indeksów ujawniło ono fundamentalne różnice między silnikami:
* W pierwszej fazie (brak indeksów) zapytanie w **MySQL** trwało zaledwie **0.0018s**, w **PostgreSQL 0.17s**, a w **MongoDB aż 1.1s**!
* **Skąd przewaga MySQL?** W kodzie zdefiniowaliśmy, że pole `statsID` to klucz obcy (`FOREIGN KEY`). Architektura MySQL z automatu, nie pytając programisty o zdanie, tworzy dla kluczy obcych niewidzialny indeks B-Tree. Dzięki temu MySQL "oszukiwał" w pierwszej fazie, nie musząc skanować wszystkich przedmiotów, lecz od razu znajdując je w ułamku milisekundy.
* **Z kolei PostgreSQL i MongoDB** to bazy, w których programista musi jawnie utworzyć indeks na każde pole (nawet klucz obcy). Brak takiego indeksu zmusza bazę do brutalnego przeszukania całej kolekcji z elementami (ok. 1.55 miliona obiektów w `Items`), co obnaża różnicę w samej optymalizacji skanowania:
    * **PostgreSQL (0.17s):** Niezwykle zoptymalizowany algorytm *Sequential Scan* napisany w C potrafi przebiec przez półtora miliona rzędów na dysku w mniej niż jedną piątą sekundy.
    * **MongoDB (1.1s):** Pełne skanowanie kolekcji (*COLLSCAN*) w bazie NoSQL zmusza silnik do załadowania 1.55 miliona ciężkich dokumentów BSON z twardego dysku do pamięci RAM, tylko po to by sprawdzić jedno pole `statsID` w każdym z nich. Deserializacja tak ogromnej masy danych JSON/BSON trwa o rząd wielkości dłużej niż bitowe skanowanie w Postgresie.
* W fazie z dodanymi indeksami (Faza 2), po ręcznym dodaniu indeksu na `statsID`, wszystkie 3 bazy odnotowały rewelacyjne ujednolicone czasy rzędu **0.002s**.
* **Wniosek:** Test dowodzi, że przenoszenie schematów i uproszczeń architektonicznych z MySQL prosto do MongoDB lub Postgresa (z pominięciem jawnego definowania indeksów) jest zabójcze dla wydajności przy powiązaniach 1-N. Dodatkowo test udowadnia wybitną wyższość skanowania blokowego silnika relacyjnego (Postgres) nad skanowaniem dokumentowym NoSQL w przypadku awaryjnego braku indeksów na potężnych tabelach.

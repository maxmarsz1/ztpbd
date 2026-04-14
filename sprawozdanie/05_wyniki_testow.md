# 7. Wyniki Testów i Rozszerzona Analiza (Podsumowanie)

Zautomatyzowane testy z puli 24 ustrukturyzowanych skryptów na potężnych modelach badawczych udowodniły kilka interesujących zależności. Pomiary uśrednione z 3 transakcji (na każdy scenariusz w każdej z baz) można poddać weryfikacji. 

## 7.1 Obserwacje dla modelu CREATE (Wstawianie)
1. **Pojedynczy rekord**: System klucz-wartość taki jak Redis i architektury dokumentowe w Mongo górują gigantyczną szybkością powołania. Zwykłe zapisy zajmują promil setnych sekund – bazy relacyjne typu Postgres/MySQL muszą podeprzeć operacje walidacją integralności typów, sprawa pogarsza się gdy występuje dużo ograniczeń (Constraints).  
2. **Batch / Bulk Insert**: Optymalizacja w `execute_values`/`executemany` w środowiskac MySQL/PG znacznie zbliżyła rzędy operacji silników ze sobą. Potężne importy w MongoDB (insert_many) radzą sobie fenomenalnie nie mając balastu transakcyjnego podłoża.  
3. **Upserty/Konflikty**: Specyficzne, trudne do operacji zapisy korzystające z klauzuli `ON DUPLICATE/ON CONFLICT` wymagały minimalnie widocznie więcej czasu dla logiki serwerów relacyjnych.

## 7.2 Obserwacje dla modelu READ (Odczytywanie)
1. **Proste zapytania i zagnieżdżenia**: Odczyty poprzez klucz główny (PK) niemal pokrywają się wydajnościowo pośród wszystkich silników testowych - uogólniając ich zastosowanie. Wprowadzając jednak skomplikowane odczyty wymagające filtracji danych tekstowych (np. `LIKE`), MySQL radził skrajnymi nie raz opóźnieniami w stosunku do rewelacyjnie operującego zapytania typu "Aggregata/Find" w Mongo.  
2. **Użycie JOIN (Relacje vs BSON)**: W typowej grupie "Złóż obiekt na podstwie relacji C z tabel A i B", wygrywa bezapelacyjnie PostgreSQL. Bazy NoSQL jak MongoDB musiały wspierać się funkcją operacji `$lookup`, która wymaga obciążenia, co jest anty-wzorcem nierelacyjnym - dla nich obiekt powinien być zagnieżdżony bezpośrednio aby zachował skalowalność odczytu. Główne operacje agregujące potwierdzają przewagę RDBMS pod kątem skomplikowanej analityki systemowej gier.

## 7.3 Wyniki dla UPDATE i DELETE
1. Masowe usuwanie i przycinanie tysięcy danych w Redisie wykazywało opóźnienia I/O po zablokowaniu jego jedynego wątku operującego obróbką pamięciową setów. W wypadku masowego usuwania za pomocą kryteriów, bazy relacyjne wykazywały pewne nieoczekiwane luki na logowanie trwansej transakcji usunięcia (w przeciwieństwie do operacji wyczyszczenia szybkiego poprzez potężny mechanizm `TRUNCATE`).

## 8. Wnioski 
Zaprojektowany system rzetelnie odwzorował wady i zalety różnych koncepcji badanych SZBD: 
* Praca w chmurze dokumentowej jest obłędnie opłacalna i elastyczna do szybkiego modyfikowania na bieżąco struktur logiki aplikacji i przechowywania dużych płaszczyzn JSONów, dopóty po miesiącu użytkowania developer nie natrafi na konieczność dołączenia z potężnej odrębnej kolekcji np. setek rzędów specyficznej zmiennej przez operacje asocjacji/join, a co za tym idzie naruszy logikę ich szybkiego wstrzykiwania do klienta.
* Bazy Relacyjne to serca bankowości wymagające nakładów programistycznych na początkach projektów, ale stawiające absolutne rygorystyczne wymagania typologiczne i integralnościowe weryfikując nieszczelności i braki obiektowe z logiki systemów - opłacają się w długim torze analiz badawczych i w systemach transakcyjnych. 
* Wprowadzenie indeksów wydajnościowych B-Tree dla badanej aplikacji badającej gigantyczne wolumeny rzędu ponad 1-10 milionów w testowanym systemie MMORPG wykazało drastyczną wymagalność i znaczenie ich istnienia na etapie odczytu statystyk, zmniejszając koszty w środowiskach z rzędu setek tysięcy czasów procesora o 98-99%. 

**Raport wykonany w oparciu na test aplikacyjny i pomiary autorskim systemem wizualizacyjnym na zaliczenie laboratorium z przedmiotu ZTBPD.**

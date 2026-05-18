\section{Przegląd wybranych technologii bazodanowych}

\subsection{Charakterystyka wybranych systemów (SZBD)}
Do weryfikacji testowej i badawczej niniejszego projektu wytypowano cztery wiodące technologie bazodanowe, reprezentujące odmienne paradygmaty przechowywania danych.

\subsubsection*{PostgreSQL}
Najpopularniejsza, otwartoźródłowa, obiektowo-relacyjna baza danych, uchodząca za rynkowy standard bezpieczeństwa i niezawodności.
\begin{itemize}
    \item \textbf{Specyfika i architektura:} Oparta na wieloprocesowości (osobny proces dla każdego zapytania), z potężnym silnikiem zapytań obsługującym złożone operacje.
    \item \textbf{Zalety:} Pełna zgodność z modelem ACID, ogromne możliwości rozszerzeń, wsparcie dla zaawansowanego indeksowania (GiST, GIN, BRIN), idealna dla hurtowni danych i skomplikowanych złączeń (JOIN).
    \item \textbf{Wady:} Wymaga znacznych zasobów konfiguracyjnych i sprzętowych (pamięciowych) przy dużej liczbie jednoczesnych, prostych połączeń. Możliwy spadek wydajności przy ekstremalnie intensywnych operacjach zapisu.
    \item \textbf{Zastosowania biznesowe:} Główne systemy transakcyjne, systemy bankowe, ERP, rozbudowane aplikacje GIS.
\end{itemize}

\subsubsection*{MySQL}
Powszechnie wdrażany, wielowątkowy system relacyjny RDBMS, którego domyślnym i nowoczesnym silnikiem zapisu jest InnoDB.
\begin{itemize}
    \item \textbf{Specyfika i architektura:} Zoptymalizowana pod kątem operacji odczytu, obsługuje połączenia w oparciu o wątki w ramach pojedynczego procesu.
    \item \textbf{Zalety:} Wyjątkowa wydajność prostych odczytów, prosta konfiguracja, ogromna społeczność oraz doskonała kompatybilność wsteczna.
    \item \textbf{Wady:} Mniejsza dyscyplina w typowaniu danych w porównaniu do PostgreSQL, słabsza obsługa bardzo złożonych zapytań analitycznych, mniejsze możliwości funkcji okna i złączeń zewnętrznych.
    \item \textbf{Zastosowania biznesowe:} Platformy e-commerce, systemy CMS (np. WordPress), aplikacje webowe o umiarkowanej złożoności danych.
\end{itemize}

\subsubsection*{MongoDB}
Nierelacyjny, rozproszony system zarządzania bazą danych (NoSQL) oparty na modelu dokumentowym (BSON).
\begin{itemize}
    \item \textbf{Specyfika i architektura:} Brak z góry narzuconego schematu (\textit{schema-less}), relacje zastąpione są zagnieżdżaniem dokumentów i potężnym \textit{Aggregation Framework}.
    \item \textbf{Zalety:} Naturalne mapowanie obiektów aplikacyjnych na dokumenty bazy, ogromna elastyczność i szybkość prototypowania, wbudowane wsparcie dla wysokiej dostępności.
    \item \textbf{Wady:} Powielanie (\textit{denormalizacja}) danych prowadzi do wysokiego zużycia przestrzeni dyskowej, brak pełnego i zoptymalizowanego mechanizmu deklaratywnych złączeń pomiędzy wieloma kolekcjami.
    \item \textbf{Zastosowania biznesowe:} Katalogi produktowe, zarządzanie treścią rozproszoną, systemy real-time analytics, rozwój w metodyce Agile.
\end{itemize}

\subsubsection*{Redis (Remote Dictionary Server)}
In-memory data structure store, klasyfikowany jako baza nierelacyjna typu klucz-wartość (Key-Value NoSQL).
\begin{itemize}
    \item \textbf{Specyfika i architektura:} Działa w głównej pamięci RAM (z opcjonalnym zrzutem na dysk), oparty na jednowątkowej pętli zdarzeń obsługującej predefiniowane struktury (listy, zbiory, hashe).
    \item \textbf{Zalety:} Ekstremalnie niskie opóźnienia (mikrosekundy), brak narzutu wejścia/wyjścia nośników dyskowych, prostota implementacji algorytmów na strukturach in-memory.
    \item \textbf{Wady:} Pojemność bazy ograniczona do fizycznej pamięci RAM, ryzyko utraty najświeższych danych w przypadku nagłej awarii zasilania (przy braku restrykcyjnego trybu AOF).
    \item \textbf{Zastosowania biznesowe:} Systemy cache'owania, sesje użytkowników webowych, tablice wyników (leaderboards) w grach, obsługa strumieni i wiadomości (pub/sub).
\end{itemize}

\subsection{Architektura, bezpieczeństwo i skalowalność}
Analiza środowisk bazodanowych wymaga szerszego spojrzenia na atrybuty takie jak ich elastyczność strukturalna i tolerancja na błędy. 

\begin{itemize}
    \item \textbf{Awaryjność i ciągłość działania (High Availability):} 
    Bazy nierelacyjne takie jak MongoDB domyślnie wykorzystują architekturę Replica Set z automatycznym wyborem węzła wiodącego (automatyczny \textit{failover}), minimalizując przestoje. Z kolei w PostgreSQL i MySQL standardem jest model Primary-Standby wspierany replikacją strumieniową logów. Redis z kolei polega na replikacji asynchronicznej połączonej z mechanizmem \textit{Sentinel} dającym odporność na awarie, jednakże jako system in-memory jest szczególnie podatny na fizyczne odcięcia zasobów i potencjalną utratę mikrosekundowych interwałów pamięci przy snapshotach dyskowych (RDB).

    \item \textbf{Mechanizmy bezpieczeństwa i integracja:}
    Systemy RDBMS posiadają rozbudowane modele autoryzacji do poziomu pojedynczego wiersza (RLS - \textit{Row-Level Security} w PostgreSQL), co sprzyja ich zastosowaniu w środowiskach rygorystycznie kontrolowanych. Technologie NoSQL jak MongoDB zyskały potężne mechanizmy ochrony i szyfrowania danych w spoczynku, jednak to schematyczne blokady w bazach relacyjnych nadal tworzą wyższy poziom twardego bezpieczeństwa przed niepożądanymi nieścisłościami referencyjnymi.

    \item \textbf{Migracje w czasie (Ewolucja struktur):}
    W systemach relacyjnych każda zmiana wymaga procedur migracyjnych (np. poprzez narzędzia Alembic lub Flyway) ingerujących z blokadami (\textit{lockami}) tabel. System dokumentowy w MongoDB nie wymusza twardych schematów, dzięki czemu rozbudowa modelu danych zachodzi bezpośrednio na poziomie kodu aplikacji podczas transformacji obiektowej bez czasochłonnych blokad strukturalnych bazy.

    \item \textbf{Skalowalność (Vertical vs Horizontal):}
    Relacyjne bazy danych (PostgreSQL, MySQL) zaprojektowane są przede wszystkim pod skalowalność pionową (\textit{Vertical Scaling} -- wzmocnienie pamięci, procesora jednej maszyny), gdyż wprowadzanie rozproszonych mechanizmów partycjonowania i klastrowania generuje wysoki stopień komplikacji i kompromisów wydajnościowych. Systemy MongoDB i Redis od początku budowane były z myślą o skalowalności poziomej (\textit{Horizontal Scaling} -- \textit{sharding} i partycjonowanie kluczy), umożliwiając swobodne poszerzanie rozproszonego klastra o nowe serwery robocze w odpowiedzi na rosnące zapotrzebowanie.
\end{itemize}

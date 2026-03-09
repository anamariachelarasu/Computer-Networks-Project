# Client CoAP
## Proiect la disciplina: Rețele de calculatoare

### Studenți:
* Ana-Maria Chelarașu
* Laurențiu-Andrei Grădinariu
### Coordonator
Nicolae-Alexandru Botezatu

## Introducere

CoAP (Constrained Application Protocol) este un protocol de comunicație web specializat, proiectat pentru dispozitive cu resurse limitate cum ar fi senzori, actuatori și alte dispozitive IoT. Este standardizat în RFC 7252 și reprezintă o alternativă lightweight la HTTP, optimizată pentru rețele cu lățime de bandă redusă și dispozitive cu putere de procesare și memorie limitate.

## Caracteristici Principale
* Protocol lightweight - optimizat pentru dispozitive cu resurse limitate
* Bazat pe UDP - overhead redus comparativ cu TCP
* Suport pentru multicast - permite descoperirea automată a serverelor
* Observarea resurselor - clienții pot fi notificați automat la schimbări
* Securitate - suport pentru DTLS (Datagram Transport Layer Security)
* Interoperabilitate cu HTTP - poate fi mapat ușor către/de la HTTP

## Metode CoAP (similare cu HTTP)
* GET - obținerea unei resurse
* POST - crearea unei noi resurse
* EDIT - actualizarea unei resurse
* MOVE - actualizarea locatiei unei resurse
* DELETE - ștergerea unei resurse

## Aplicație - CoAP Client
Proiectul implementează funcționalitatea unui client CoAP care poate comunica cu servere CoAP din rețea. Interfața grafică permite utilizatorului să trimită request-uri, să observe resurse și să descopere servere disponibile. În cadrul acestui proiect, comunicarea este gestionată prin intermediul modulului socket din Python, fără a utiliza biblioteci externe (de exemplu aiocoap, coapthon). 

## Implementare
Proiectul implementează atât partea de mesagerie, cât și partea de cerere/răspuns, amândouă specifice protocolului CoAP. Mesajele sunt de două tipuri: 
* **Confirmable (CON)** care necesită un pachet de tip Acknowledgement (ACK). Clientul monitorizează primirea acestuia printr-un mecanism de timeout.
* **Non-Confirmable (NON)** care nu necesită confirmare. Acest tip este folosit pentru operațiuni unde confirmarea imediată nu este critică (de exemplu refresh la listă în anumite condiții).

![Arhitectura Aplicatiei](images/arhitectura_app.svg)

## Logica de comunicare UDP
Pentru a asigura recepția răspunsurilor, aplicația folosește un socket UDP legat de un port local (sock.bind(('0.0.0.0', 6000))). Transmisia se realizează către un port al serverului, iar pentru fiecare pachet de tip Confirmable se aplică un settimeout(2), asigurând astfel gestionarea situațiilor în care serverul este indisponibil.

## Cererile și Răspunsurile
Cererile si răspunsurile CoAP sunt transportate în mesaje CoAP, care includ fie un cod de metodă (Method Code), fie un cod de răspuns (Response Code). Informațiile opționale sunt transportate sub formă de date utile (Payload), conform pachetului de date specificat. O cerere este transportată într-un mesaj Confirmabil sau Neconfirmabil.

Mesajele care nu necesită o transmisie fiabilă poate fi trimis ca mesaj Neconfirmabil (NON). Acestea nu sunt confirmate, dar au un ID de Mesaj pentru detectarea duplicatelor (de exemplu 0x01a0).
```
Client              Server
    |                  |
    |   NON [0x01a0]   |
    +----------------->|
    |                  |
```

Fiabilitatea este asigurată prin marcarea unui mesaj ca fiind Confirmabil (CON). În implementare este folosit un algoritm de back-off exponențial până la primirea unui mesaj de Confirmare (ACK) cu același ID (de exemplu 0x7d34).

```
Client              Server
    |                  |
    |   CON [0x7d34]   |
    +----------------->|
    |                  |
    |   ACK [0x7d34]   |
    |<-----------------+
    |                  |
```

## Structura mesajului CoAP
Mesajele CoAP sunt codificate într-un format binar simplu. Formatul mesajului începe cu antetul (header-ul) de dimensiune fixă de 4 octeți. 
```
0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Ver| T |  TKL  |      Code     |          Message ID           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |   Token (if any, TKL bytes) ...
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |   Options (if any) ...
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |1 1 1 1 1 1 1 1|    Payload (if any) ...
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```
Explicația câmpurilor:
* **Verisune (Ver)** Întreg fără semn pe 2 biți. Indică numărul versiunii CoAP (01 în binar).
* **Tip (T)** Întreg fără semn pe 2 biți. Indică dacă acest mesaj este de tip CON (0), NON (1), ACK (2) sau RST (3).
* **Lungime Token (TKL)** Întreg fără semn pe 4 biți. Indică lungimea câmpului Token variabil (0-8 octeți). Lungimile 9-15 sunt rezervate.
* **Code (Code)** Întreg fără semn pe 8 biți, împărțit într-o clasă de 3 biți și un detaliu de 5 biți sub forma "c.dd", unde "c" este de la 0 la 7, iar "dd" este de la 00 la 31.
* **ID Mesaj (Message ID)** Întreg fără semn pe 16 biți în ordinea octeților de rețea (network byte order), scopul fiind prevenirea duplicării mesajelor.

## Formatul și Structura Payload-ului
Toate cererile utilizează un obiect JSON codificat UTF-8. Fiecare mesaj include date pentru controlul fragmentării:
* **f_cur**: indexul fragmentului curent (începând de la 1)
* **f_tot**: numărul total de fragmente trimise

### Create (CODE_CREATE = 1)
Folosit pentru crearea unui nou fișier sau director pe server.
* **type** - tipul resursei.
* **name** - numele noului fișier.
* **extension** - extensia noului fișier.
* **content** - fragmentul de conținut.
* **f_cur / f_tot** - indicatori pentru reasamblarea fișierului pe server.

### Get (CODE_GET = 2)
Folosit pentru a lista conținutul directorului sau a prelua un fișier.
* **path** - calea completă a fișierului care urmează a fi primit.
* **name / extension** - confirmarea numelui și extensiei.

### Delete (CODE_DELETE = 3)
Elimină o resursa de pe server.
* **path** - calea completă a fișierului care urmează să fie șters.

### Move / Rename (CODE_MOVE = 4)
Folosit pentru a redenumi un fișiser sau pentru a îl muta într-o altă locație.
* **path** - calea completă a fișierului.
* **new_path** - noua cale unde va fi mutat fișierul.

### Edit (CODE_EDIT = 5)
Actualizează conținutul unui fișier existent.
* **path** - calea completă a fișierului.
* **content** - noul fragment de text ce trebuie adăugat sau suprascris.
* **new_name** - câmp opțional pentru redenumire simultană cu editarea.

## Fragmentarea mesajelor
În cazul în care se dorește transmiterea de fișiere mari, aplicația folosește o fragmentare la nivel de aplicație, divizând datele în bucăți care pot fi gestionate. Textul este preluat și împărțit pe segmente de dimensiune fixă, aceasta fiind egală cu 2 unități.
În scopul reasamblării corect a conținutului de către server fiecare pachet conține datele de secvențiere în payload-ul JSON: f_cur (indexul fragmentului curent) și f_tot (numărul total de pachete care trebuie să ajungă). 
Aplicația parcurge lista de fragmente și trimite câte un mesaj CoAP separat pentru fiecare. Dacă mesajul este de Confirmable, aplicația așteaptă un Acknowledgement pentru fragmentul curent înainte de a trece la următorul.

## Tehnologii folosite

* **Python cu Tkinter** pentru construirea interfeței grafice (GUI), gestionarea evenimentelor (de exemplu click-uri, selecții din listă) și afișarea jurnalului de mesaje;
* **Socket (UDP)** pentru trimiterea si primirea datagramelor pe portul 5000, cu scopul implementării comunicării la nivel transport;
* **Procesare binară (Bitwise Operations)** pentru împachetarea manuală a header-ului CoAP;  
* **JSON** - pentru serializarea / deserializare payload-ului. Toate datele sub trimise sub formă de obiecte JSON codificate în format binar (UTF-8).
* **Fragmentarea mesajelor** pentru împărțirea fișierelor mai mari în bucăți de 2 unități pentru a respecta limitele pachetelor UDP.
* **Timeout-urile** de 2 secunde pentru a gestiona mecanismele de confirmare prin Acknowledgement în cazul mesajelor Confirmable.

## Structura Aplicației
![Structura Aplicatiei](images/structura_aplicatie.svg)
## Diagramă de clase
![Diagrama de clase](images/diagrama_app.svg)

## Bibliografie
* **RFC 7252** - https://datatracker.ietf.org/doc/html/rfc7252
* **Documentație Python** - https://docs.python.org/3/
* **Materiale puse la dispoziție pe platforma educațională**
#   C o m p u t e r - N e t w o r k s - P r o j e c t  
 
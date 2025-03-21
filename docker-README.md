## PyRope in Docker

### Vorbedingung

- Docker Desktop ist installiert und läuft

### Befehle zum erstmaligen Erzeugen des Containers

#### ohne Volume

- Bauen des Docker-Containers: `docker build . -t pyrope`

- Starten des Containers: `docker run -p 8888:8888 pyrope`

#### mit Volume

- Erstellen des Volume: `docker volume create pyrope-notebooks`

- Bauen des Docker-Containers: `docker build . -t pyrope`

- Starten des Containers: `docker run -p 8888:8888 -v pyrope-notebooks:/work pyrope`

### weitere Nutzungshinweise

- um zum Notebook zu gelangen, Link mit `http://127.0.0.1:...` aus der Konsole kopieren und im Browser öffnen

- Starten und Stoppen des Containers über die Docker Desktop Oberfläche (Link zum Notebook ist dann beim Klick auf den Container-Namen zu finden)
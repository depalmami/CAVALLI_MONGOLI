# Cavalli Bridge — Live su un Mac, gioco sull'altro

Il ponte invia **clock di Live, note/CC MIDI e livello audio** al gioco 3D via UDP. Il gioco mostra lo stato nella console Musica e usa i dati per il suo motore visivo. Il device Audio lascia passare il suono nella traccia; il device MIDI lascia passare le note.

## Preparazione

1. Collega i Mac alla stessa rete, preferibilmente Ethernet. Sul Mac del gioco, nella cartella `CAVALLI_MONGOLI`, avvia `npm install` (solo la prima volta) e `npm start`, poi apri `http://localhost:3000/horse-racing-3d.html` oppure l'indirizzo HTTPS indicato dal server.
2. Sul Mac del gioco trova l'indirizzo IPv4 mostrato da `npm start` (per esempio `192.168.1.20`). Il server ascolta UDP **41234**; autorizza Node nel firewall macOS se richiesto.
3. Copia **tutta** questa cartella sul Mac con Ableton Live. In `bridge-config.json` sostituisci `127.0.0.1` con l'IPv4 del Mac del gioco. Mantieni i file `.amxd`, `.js` e `.json` nella stessa cartella.
4. Trascina `Cavalli Bridge Audio.amxd` sulla traccia Master di Live. Mentre Live suona, la console del gioco deve mostrare `RETE … BPM` e `audio …%`.
5. Trascina `Cavalli Bridge MIDI.amxd` **prima dello strumento** sulla traccia MIDI da cui vuoi ricevere note e CC. Se vuoi più tracce, metti una copia del device su ciascuna. Le note GM 35/36, 38/40, 42/44/46 diventano cassa, rullante e charleston; il gioco riceve anche gli eventi `nota` e `cc`.

Nella console Musica del gioco, `Tempo da: Automatico` preferisce il clock di rete. `Solo clock da Live in rete` lo forza. Se Live non sta suonando o la rete cade, il gioco torna al tempo libero; con Automatico può usare anche gli ingressi locali. `Anticipo visivo` compensa la latenza del proiettore.

**Audio:** questo ponte trasmette il livello del segnale circa 20 volte al secondo, utile per l'energia e gli effetti. Non trasporta il suono ascoltabile né uno spettro multibanda. Per ascoltare l'audio del secondo Mac serve un percorso audio separato (interfaccia/cavo o un'app di audio in rete); se arriva come ingresso al Mac del gioco, puoi selezionarlo in `Ascolta ingresso` per ottenere anche l'analisi completa del gioco.

I device sono stati generati dai template Max for Live di Live 12 e non richiedono pacchetti NPM sul Mac di Live. `node.script` usa il Node integrato in Max. Se cambi `bridge-config.json` con i device già caricati, rimuovili e ricaricali.

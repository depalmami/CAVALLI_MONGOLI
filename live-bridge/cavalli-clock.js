// Max js: legge il trasporto di Live, senza alterarlo.
autowatch = 1;
outlets = 1;
var song = null;
function bang() {
  try {
    if (!song) song = new LiveAPI('live_set');
    var bpm = Number(song.get('tempo')[0]);
    var beat = Number(song.get('current_song_time')[0]);
    var playing = Number(song.get('is_playing')[0]);
    if (isFinite(bpm) && isFinite(beat)) outlet(0, 'clock', bpm, Math.max(0, beat), playing);
  } catch (e) { post('Cavalli Bridge clock: ' + e + '\n'); }
}

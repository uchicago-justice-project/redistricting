// Interactive 1: hop through pre-rendered PNGs at each redistricting year.

const REDIST_YEARS = [1923, 1931, 1947, 1961, 1970, 1981, 1985, 1995, 2005, 2015, 2023];
const DWELL_MS = 1000; // ms to pause at each year

(function () {
  const img      = document.getElementById('ward-img');
  const slider   = document.getElementById('year-slider');
  const yearLabel = document.getElementById('real-year');

  // Preload all images
  const imgCache = {};
  REDIST_YEARS.forEach(y => {
    const i = new Image();
    i.src = `./images/ward_${y}.png`;
    imgCache[y] = i;
  });

  slider.min   = 0;
  slider.max   = REDIST_YEARS.length - 1;
  slider.step  = 1;
  slider.value = 0;

  function showYear(idx) {
    const year = REDIST_YEARS[idx];
    img.src = imgCache[year].src;
    yearLabel.textContent = year;
    slider.value = idx;
  }

  // ── Animation ─────────────────────────────────────────────────────────────
  let idx    = 0;
  let timerId = null;
  let paused  = false;

  function advance() {
    if (paused) return;
    idx = (idx + 1) % REDIST_YEARS.length;
    showYear(idx);
    timerId = setTimeout(advance, DWELL_MS);
  }

  function start() {
    paused = false;
    timerId = setTimeout(advance, DWELL_MS);
  }

  function stop() {
    paused = true;
    clearTimeout(timerId);
    timerId = null;
  }

  // Manual scrubbing
  slider.addEventListener('mousedown',  stop);
  slider.addEventListener('touchstart', stop, { passive: true });

  slider.addEventListener('input', () => {
    idx = Number(slider.value);
    showYear(idx);
  });

  slider.addEventListener('mouseup',  () => { start(); });
  slider.addEventListener('touchend', () => { start(); });

  showYear(0);
  start();
})();

// Interactive 1: swap pre-rendered PNGs on a smooth animated slider.
// Slider range = real years 1923–2023. Map snaps at each redistricting year.

const REDIST_YEARS = [1923, 1931, 1947, 1961, 1970, 1981, 1985, 1995, 2005, 2015, 2023];
const YEAR_MIN = 1923;
const YEAR_MAX = 2023;

const SPEED    = 7;    // real years per second during travel
const DWELL_S  = 0.4;  // seconds to pause when hitting a redistricting year

(function () {
  const img       = document.getElementById('ward-img');
  const slider    = document.getElementById('year-slider');
  const realYear = document.getElementById('real-year');  // 1923, 1924 … 2023

  // Preload all images for instant swaps
  const imgCache = {};
  REDIST_YEARS.forEach(y => {
    const i = new Image();
    i.src = `./images/ward_${y}.png`;
    imgCache[y] = i;
  });

  slider.min   = YEAR_MIN;
  slider.max   = YEAR_MAX;
  slider.step  = 1;
  slider.value = YEAR_MIN;

  // Which redistricting year applies for a given real year
  function redistYearFor(y) {
    let result = REDIST_YEARS[0];
    for (const ry of REDIST_YEARS) {
      if (ry <= y) result = ry;
      else break;
    }
    return result;
  }

  function showRedistYear(ry) {
    img.src = imgCache[ry].src;
  }

  // ── Animation ─────────────────────────────────────────────────────────────
  let pos          = YEAR_MIN;   // current real-year position
  let lastRedist   = YEAR_MIN;   // redistricting year currently displayed
  let dwelling     = false;
  let dwellEnd     = null;
  let lastTs       = null;
  let rafId        = null;
  let paused       = false;

  function tick(ts) {
    if (paused) return;
    if (lastTs === null) lastTs = ts;
    const dt = Math.min((ts - lastTs) / 1000, 0.1); // cap dt to avoid jumps
    lastTs = ts;

    if (dwelling) {
      if (ts >= dwellEnd) dwelling = false;
    } else {
      pos += SPEED * dt;

      if (pos >= YEAR_MAX) {
        pos = YEAR_MIN;
        lastRedist = YEAR_MIN;
        showRedistYear(YEAR_MIN);
      }

      // Check if we've crossed into a new redistricting year
      const ry = redistYearFor(Math.floor(pos));
      if (ry !== lastRedist) {
        lastRedist = ry;
        showRedistYear(ry);
        dwelling = true;
        dwellEnd = ts + DWELL_S * 1000;
      }
    }

    const currentYear = Math.round(pos);
    slider.value = currentYear;
    realYear.textContent = currentYear;
    rafId = requestAnimationFrame(tick);
  }

  function start() {
    paused = false;
    lastTs = null;
    rafId  = requestAnimationFrame(tick);
  }

  function stop() {
    paused = true;
    cancelAnimationFrame(rafId);
    rafId = null;
  }

  // Manual scrubbing
  slider.addEventListener('mousedown',  stop);
  slider.addEventListener('touchstart', stop, { passive: true });

  slider.addEventListener('input', () => {
    pos = Number(slider.value);
    realYear.textContent = Math.round(pos);
    const ry = redistYearFor(Math.floor(pos));
    lastRedist = ry;
    showRedistYear(ry);
  });

  slider.addEventListener('mouseup', () => {
    dwelling = false; lastTs = null; start();
  });
  slider.addEventListener('touchend', () => {
    dwelling = false; lastTs = null; start();
  });

  showRedistYear(YEAR_MIN);
  start();
})();

// Rewritten version of gauge_modals.js to implement looping structure with tabbed UI
// This file deals with generating the pins on the interactive map and generating graphs after they are clicked

// Function to close all modals
function closeModal() {
  var modals = document.querySelectorAll('.modal');
  for (var i = 0; i < modals.length; i++) {
    modals[i].style.display = 'none';
  }
}

// Event handler when map loads
map.on('load', function () {
  map.resize();
});

// Arrays for latitude, longitude, and text
var lat = [47.2852816, 47.287222, 47.2888822, 47.07971406, 46.8338827, 46.81416667, 46.7033333, 46.3761111, 
           45.6486883, 45.7119422, 45.2558171, 46.65638889, 42.74844444, 44.4512927, 44.0516567, 43.0661976, 42.8619, 47.4949814, 48.0027953,
           46.084858, 46.38, 46.44303, 46.328, 45.92, 45.92, 45.8, 45.67, 45.42];

var lon = [-101.6221093, -101.3397222, -101.0379239, -100.9323594, -100.9745789, -100.8213889, -101.2136111, 
           -100.93444, -102.6433259, -100.5593015, -100.8429214, -100.7391667, -98.058, -100.4043407, -99.4545179, -98.5366157, -97.4853, -101.4162492, -106.4183359,
           -100.676495, -102.322, -101.373829, -100.277, -102.11, -101.34, -100.78, -100.11, -101.08];

var text = ['Hazen', 'Stanton', 'Washburn', 
            'Price', 'Mandan', 'Bismarck', 'Judson', 
            'Breien', 'Cash', 'Wakpala', 'Whitehorse', 
            'Schmidt', 'Little Eagle', 'Oahe', 'Big Bend', 'Fort Randall', 'Gavins Point', 'Garrison', 'Fort Peck',
            'Fort Yates', 'Mott', 'Carson', 'Linton', 'Lemmon', 'McIntosh', 'Mclaughlin', 'Mound City', 'Timber Lake'];


// Build fetchedURLS from server-provided graphMap when available.
// Fallback: if named <Place>URLS variables exist, use them; otherwise empty array.
var fetchedURLS = (function(){
  try {
    var map = window.graphMap || {};
    return text.map(function(name){
      if (map && map[name] && Array.isArray(map[name]) && map[name].length) return map[name];
      // try fallback variable like HazenURLS (if template still defines them)
      var varName = name.replace(/\s+/g, '') + 'URLS';
      if (typeof window[varName] !== 'undefined') return window[varName];
      return [];
    });
  } catch (e) {
    console.warn('Error building fetchedURLS from graphMap', e);
    return text.map(function(){ return []; });
  }
})();

// Group URLs by inferred type and chart/table

// Resolve a raw entry to an absolute/static URL when possible.
function resolveUrl(raw) {
  if (!raw) return raw;
  const s = String(raw);
  if (/^(https?:)?\/\//i.test(s)) return s;
  if (s.startsWith('/')) return s;
  const base = (window && window.baseGraphUrl) ? window.baseGraphUrl : '';
  if (/graphs\//i.test(s)) {
    if (base && !s.startsWith(base)) {
      const p = s.split(/graphs\//i).pop();
      return base + p;
    }
    return s;
  }
  return base + s;
}

function groupUrlsByType(urls) {
  const grouped = {};
  if (!Array.isArray(urls)) return grouped;

  const decode = (s) => String(s || '').replace(/%20/g, ' ');

  // Resolve a raw entry to an absolute/static URL when possible.
  function resolveUrl(raw) {
    if (!raw) return raw;
    const s = String(raw);
    // Already absolute or protocol-relative
    if (/^(https?:)?\/\//i.test(s)) return s;
    // Leading slash (site-relative) — return as-is
    if (s.startsWith('/')) return s;
    // If the app provided a baseGraphUrl, prefer that for bare filenames
    const base = (window && window.baseGraphUrl) ? window.baseGraphUrl : '';
    // If it already contains "graphs/" but is not absolute, attempt to make it rooted under base
    if (/graphs\//i.test(s)) {
      // if base already included, concatenate accordingly
      if (base && !s.startsWith(base)) {
        // take filename after 'graphs/' and append to base
        const p = s.split(/graphs\//i).pop();
        return base + p;
      }
      return s;
    }
    // Bare filename -> prefix with base
    return base + s;
  }

  urls.forEach(raw => {
    const path = decode(raw);

    // Try to extract the title from different possible layouts
    let m = path.match(/graphs\/(.+?)\.html/i);
    if (!m) {
      const m2 = path.match(/([^\/]+)\.html$/i);
      if (m2) m = [null, m2[1]];
    }
    if (!m) return;

    const title = m[1];
    const isTable = /table/i.test(title);

    let type = '';
    if (title.includes(' at ')) {
      const parts = title.split(' at ');
      type = parts[0].trim();
    } else if (isTable) {
      const withoutTable = title.replace(/\s+Table$/i, '').trim();
      const places = ['Hazen', 'Stanton', 'Washburn', 'Price', 'Mandan', 'Bismarck', 'Judson', 
                      'Breien', 'Cash', 'Wakpala', 'Whitehorse', 'Schmidt', 'Little Eagle', 
                      'Oahe', 'Big Bend', 'Fort Randall', 'Gavins Point', 'Garrison', 'Fort Peck',
                      'Fort Yates', 'Mott', 'Carson', 'Linton', 'Lemmon', 'McIntosh', 
                      'Mclaughlin', 'Mound City', 'Timber Lake'];
      let foundPlace = false;
      for (const place of places) {
        if (withoutTable.startsWith(place + ' ')) {
          type = withoutTable.substring(place.length).trim();
          foundPlace = true;
          break;
        }
      }
      if (!foundPlace) type = withoutTable;
    } else {
      type = title.replace(/\s+Table$/i, '').trim();
    }

    type = type.replace(/\s+/g, ' ').replace(/Baromatric/i, 'Barometric').trim();
    if (!type || type.length < 3) type = title.replace(/\s+Table$/i, '').trim();

    grouped[type] = grouped[type] || { Chart: null, Table: null };
    // store the raw entry (resolve later when assigning frame.src)
    if (isTable) grouped[type].Table = raw;
    else grouped[type].Chart = raw;
  });

  return grouped;
}

// Turn a raw graph/title string into a human-friendly tab label
function prettifyTitle(raw) {
  if (!raw) return '';
  let s = String(raw || '');
  // Decode common encodings
  s = s.replace(/%20/g, ' ');

  // Remove trailing '-interactive' or '_interactive' or 'interactive' tokens
  s = s.replace(/[_\-]?interactive$/i, '');
  s = s.replace(/[_\-]?interactive/i, '');

  // Strip common file-date suffixes like _20240805_20240904 or _2024-08-05_2024-09-04
  s = s.replace(/_?\d{6,8}(_|-)\d{6,8}$/g, '');
  s = s.replace(/_?\d{4}-\d{2}-\d{2}(_|-)\d{4}-\d{2}-\d{2}$/g, '');

  // Handle double-underscore gauge-style names: gauge__Place__metric__dates
  const parts = s.split('__');
  if (parts.length >= 3 && /^gauge$/i.test(parts[0])) {
    const place = parts[1].replace(/[_\-]+/g, ' ').trim();
    const metric = parts[2].replace(/[_\-]+/g, ' ').trim();
    return (metric ? capitalizeWords(metric) + ' — ' : '') + capitalizeWords(place) + ' (Gauge)';
  }

  // If there are double-underscores but not a gauge prefix, join them with em-dash
  if (s.indexOf('__') !== -1) {
    return parts.map(p => capitalizeWords(p.replace(/[_\-]+/g, ' ').trim())).join(' — ');
  }

  // Replace remaining underscores or hyphens with spaces
  s = s.replace(/[_\-]+/g, ' ').trim();

  // Remove redundant words
  s = s.replace(/\btable\b/i, '').trim();

  // Capitalize words
  return capitalizeWords(s);
}

function capitalizeWords(str) {
  return String(str || '').toLowerCase().split(/\s+/).filter(Boolean).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/** Build the tab UI inside a given modal element */
function renderTabsIntoModal(modalEl, urls) {
  if (!modalEl) return;
  const content = modalEl.querySelector('.modal-content');
  if (!content) return;

  // Preserve close button
  const closeBtn = content.querySelector('.close');
  content.innerHTML = '';
  if (closeBtn) content.appendChild(closeBtn);

  // Check for no URLs
  const grouped = groupUrlsByType(urls);
  const typeKeys = Object.keys(grouped).sort();
  // map keys to objects with human-friendly labels
  const types = typeKeys.map(k => ({ key: k, label: prettifyTitle(k) }));
  if (!types.length) {
    const p = document.createElement('p');
    p.textContent = 'No graphs available for this location.';
    content.appendChild(p);
    return;
  }
  // Base containers
  const tabsWrap = document.createElement('div');
  tabsWrap.className = 'tabs';

  const typeRow = document.createElement('div');
  typeRow.className = 'tab-row';
  typeRow.setAttribute('role', 'tablist');

  const subRow = document.createElement('div');
  subRow.className = 'subtab-row';

  const panels = document.createElement('div');
  panels.className = 'tab-panels';

  const frame = document.createElement('iframe');
  frame.className = 'graph';
  frame.style.width = '100%';
  frame.style.height = '70vh';
  frame.style.border = '0';
  panels.appendChild(frame);

  // State
  let activeType = types[0].key;
  let activeSub = 'Chart';

  // Build type buttons
  types.forEach((entry, idx) => {
    const t = entry.key;
    const label = entry.label || t;
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.title = t; // keep original key as tooltip for more detail
    if (idx === 0) b.classList.add('active');
    b.addEventListener('click', () => {
      [...typeRow.querySelectorAll('button')].forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      activeType = t;
      updateFrame();
    });
    typeRow.appendChild(b);
  });

  // Build sub buttons
  const chartBtn = document.createElement('button');
  chartBtn.type = 'button';
  chartBtn.textContent = 'Chart';

  const tableBtn = document.createElement('button');
  tableBtn.type = 'button';
  tableBtn.textContent = 'Table';

  [chartBtn, tableBtn].forEach(btn => {
    btn.addEventListener('click', () => {
      [...subRow.querySelectorAll('button')].forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      activeSub = btn.textContent;
      updateFrame();
    });
    subRow.appendChild(btn);
  });

  function updateFrame() {
    const entry = grouped[activeType] || {};
    const hasChart = !!entry.Chart;
    const hasTable = !!entry.Table;

    chartBtn.style.display = hasChart ? '' : 'none';
    tableBtn.style.display = hasTable ? '' : 'none';

    // If current sub is unavailable, switch to the other
    if (activeSub === 'Chart' && !hasChart && hasTable) activeSub = 'Table';
    if (activeSub === 'Table' && !hasTable && hasChart) activeSub = 'Chart';

    // Reflect sub active state
    [...subRow.querySelectorAll('button')].forEach(x => x.classList.remove('active'));
    if (activeSub === 'Chart' && hasChart) chartBtn.classList.add('active');
    if (activeSub === 'Table' && hasTable) tableBtn.classList.add('active');

    // Set src (resolve filenames or relative paths using baseGraphUrl)
    const rawUrl = (activeSub === 'Table') ? (entry.Table || '') : (entry.Chart || '');
    frame.src = rawUrl ? resolveUrl(rawUrl) : '';

    // If only one sub available, hide sub row
    if ((hasChart && !hasTable) || (!hasChart && hasTable)) {
      subRow.style.display = 'none';
    } else {
      subRow.style.display = '';
    }
  }

  tabsWrap.appendChild(typeRow);
  tabsWrap.appendChild(subRow);
  tabsWrap.appendChild(panels);
  content.appendChild(tabsWrap);

  updateFrame(); // init
}

for (var i = 0; i < lat.length; i++) {
  var markerColor;
  // 0–12: Gauge (red), 13–18: Dam (blue), 19+: Mesonet (green)
  if (i < 13) {
    markerColor = 'red';
  } else if (i < 19) {
    markerColor = 'blue';
  } else {
    markerColor = 'green';
  }

  // Create marker for each location
  var marker = new mapboxgl.Marker({ color: markerColor })
    .setLngLat([lon[i], lat[i]])
    .addTo(map);

  // Debug: log marker creation
  console.debug('[openModals.js] Created marker', i, 'coords:', lon[i], lat[i], 'label:', text[i]);

  // Add event listener to each marker
  (function(index) {
    marker.getElement().addEventListener('click', function() {
      console.debug('[openModals.js] marker click', index, text[index]);
      // Close all modals
      closeModal();

      // Find modal by sanitized ID (strip spaces) but fall back to raw text
      var baseId = text[index];
      var modalIdNoSpace = baseId.replace(/\s+/g, '');
      var modal = document.getElementById(modalIdNoSpace) || document.getElementById(baseId);

      if (!modal) {
        console.warn('Modal not found for:', baseId);
        return;
      }

      // Show modal
      modal.style.display = 'block';

      // Clear existing content but preserve close button
      var content = modal.querySelector('.modal-content');
      var closeButton = content.querySelector('.close');
      content.innerHTML = '';
      if (closeButton) content.appendChild(closeButton);

      // Build tabbed iframe(s) for this station, based on offered graph types
      var urls = fetchedURLS[index]; // may be undefined if you haven't added arrays yet
      renderTabsIntoModal(modal, urls);

      // Close behavior
      closeButton = modal.querySelector('.close');
      if (closeButton) {
        closeButton.addEventListener('click', function() {
          modal.style.display = 'none';
        }, { once: true });
      }

      // Scroll to the bottom of the map to reveal the opened modal area
      var mapHeight = document.getElementById("map").offsetHeight; 
      scrollTo({
        top: mapHeight,
        left: 0,
        behavior: "smooth"
      });
    });
  })(i);
}
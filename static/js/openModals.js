// Rewritten version of gauge_modals.js to implement looping structure
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

            fetch(HazenURLS)
            fetch(StantonURLS)
            fetch(WashburnURLS)
            fetch(PriceURLS)
            fetch(MandanURLS)
            fetch(BismarckURLS)
            fetch(JudsonURLS)
            fetch(BreienURLS)
            fetch(CashURLS)
            fetch(WakpalaURLS)
            fetch(WhitehorseURLS)
            fetch(SchmidtURLS)
            fetch(LittleEagleURLS)
            fetch(OaheURLS)
            fetch(BigBendURLS)
            fetch(FortRandallURLS)
            fetch(GavinsPointURLS)
            fetch(GarrisonURLS)
            fetch(FortPeckURLS)
            fetch(FortYatesURLS)
            fetch(MottURLS)
            fetch(CarsonURLS)
            fetch(LintonURLS)

fetchedURLS = [HazenURLS, StantonURLS, WashburnURLS, PriceURLS, MandanURLS, BismarckURLS, JudsonURLS, BreienURLS, CashURLS, WakpalaURLS, WhitehorseURLS, SchmidtURLS, LittleEagleURLS, OaheURLS, BigBendURLS,
              FortRandallURLS, GavinsPointURLS, GarrisonURLS, FortPeckURLS, FortYatesURLS, MottURLS, CarsonURLS, LintonURLS]

// Loop through the data arrays
for (var i = 0; i < lat.length; i++) {
  var markerColor;
  // Assign marker color based on index
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

  // Add event listener to each marker
  (function(index) {
    marker.getElement().addEventListener('click', function() {
      
      // Close all modals
      closeModal();
      
      // Get modal ID and display it
      var modalId = text[index].replace(/\s+/g, '');
      document.getElementById(modalId).style.display = 'block';
      var modal = document.getElementById(modalId);

      //Clears the previous list of child nodes(aka graphs) so that they will not be redisplayed
      var closeButton = modal.querySelector('.close'); //copy the close button node
      while(modal.querySelector('.modal-content').firstChild) //while there are child nodes
      {
        modal.querySelector('.modal-content').removeChild(modal.querySelector('.modal-content').firstChild); //remove the first child node from the list
      }
      modal.querySelector('.modal-content').appendChild(closeButton); //reinsert the close button node into the modal

      // Create and append iframes
      var iframeUrls = fetchedURLS[index];
      iframeUrls.forEach(function(url, iframeIndex) {
        var iframe = document.createElement('iframe');
        iframe.className = "graph";
        iframe.src = url;
        // Calculate dimensions based on iframe index
        iframe.style.width = '100%';
        if (iframeIndex % 2 === 0) {
          // For even-indexed iframes
          iframe.style.height = '50vh';
        } else {
          // For odd-indexed iframes
          iframe.style.height = '10vh';
        }
        modal.querySelector('.modal-content').appendChild(iframe);
      });
      // Add event listener to modal close button
      closeButton = modal.querySelector('.close');
      closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
      });

      //scroll to the newly generated graphs by scrolling to the bottom of the map
      mapHeight = document.getElementById("map").offsetHeight; 
      scrollTo({
        top: mapHeight,
        left: 0,
        behavior: "smooth" //smooth scrolling
      });

    });
  })(i);
}
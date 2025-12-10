mapboxgl.accessToken = 'pk.eyJ1IjoiYWxleGlzMTMiLCJhIjoiY2xkeGk4bXpvMDJmeTNwbXV2bmpleGxxeCJ9.4PMbriYdSiVtIskoEwAsfw';
      const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/outdoors-v12',
        center: [-95.5, 47], // Centered between North and South Dakota
        zoom: 6,
        maxBounds: [
        [-112.0399, 42.000], // Southwest coordinates of North and South Dakota
        [-90.3084, 49.0014] // Northeast coordinates of North and South Dakota
        ],
      });
      



      function search() {
        const searchTerm = document.getElementById("search-input").value.toLowerCase();

        // Check the entered search term and redirect to the corresponding modal
        if (searchTerm === "big bend" || searchTerm === "big bend dam") {
          document.getElementById('Big Bend').style.display = 'block';
          var closeButton = modal.querySelector('.close');
          // Add a click event listener to the close button to close the modal
          closeButton.addEventListener('click', function() {
            modal.style.display = 'none';
          });
        } 
        
        else if (searchTerm === "oahe dam" || searchTerm === "oahe") {
          document.getElementById('Oahe').style.display = 'block';
        } 
        
        else if (searchTerm === "fort randal" || searchTerm === "fort randal dam") {
          document.getElementById('Fort Randall').style.display = 'block';
        } 
        
        else if (searchTerm === "gavins point" || searchTerm === "gavins point dam") {
          document.getElementById('Gavins Point').style.display = 'block';
        } 
        
        else if (searchTerm === "garrison" || searchTerm === "garrison dam") {
          document.getElementById('Garrison').style.display = 'block';
        } 
        
        else if (searchTerm === "fork peck" || searchTerm === "fork peck dam") {
          document.getElementById('Fort Peck').style.display = 'block';
        } 
        
        else if (searchTerm === "knife river" || searhTerm === "knife river at hazen nd") {
          document.getElementById('Hazen').style.display = 'block';
        } 
        else if (searchTerm === "stanton") {
        document.getElementById('Stanton').style.display = 'block';
        } 

        else if (searchTerm === "washburn") {
          document.getElementById('Washburn').style.display = 'block';
        } 

        else if (searchTerm === "price") {
          document.getElementById('Price').style.display = 'block';
        } 

        else if (searchTerm === "mandan") {
          document.getElementById('Mandan').style.display = 'block';
        } 

        else if (searchTerm === "bismarck") {
          document.getElementById('Bismarck').style.display = 'block';
        } 

        else if (searchTerm === "stark bridge near judson" || searchTerm === "judson") {
          document.getElementById('Judson').style.display = 'block';
        } 

        else if (searchTerm === "dannonball river at breien" || searchTerm === "breien") {
          document.getElementById('Breien').style.display = 'block';
        } 

        else if (searchTerm === "schmidt") {
          document.getElementById('Schmidt').style.display = 'block';
        } 

        else if (searchTerm === "grand river near cash" || searchTerm === "cash") {
          document.getElementById('Cash').style.display = 'block';
        } 

        else if (searchTerm === "oak creek at wakpala" || searchTerm === "oak creek" || searchTerm === "wakpala") {
          document.getElementById('Wakpala').style.display = 'block';
        } 

        else if (searchTerm === "moreau river near whitehorse" || searchTerm === "moreau river" || searchTerm === "whitehorse") {
          document.getElementById('Whitehorse').style.display = 'block';
        } 

        else if (searchTerm === "grand river near little eagle" || searchTerm === "little eagle") {
          document.getElementById('Little Eagle').style.display = 'block';
        } 

        else if (searchTerm === "fort yates" || searchTerm === "fort yates mesonet") {
          document.getElementById('Fort Yates').style.display = 'block';
        } 
        
        else if (searchTerm === "mott" || searchTerm === "mott mesonet") {
          document.getElementById('Mott').style.display = 'block';
        } 

        else if (searchTerm === "carson" || searchTerm === "carson mesonet") {
          document.getElementById('Carson').style.display = 'block';
        } 

        else if (searchTerm === "linton" || searchTerm === "linton mesonet") {
          document.getElementById('Linton').style.display = 'block';
        } 

        else if (searchTerm === "lemmon" || searchTerm === "lemmon mesonet") {
          document.getElementById('Lemmon').style.display = 'block';
        } 

        else if (searchTerm === "mcintosh" || searchTerm === "mcintosh mesonet") {
          document.getElementById('Mcintosh').style.display = 'block';
        } 

        else if (searchTerm === "mclaughlin" || searchTerm === "mclaughlin mesonet") {
          document.getElementById('Mclaughlin').style.display = 'block';
        } 

        else if (searchTerm === "mound city" || searchTerm === "mound city mesonet") {
          document.getElementById('Mound City').style.display = 'block';
        } 
        
        else if (searchTerm === "timber lake" || searchTerm === "timber lake mesonet") {
          document.getElementById('Timber Lake').style.display = 'block';
        } 

        else {
          alert("Search term not found");
        }
      }



      map.on('load', () => {
        map.addSource('points', {
          'type': 'geojson',
          'data': {
          'type': 'FeatureCollection',
          'features': [
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.4043407, 44.4512927]},
          'properties': {
          'title': 'Oahe Dam'
          ,'description': '<strong>Oahe Dam</strong><p>Super cool and useful information</p>'
        }},
        {
        'type': 'Feature',
        'geometry': {
        'type': 'Point',
        'coordinates': [-99.4545179, 44.0516567]},
        'properties': {
        'title': 'Big Bend Dam'
        ,'description': '<strong>Big Bend Dam</strong><p>Very informative and useful information</p>'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-98.5366157, 43.0661976]},
          'properties': {
          'title': 'Fort Randall Dam'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-97.4853, 42.8619]},
          'properties': {
          'title': 'Gavins Point Dam'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.4162492, 47.4949814]},
          'properties': {
          'title': 'Garrison Dam'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-106.4183359, 48.0027953]},
          'properties': {
          'title': 'Fork Peck Dam'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.6221093, 47.2852816]},
          'properties': {
          'title': 'Knife River at Hazen ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.3397222, 47.287222]},
          'properties': {
          'title': 'Missouri River Near Stanton ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.0379239, 47.2888822]},
          'properties': {
          'title': 'Missouri River at Washburn ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.9323594, 47.07971406]},
          'properties': {
          'title': 'Missouri River at Price ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.9745789, 46.8338827]},
          'properties': {
          'title': 'Heart River near Mandan ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.8213889, 46.81416667]},
          'properties': {
          'title': 'Missouri River at Bismarck'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.2136111, 46.7033333]},
          'properties': {
          'title': 'Heart River at Stark Bridge near Judson'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.93444, 46.3761111]},
          'properties': {
          'title': 'Cannonball River at Breien'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-102.6433259, 45.6486883]},
          'properties': {
          'title': 'NF Grand River near Cash SD'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.5593015, 45.7119422]},
          'properties': {
          'title': 'Oak Creek at Wakpala'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.8429214, 45.2558171]},
          'properties': {
          'title': 'Moreau River near Whitehorse SD'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.7391667, 46.65638889]},
          'properties': {
          'title': 'Missouri River at Schmidt ND'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-98.058, 42.74844444]},
          'properties': {
          'title': 'Grand River near Little Eagle SD'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.676495, 46.084858]},
          'properties': {
          'title': 'Fort Yates'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-102.322, 46.38]},
          'properties': {
          'title': 'Mott'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.373829, 46.44303]},
          'properties': {
          'title': 'Corson'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.277, 46.328]},
          'properties': {
          'title': 'Linton'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-102.11, 45.92]},
          'properties': {
          'title': 'Lemmon'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.34, 45.92]},
          'properties': {
          'title': 'McIntosh'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.78, 45.8]},
          'properties': {
          'title': 'Mclaughlin'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-100.11, 45.67]},
          'properties': {
          'title': 'Mound City'
        }},
        {
          'type': 'Feature',
          'geometry': {
          'type': 'Point',
          'coordinates': [-101.08, 45.42]},
          'properties': {
          'title': 'Timber Lake'
        }},

        ]
        }
        });
         
        // Add a symbol layer
        map.addLayer({
        'id': 'points',
        'type': 'symbol',
        'source': 'points',
        'layout': {
        'icon-image': 'custom-marker',
        // get the title name from the source's "title" property
        'text-field': ['get', 'title'],
        'text-font': ['Arial Unicode MS Bold'],
        'text-offset': [0, 0.75],
        'text-anchor': 'top',
        // "paint": {"color": "#808080"}        
      },

      
        });
        
        // Hover tooltips disabled
        /*
        const popup = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false
          });


        map.on('mouseenter', 'points', (e) => {
          
          // Change the cursor style as a UI indicator.
          map.getCanvas().style.cursor = 'pointer';
           
          // Copy coordinates array.
          const coordinates = e.features[0].geometry.coordinates.slice();
          const description = e.features[0].properties.description;
           
          // Ensure that if the map is zoomed out such that multiple
          // copies of the feature are visible, the popup appears
          // over the copy being pointed to.
          while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
          coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
          }
          //*/ 

          // Populate the popup and set its coordinates
          // based on the feature found.
          //popup.setLngLat(coordinates).setHTML(description).addTo(map);
          //});
           
        //map.on('mouseleave', 'points', () => {
          //map.getCanvas().style.cursor = '';
          //popup.remove();
          //});
        //*/

        }
        );
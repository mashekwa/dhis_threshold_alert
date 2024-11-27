<template>
    <div ref="mapContainer" class="map-container"></div>
  </template>
  
  <script setup>
  import { onMounted, watch, ref } from 'vue';
  import L from 'leaflet';
  
  const props = defineProps({
    geoData: Object,        // GeoJSON data for the map
    highlightFeatureId: String, // The ID to highlight (province or district)
    alertInfo: Array,       // Alert data for displaying popups
    autoZoom: Boolean,      // Whether to automatically zoom/pan
  });
  
  const mapContainer = ref(null);
  let mapInstance = null;
  let geoJsonLayer = null;
  
  // Function to style features based on alert data
  const styleFeature = (feature) => {
    const alertCount = feature.properties.alerts || 0;
    const alertColor = alertCount > 10 ? '#ff0000' : alertCount > 5 ? '#ff6666' : '#ffcccc';
    return {
      color: alertColor,
      weight: 2,
      fillOpacity: 0.7,
    };
  };
  
  // Function to highlight a feature on hover
  const highlightFeature = (e) => {
    const layer = e.target;
    layer.setStyle({
      weight: 5,
      color: '#666',
      fillOpacity: 0.9,
    });
  };
  
  // Function to reset highlight when hover ends
  const resetHighlight = (e) => {
    geoJsonLayer.resetStyle(e.target);
  };
  
  // Function to zoom to feature on click
  const zoomToFeature = (e) => {
    if (props.autoZoom && mapInstance) {
      mapInstance.fitBounds(e.target.getBounds());
    }
  };
  
  // Function to bind popups with alert information
  const onEachFeature = (feature, layer) => {
    layer.on({
      mouseover: highlightFeature,
      mouseout: resetHighlight,
      click: zoomToFeature,
    });
  
    // If alert information is available, show it in a popup
    if (feature.properties.alertInfo) {
      layer.bindPopup(
        `<strong>${feature.properties.name}</strong><br>Alerts: ${feature.properties.alerts}`
      );
    }
  };
  
  // Function to render the map with GeoJSON data
  const renderMap = () => {
    if (mapInstance) {
      mapInstance.remove(); // Remove previous instance if it exists
    }
  
    mapInstance = L.map(mapContainer.value).setView([0, 0], 2);
  
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(mapInstance);
  
    // Load GeoJSON data
    geoJsonLayer = L.geoJSON(props.geoData, {
      style: styleFeature,
      onEachFeature: onEachFeature,
    }).addTo(mapInstance);
  
    if (props.autoZoom) {
      mapInstance.fitBounds(geoJsonLayer.getBounds());
    }
  };
  
  onMounted(() => {
    renderMap();
  });
  
  watch(
    () => props.highlightFeatureId,
    (newId) => {
      // Add logic to highlight a feature by ID when it changes
      geoJsonLayer.eachLayer((layer) => {
        const feature = layer.feature;
        if (feature.properties.id === newId) {
          layer.setStyle({ weight: 3, color: '#0000ff' }); // Highlight style
          if (props.autoZoom) {
            mapInstance.fitBounds(layer.getBounds());
          }
        } else {
          geoJsonLayer.resetStyle(layer);
        }
      });
    }
  );
  </script>
  
  <style scoped>
  .map-container {
    height: 400px; /* Adjust as needed */
    width: 100%;
    margin-bottom: 1rem;
  }
  </style>
  
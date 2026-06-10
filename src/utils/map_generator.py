import folium
from folium.plugins import HeatMap, MiniMap, Geocoder

def generate_dashboard_map(incidents, resources, show_heatmap=True, show_resources=True, show_incidents=True) -> str:
    """Generate the main dashboard map with clustering and heatmap layers."""
    # Base map centered on Ghana
    m = folium.Map(location=[7.9465, -1.0232], zoom_start=7, tiles='OpenStreetMap')
    
    # Severity color mapping
    severity_colors = {
        'critical': '#E74C3C',
        'high': '#F39C12',
        'medium': '#3498DB',
        'low': '#27AE60'
    }
    
    # Optional Heatmap layer
    if show_heatmap and incidents:
        heat_data = []
        for inc in incidents:
            if 'location' in inc and 'lat' in inc['location'] and 'lng' in inc['location']:
                heat_data.append([inc['location']['lat'], inc['location']['lng']])
        
        if heat_data:
            HeatMap(
                heat_data, 
                name='Incident Heatmap',
                gradient={0.4: 'blue', 0.65: 'lime', 1: 'red'}
            ).add_to(m)

    # Incident Markers
    if show_incidents and incidents:
        incident_group = folium.FeatureGroup(name="Incidents")
        for inc in incidents:
            if 'location' not in inc or 'lat' not in inc['location'] or 'lng' not in inc['location']:
                continue
                
            severity = inc.get('severity', 'low').lower()
            color = severity_colors.get(severity, '#27AE60')
            
            # HTML Popup
            popup_html = f"""
            <div style="width:200px">
                <h4 style="margin-top:0">{inc.get('title', 'Unknown Incident')}</h4>
                <table style="width:100%">
                    <tr><td><b>Type:</b></td><td>{inc.get('type', 'Unknown')}</td></tr>
                    <tr><td><b>Severity:</b></td><td>{inc.get('severity', 'Unknown')}</td></tr>
                    <tr><td><b>Status:</b></td><td>{inc.get('status', 'Unknown')}</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[inc['location']['lat'], inc['location']['lng']],
                radius=10,
                color=color,
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=inc.get('title', 'Incident'),
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(incident_group)
        incident_group.add_to(m)

    # Resource Markers
    if show_resources and resources:
        resource_group = folium.FeatureGroup(name="Resources")
        for res in resources:
            if 'location' not in res or 'lat' not in res['location'] or 'lng' not in res['location']:
                continue
                
            status_colors = {
                'available': '#27AE60',
                'deployed': '#F39C12',
                'maintenance': '#E74C3C',
                'reserved': '#8B9DC3'
            }
            status = res.get('status', 'available').lower()
            color = status_colors.get(status, '#3498DB')
            
            # Custom DivIcon (Blue square, or colored by status)
            icon_html = f"""
            <div style="background-color: {color}; width: 20px; height: 20px; border-radius: 4px; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);">
            </div>
            """
            
            popup_html = f"""
            <div style="width:200px">
                <h4 style="margin-top:0">{res.get('name', 'Unknown Resource')}</h4>
                <table style="width:100%">
                    <tr><td><b>Type:</b></td><td>{res.get('type', 'Unknown')}</td></tr>
                    <tr><td><b>Status:</b></td><td>{res.get('status', 'Unknown')}</td></tr>
                    <tr><td><b>Capacity:</b></td><td>{res.get('capacity', 'N/A')}</td></tr>
                </table>
            </div>
            """
            
            folium.Marker(
                location=[res['location']['lat'], res['location']['lng']],
                icon=folium.DivIcon(html=icon_html, icon_size=(20, 20), icon_anchor=(10, 10)),
                tooltip=res.get('name', 'Resource'),
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(resource_group)
        resource_group.add_to(m)

    # MiniMap
    MiniMap(toggle_display=True, position='bottomright').add_to(m)
    
    # Layer Control
    folium.LayerControl().add_to(m)
    
    # Geocoder Search Bar (add_marker=False is required for custom zoom to work)
    Geocoder(position='topright', add_marker=False, zoom=18).add_to(m)
    
    return m.get_root().render()

def generate_incident_location_thumbnail(lat: float, lng: float, title: str) -> str:
    """Generate a small 280x160 map centered on the incident."""
    m = folium.Map(location=[lat, lng], zoom_start=13, tiles='OpenStreetMap', zoom_control=False)
    
    folium.Marker(
        location=[lat, lng],
        tooltip=title,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    return m.get_root().render()

def generate_location_picker_map(initial_lat=7.9465, initial_lng=-1.0232) -> str:
    """Generate a map for selecting a location with a click, using a JS callback."""
    m = folium.Map(location=[initial_lat, initial_lng], zoom_start=7, tiles='OpenStreetMap')
    
    # Add Search Bar for Landmarks
    Geocoder(position='topright', add_marker=False, zoom=18).add_to(m)
    
    map_var = m.get_name()
    
    # Add JS script to capture clicks and store in hidden div
    click_js = f"""
    <div id="selected_coordinates" style="display:none;"></div>
    <script>
        function initMapClick() {{
            if (typeof {map_var} !== 'undefined') {{
                var selected_marker_{map_var} = null;
                {map_var}.on('click', function(e) {{
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;
                    
                    document.getElementById('selected_coordinates').innerText = lat + ',' + lng;
                    
                    if (selected_marker_{map_var}) {{
                        {map_var}.removeLayer(selected_marker_{map_var});
                    }}
                    
                    selected_marker_{map_var} = L.marker([lat, lng]).addTo({map_var});
                }});
            }} else {{
                setTimeout(initMapClick, 100);
            }}
        }}
        initMapClick();
    </script>
    """
    
    m.get_root().html.add_child(folium.Element(click_js))
    
    return m.get_root().render()

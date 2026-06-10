# pyrefly: ignore [missing-import]
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB using environment variable
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGODB_URI)
db = client['disasterconnect']


def clear_existing_data():
    """Delete all existing records from incidents and resources collections"""
    db.incidents.delete_many({})
    db.resources.delete_many({})
    print("Existing records deleted successfully")


def generate_dummy_incidents():
    """Generate dummy incident data with Ghanaian locations"""

    # Ghanaian cities/regions with precise coordinates
    # MongoDB stores coordinates as [longitude, latitude]
    locations = [
        {"area": "Accra, Greater Accra Region",     "coords": [-0.1869, 5.6037],  "lat": 5.6037,  "lng": -0.1869},
        {"area": "Kumasi, Ashanti Region",           "coords": [-1.6236, 6.6885],  "lat": 6.6885,  "lng": -1.6236},
        {"area": "Tamale, Northern Region",          "coords": [-0.8393, 9.4008],  "lat": 9.4008,  "lng": -0.8393},
        {"area": "Cape Coast, Central Region",       "coords": [-1.2466, 5.1053],  "lat": 5.1053,  "lng": -1.2466},
        {"area": "Takoradi, Western Region",         "coords": [-1.7557, 4.8845],  "lat": 4.8845,  "lng": -1.7557},
        {"area": "Sunyani, Bono Region",             "coords": [-2.3279, 7.3349],  "lat": 7.3349,  "lng": -2.3279},
        {"area": "Wa, Upper West Region",            "coords": [-2.4987, 10.0607], "lat": 10.0607, "lng": -2.4987},
        {"area": "Bolgatanga, Upper East Region",    "coords": [-0.8530, 10.7869], "lat": 10.7869, "lng": -0.8530},
        {"area": "Ho, Volta Region",                 "coords": [0.4726,  6.6012],  "lat": 6.6012,  "lng": 0.4726 },
        {"area": "Koforidua, Eastern Region",        "coords": [-0.2584, 6.0938],  "lat": 6.0938,  "lng": -0.2584},
    ]

    incident_types = [
        "Flood", "Earthquake", "Fire", "Landslide", "Industrial Accident",
        "Building Collapse", "Gas Leak", "Chemical Spill"
    ]
    severity_levels = ["High", "Medium", "Low", "Critical"]
    status_options = ["Active", "Resolved", "In Progress", "Under Review"]

    incidents = []
    for _ in range(20):  # Generate 20 incidents
        location = random.choice(locations)
        created_at = datetime.now() - timedelta(days=random.randint(0, 30))
        incident_type = random.choice(incident_types)

        incident = {
            "title": f"{incident_type} in {location['area']}",
            "type": incident_type,
            "severity": random.choice(severity_levels),
            "status": random.choice(status_options),
            "location": {
                "type": "Point",
                "coordinates": location["coords"],
                "area": location["area"],
                "description": f"Incident reported in {location['area']}",
                "lat": location["lat"],
                "lng": location["lng"],
            },
            "description": f"Emergency situation reported in {location['area']}",
            "created_at": created_at,
        }
        incidents.append(incident)

    db.incidents.insert_many(incidents)
    print(f"{len(incidents)} incidents inserted successfully")


def generate_dummy_resources():
    """Generate dummy resource data staged at Ghanaian hospitals/facilities"""

    # Ghanaian hospital / emergency staging locations
    locations = [
        {"area": "37 Military Hospital, Accra",                  "coords": [-0.1941, 5.5820],  "lat": 5.5820,  "lng": -0.1941},
        {"area": "Komfo Anokye Teaching Hospital, Kumasi",        "coords": [-1.6176, 6.6958],  "lat": 6.6958,  "lng": -1.6176},
        {"area": "Tamale Teaching Hospital",                      "coords": [-0.8337, 9.4149],  "lat": 9.4149,  "lng": -0.8337},
        {"area": "Cape Coast Teaching Hospital",                  "coords": [-1.2399, 5.1106],  "lat": 5.1106,  "lng": -1.2399},
        {"area": "Effia Nkwanta Regional Hospital, Takoradi",     "coords": [-1.7493, 4.9002],  "lat": 4.9002,  "lng": -1.7493},
        {"area": "Sunyani Regional Hospital",                     "coords": [-2.3258, 7.3290],  "lat": 7.3290,  "lng": -2.3258},
        {"area": "Wa Regional Hospital",                          "coords": [-2.5016, 10.0619], "lat": 10.0619, "lng": -2.5016},
        {"area": "Bolgatanga Regional Hospital",                  "coords": [-0.8432, 10.7927], "lat": 10.7927, "lng": -0.8432},
        {"area": "Ho Teaching Hospital",                          "coords": [0.4778,  6.6029],  "lat": 6.6029,  "lng": 0.4778 },
        {"area": "St Joseph Hospital, Koforidua",                 "coords": [-0.2604, 6.0903],  "lat": 6.0903,  "lng": -0.2604},
    ]

    resource_types = {
        "Ambulance":               {"capacity": [2, 4]},
        "Fire Truck":              {"capacity": [6, 8]},
        "Rescue Vehicle":          {"capacity": [4, 6]},
        "Medical Supply Unit":     {"capacity": [100, 500]},
        "Emergency Response Team": {"capacity": [5, 15]},
        "Mobile Hospital":         {"capacity": [20, 50]},
        "Water Tanker":            {"capacity": [1000, 5000]},
        "Relief Supplies Vehicle": {"capacity": [200, 1000]},
    }

    status_options = ["Available", "Deployed", "Maintenance", "Reserved"]

    resources = []
    for _ in range(30):  # Generate 30 resources
        location = random.choice(locations)
        resource_type = random.choice(list(resource_types.keys()))
        capacity_range = resource_types[resource_type]["capacity"]

        resource = {
            "name": f"{resource_type}-{random.randint(100, 999)}",
            "type": resource_type,
            "status": random.choice(status_options),
            "capacity": random.randint(capacity_range[0], capacity_range[1]),
            "location": {
                "type": "Point",
                "coordinates": location["coords"],
                "area": location["area"],
                "description": f"Stationed at {location['area']}",
                "lat": location["lat"],
                "lng": location["lng"],
            },
            "created_at": datetime.now() - timedelta(days=random.randint(0, 60)),
        }
        resources.append(resource)

    db.resources.insert_many(resources)
    print(f"{len(resources)} resources inserted successfully")


if __name__ == "__main__":
    try:
        clear_existing_data()
        generate_dummy_incidents()
        generate_dummy_resources()
        print("Dummy data insertion completed successfully!")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        client.close()

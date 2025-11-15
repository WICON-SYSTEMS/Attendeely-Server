"""
Geofence utilities using Haversine formula for distance calculation
"""
import math
from decimal import Decimal
from typing import Optional


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
    
    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000  # meters
    
    # Distance in meters
    distance = c * r
    
    return distance


def is_within_geofence(
    center_lat: float,
    center_lon: float,
    radius_meters: float,
    check_lat: float,
    check_lon: float
) -> bool:
    """
    Check if a point is within the geofence radius.
    
    Args:
        center_lat: Center latitude of geofence
        center_lon: Center longitude of geofence
        radius_meters: Radius of geofence in meters
        check_lat: Latitude to check
        check_lon: Longitude to check
    
    Returns:
        True if point is within geofence, False otherwise
    """
    distance = haversine_distance(center_lat, center_lon, check_lat, check_lon)
    return distance <= radius_meters


def get_distance_from_geofence(
    center_lat: float,
    center_lon: float,
    check_lat: float,
    check_lon: float
) -> float:
    """
    Get the distance from a point to the geofence center.
    
    Args:
        center_lat: Center latitude of geofence
        center_lon: Center longitude of geofence
        check_lat: Latitude to check
        check_lon: Longitude to check
    
    Returns:
        Distance in meters
    """
    return haversine_distance(center_lat, center_lon, check_lat, check_lon)


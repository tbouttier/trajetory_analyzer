"""
KML Parser for trajectory analysis.
Extracts coordinates and altitudes from KML files using lxml.
"""

from lxml import etree
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import re


class KMLParser:
    """Parser for KML files containing aircraft trajectories."""
    
    KML_NS = 'http://www.opengis.net/kml/2.2'
    
    def __init__(self, kml_file: str):
        """
        Initialize parser with KML file path.
        
        Args:
            kml_file: Path to the KML file
        """
        self.kml_file = kml_file
        self.trajectory = None
        self.name = None
    
    def parse(self) -> pd.DataFrame:
        """
        Parse KML file and extract trajectory data.
        
        Returns:
            DataFrame with columns: timestamp, latitude, longitude, altitude, name
        """
        tree = etree.parse(self.kml_file)
        root = tree.getroot()
        
        ns = {'kml': self.KML_NS}
        
        # Find all Placemark elements
        placemarks = root.findall('.//kml:Placemark', ns)
        
        if not placemarks:
            # Try without namespace
            placemarks = root.findall('.//Placemark')
        
        trajectory_data = []
        
        for placemark in placemarks:
            # Get name
            name_elem = placemark.find('kml:name', ns)
            if name_elem is None:
                name_elem = placemark.find('name')
            name = name_elem.text if name_elem is not None else "Unknown"
            
            # Get timestamp
            timestamp = None
            time_elem = placemark.find('kml:TimeStamp/kml:when', ns)
            if time_elem is None:
                time_elem = placemark.find('TimeStamp/when')
            if time_elem is not None:
                timestamp = time_elem.text
            
            # Extract coordinates from LineString
            linestring = placemark.find('kml:LineString', ns)
            if linestring is None:
                linestring = placemark.find('LineString')
            
            if linestring is not None:
                coords_text = self._get_coords_text(linestring, ns)
                if coords_text:
                    coords = self._parse_coordinates(coords_text)
                    for coord in coords:
                        trajectory_data.append({
                            'timestamp': timestamp,
                            'latitude': coord[1],
                            'longitude': coord[0],
                            'altitude': coord[2] if len(coord) > 2 else None,
                            'name': name
                        })
            
            # Extract coordinates from Point
            point = placemark.find('kml:Point', ns)
            if point is None:
                point = placemark.find('Point')
            
            if point is not None:
                coords_text = self._get_coords_text(point, ns)
                if coords_text:
                    coords = self._parse_coordinates(coords_text)
                    if coords:
                        coord = coords[0]
                        trajectory_data.append({
                            'timestamp': timestamp,
                            'latitude': coord[1],
                            'longitude': coord[0],
                            'altitude': coord[2] if len(coord) > 2 else None,
                            'name': name
                        })
            
            # Extract coordinates from MultiGeometry
            multigeom = placemark.find('kml:MultiGeometry', ns)
            if multigeom is None:
                multigeom = placemark.find('MultiGeometry')
            
            if multigeom is not None:
                for child in multigeom:
                    if child.tag.endswith('LineString') or child.tag.endswith('Point'):
                        coords_text = self._get_coords_text(child, ns)
                        if coords_text:
                            coords = self._parse_coordinates(coords_text)
                            for coord in coords:
                                trajectory_data.append({
                                    'timestamp': timestamp,
                                    'latitude': coord[1],
                                    'longitude': coord[0],
                                    'altitude': coord[2] if len(coord) > 2 else None,
                                    'name': name
                                })
        
        if not trajectory_data:
            raise ValueError(f"No trajectory data found in {self.kml_file}")
        
        self.trajectory = pd.DataFrame(trajectory_data)
        self.name = self.trajectory['name'].iloc[0] if len(self.trajectory) > 0 else None
        
        return self.trajectory
    
    def _get_coords_text(self, element, ns: Dict) -> Optional[str]:
        """Extract coordinates text from element."""
        coords_elem = element.find('kml:coordinates', ns)
        if coords_elem is None:
            coords_elem = element.find('coordinates')
        
        if coords_elem is not None and coords_elem.text:
            return coords_elem.text.strip()
        return None
    
    def _parse_coordinates(self, coords_text: str) -> List[Tuple[float, float, float]]:
        """
        Parse coordinates text into list of (lon, lat, alt) tuples.
        
        Args:
            coords_text: Text like "lon,lat,alt lon,lat,alt ..."
            
        Returns:
            List of coordinate tuples
        """
        coords = []
        
        # Remove extra whitespace
        coords_text = re.sub(r'\s+', ' ', coords_text).strip()
        
        # Split by whitespace and parse each coordinate
        for coord_str in coords_text.split():
            parts = coord_str.split(',')
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else 0.0
                coords.append((lon, lat, alt))
        
        return coords
    
    def get_trajectory_array(self) -> np.ndarray:
        """
        Get trajectory as numpy array (N x 3: lon, lat, alt).
        
        Returns:
            Numpy array of shape (N, 3)
        """
        if self.trajectory is None:
            self.parse()
        
        return self.trajectory[['longitude', 'latitude', 'altitude']].values
    
    def get_2d_coordinates(self) -> np.ndarray:
        """
        Get 2D coordinates (latitude, longitude).
        
        Returns:
            Numpy array of shape (N, 2)
        """
        if self.trajectory is None:
            self.parse()
        
        return self.trajectory[['latitude', 'longitude']].values


def parse_kml_files(kml_files: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Parse multiple KML files.
    
    Args:
        kml_files: List of KML file paths
        
    Returns:
        Dictionary mapping file names to trajectory DataFrames
    """
    trajectories = {}
    
    for kml_file in kml_files:
        parser = KMLParser(kml_file)
        df = parser.parse()
        trajectories[kml_file] = df
    
    return trajectories

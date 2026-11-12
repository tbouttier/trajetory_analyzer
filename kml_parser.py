"""
KML Parser for trajectory analysis.
Extracts coordinates and altitudes from KML files using lxml.
Supports LineString, Point, MultiGeometry, and gx:Track elements.
"""

from lxml import etree
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import re


class KMLParser:
    """Parser for KML files containing aircraft trajectories."""
    
    KML_NS = 'http://www.opengis.net/kml/2.2'
    KML_NS_GOOGLE = 'http://earth.google.com/kml/2.0'
    GX_NS = 'http://www.google.com/kml/ext/2.2'
    
    def __init__(self, kml_file: str):
        """
        Initialize parser with KML file path.
        
        Args:
            kml_file: Path to the KML file
        """
        self.kml_file = kml_file
        self.trajectory = None
        self.name = None
    
    def _find_element(self, parent, local_name: str, namespaces: List[Dict]) -> Optional[etree.Element]:
        """Find element trying multiple namespaces."""
        for ns in namespaces:
            elem = parent.find(f'{{{ns.get("kml", "")}}}{local_name}' if "kml" in ns else local_name)
            if elem is not None:
                return elem
        # Try without namespace
        elem = parent.find(local_name)
        if elem is not None:
            return elem
        # Try with any namespace
        elem = parent.find(f'.//*{local_name}')
        return elem
    
    def _find_elements(self, parent, local_name: str, namespaces: List[Dict]) -> List[etree.Element]:
        """Find all elements trying multiple namespaces."""
        all_elems = []
        for ns in namespaces:
            elems = parent.findall(f'.//{{{ns.get("kml", "")}}}{local_name}' if "kml" in ns else f'.//{local_name}')
            all_elems.extend(elems)
        # Try without namespace
        elems = parent.findall(f'.//{local_name}')
        all_elems.extend(elems)
        # Remove duplicates
        return list(dict.fromkeys(all_elems))
    
    def parse(self) -> pd.DataFrame:
        """
        Parse KML file and extract trajectory data.
        
        Returns:
            DataFrame with columns: timestamp, latitude, longitude, altitude, name
        """
        tree = etree.parse(self.kml_file)
        root = tree.getroot()
        
        # Define namespaces to try
        namespaces = [
            {'kml': self.KML_NS, 'gx': self.GX_NS},
            {'kml': self.KML_NS_GOOGLE, 'gx': self.GX_NS},
            {}
        ]
        
        # Find all Placemark elements
        placemarks = []
        for ns in namespaces:
            if 'kml' in ns:
                placemarks = root.findall(f'.//{{{ns["kml"]}}}Placemark')
                if placemarks:
                    break
        if not placemarks:
            placemarks = root.findall('.//Placemark')
        
        trajectory_data = []
        
        for placemark in placemarks:
            # Get name
            name = "Unknown"
            for ns in namespaces:
                if 'kml' in ns:
                    name_elem = placemark.find(f'{{{ns["kml"]}}}name')
                else:
                    name_elem = placemark.find('name')
                if name_elem is not None and name_elem.text:
                    name = name_elem.text
                    break
            
            # Try to parse gx:Track first (has individual timestamps per point)
            gx_track = None
            for ns in namespaces:
                if 'gx' in ns:
                    gx_track = placemark.find(f'.//{{{ns["gx"]}}}Track')
                else:
                    gx_track = placemark.find('.//Track')
                if gx_track is not None:
                    break
            
            if gx_track is not None:
                # Parse gx:Track with individual <when> and <gx:coord> elements
                coords = self._parse_gx_track(gx_track, namespaces)
                timestamps = self._parse_gx_track_timestamps(gx_track, namespaces)
                
                for i, coord in enumerate(coords):
                    timestamp = timestamps[i] if i < len(timestamps) else None
                    trajectory_data.append({
                        'timestamp': timestamp,
                        'latitude': coord[1],
                        'longitude': coord[0],
                        'altitude': coord[2] if len(coord) > 2 else None,
                        'name': name
                    })
                continue
            
            # Get timestamp (for LineString/Point)
            timestamp = None
            for ns in namespaces:
                if 'kml' in ns:
                    time_elem = placemark.find(f'{{{ns["kml"]}}}TimeStamp/{{{ns["kml"]}}}when')
                else:
                    time_elem = placemark.find('TimeStamp/when')
                if time_elem is not None and time_elem.text:
                    timestamp = time_elem.text
                    break
            
            # Extract coordinates from LineString
            linestring = None
            for ns in namespaces:
                if 'kml' in ns:
                    linestring = placemark.find(f'{{{ns["kml"]}}}LineString')
                else:
                    linestring = placemark.find('LineString')
                if linestring is not None:
                    break
            
            if linestring is not None:
                coords_text = self._get_coords_text(linestring, namespaces)
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
                continue
            
            # Extract coordinates from Point
            point = None
            for ns in namespaces:
                if 'kml' in ns:
                    point = placemark.find(f'{{{ns["kml"]}}}Point')
                else:
                    point = placemark.find('Point')
                if point is not None:
                    break
            
            if point is not None:
                coords_text = self._get_coords_text(point, namespaces)
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
                continue
            
            # Extract coordinates from MultiGeometry
            multigeom = None
            for ns in namespaces:
                if 'kml' in ns:
                    multigeom = placemark.find(f'{{{ns["kml"]}}}MultiGeometry')
                else:
                    multigeom = placemark.find('MultiGeometry')
                if multigeom is not None:
                    break
            
            if multigeom is not None:
                for child in multigeom:
                    coords_text = self._get_coords_text(child, namespaces)
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
    
    def _parse_gx_track(self, gx_track, namespaces: List[Dict]) -> List[Tuple[float, float, float]]:
        """
        Parse gx:Track element to extract coordinates.
        
        Args:
            gx_track: The gx:Track element
            namespaces: List of namespace dictionaries
            
        Returns:
            List of (lon, lat, alt) tuples
        """
        coords = []
        
        # Find all gx:coord elements
        gx_coords = []
        for ns in namespaces:
            if 'gx' in ns:
                gx_coords = gx_track.findall(f'.//{{{ns["gx"]}}}coord')
            else:
                gx_coords = gx_track.findall('.//coord')
            if gx_coords:
                break
        
        for gx_coord in gx_coords:
            if gx_coord.text:
                parts = gx_coord.text.strip().split()
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    alt = float(parts[2]) if len(parts) > 2 else 0.0
                    coords.append((lon, lat, alt))
        
        return coords
    
    def _parse_gx_track_timestamps(self, gx_track, namespaces: List[Dict]) -> List[str]:
        """
        Parse gx:Track element to extract timestamps.
        
        Args:
            gx_track: The gx:Track element
            namespaces: List of namespace dictionaries
            
        Returns:
            List of timestamp strings
        """
        timestamps = []
        
        # Find all when elements
        when_elems = []
        for ns in namespaces:
            if 'kml' in ns:
                when_elems = gx_track.findall(f'.//{{{ns["kml"]}}}when')
            else:
                when_elems = gx_track.findall('.//when')
            if when_elems:
                break
        
        for when_elem in when_elems:
            if when_elem.text:
                timestamps.append(when_elem.text.strip())
        
        return timestamps
    
    def _get_coords_text(self, element, namespaces: List[Dict]) -> Optional[str]:
        """Extract coordinates text from element."""
        coords_elem = None
        for ns in namespaces:
            if 'kml' in ns:
                coords_elem = element.find(f'{{{ns["kml"]}}}coordinates')
            else:
                coords_elem = element.find('coordinates')
            if coords_elem is not None and coords_elem.text:
                return coords_elem.text.strip()
        
        # Try without namespace
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
        
        # Remove extra whitespace and newlines
        coords_text = re.sub(r'[\r\n\s]+', ' ', coords_text).strip()
        
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

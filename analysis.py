"""
Trajectory analysis module.
Calculates deviations between two trajectories.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
from scipy.spatial.distance import euclidean


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    
    Args:
        lon1, lat1: Longitude and latitude of point 1
        lon2, lat2: Longitude and latitude of point 2
        
    Returns:
        Distance in meters
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Radius of earth in kilometers is 6371
    distance_m = 6371000 * c
    return distance_m


def calculate_lateral_deviation(
    traj1_coords: np.ndarray,
    traj2_coords: np.ndarray
) -> np.ndarray:
    """
    Calculate lateral (2D) deviation between two trajectories.
    
    Uses point-to-point comparison assuming same number of points.
    For trajectories with different number of points, use interpolation.
    
    Args:
        traj1_coords: Array of shape (N, 2) - (lat, lon) or (lon, lat)
        traj2_coords: Array of shape (N, 2) - (lat, lon) or (lon, lat)
        
    Returns:
        Array of lateral distances in meters
    """
    if traj1_coords.shape != traj2_coords.shape:
        raise ValueError("Trajectories must have the same shape for direct comparison")
    
    deviations = []
    for i in range(len(traj1_coords)):
        lon1, lat1 = traj1_coords[i, 0], traj1_coords[i, 1]
        lon2, lat2 = traj2_coords[i, 0], traj2_coords[i, 1]
        dist = haversine_distance(lon1, lat1, lon2, lat2)
        deviations.append(dist)
    
    return np.array(deviations)


def calculate_vertical_deviation(
    traj1_altitudes: np.ndarray,
    traj2_altitudes: np.ndarray
) -> np.ndarray:
    """
    Calculate vertical (altitude) deviation between two trajectories.
    
    Args:
        traj1_altitudes: Array of altitudes from trajectory 1
        traj2_altitudes: Array of altitudes from trajectory 2
        
    Returns:
        Array of altitude differences in meters
    """
    if traj1_altitudes.shape != traj2_altitudes.shape:
        raise ValueError("Altitude arrays must have the same shape")
    
    # Handle None values
    traj1_altitudes = np.where(pd.isna(traj1_altitudes), 0, traj1_altitudes)
    traj2_altitudes = np.where(pd.isna(traj2_altitudes), 0, traj2_altitudes)
    
    return np.abs(traj1_altitudes - traj2_altitudes)


def resample_trajectory(
    traj_coords: np.ndarray,
    target_length: int
) -> np.ndarray:
    """
    Resample trajectory to target number of points using linear interpolation.
    
    Args:
        traj_coords: Array of shape (N, 3) - (lon, lat, alt)
        target_length: Target number of points
        
    Returns:
        Resampled array of shape (target_length, 3)
    """
    if len(traj_coords) == target_length:
        return traj_coords
    
    # Create parameter space
    t_old = np.linspace(0, 1, len(traj_coords))
    t_new = np.linspace(0, 1, target_length)
    
    # Interpolate each coordinate
    resampled = np.zeros((target_length, 3))
    for i in range(3):
        resampled[:, i] = np.interp(t_new, t_old, traj_coords[:, i])
    
    return resampled



def align_by_bidirectional(
    traj1: np.ndarray,
    traj2: np.ndarray,
    max_distance_deg: float = 0.01
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align trajectories by finding bidirectional nearest neighbors.
    Only keeps points that are mutual nearest neighbors within a distance threshold.
    
    Args:
        traj1: Reference trajectory (lon, lat, alt)
        traj2: Trajectory to align
        max_distance_deg: Maximum distance in degrees for considering a match
        
    Returns:
        Tuple of (aligned_traj1, aligned_traj2) containing only mutual matches
    """
    aligned_traj1 = []
    aligned_traj2 = []
    
    # For each point in traj1, find closest in traj2
    for i, point1 in enumerate(traj1):
        min_dist = float('inf')
        closest_idx_in_traj2 = -1
        
        for j, point2 in enumerate(traj2):
            dist = np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_idx_in_traj2 = j
        
        # For the closest point in traj2, check if its closest in traj1 is the original point
        if closest_idx_in_traj2 >= 0:
            # Find closest in traj1 for this traj2 point
            min_dist_back = float('inf')
            closest_idx_in_traj1 = -1
            
            for k, point1_back in enumerate(traj1):
                dist = np.sqrt((traj2[closest_idx_in_traj2][0] - point1_back[0])**2 + 
                               (traj2[closest_idx_in_traj2][1] - point1_back[1])**2)
                if dist < min_dist_back:
                    min_dist_back = dist
                    closest_idx_in_traj1 = k
            
            # If mutual match and within distance threshold
            if closest_idx_in_traj1 == i and min_dist <= max_distance_deg:
                aligned_traj1.append(point1)
                aligned_traj2.append(traj2[closest_idx_in_traj2])
    
    return np.array(aligned_traj1), np.array(aligned_traj2)


def align_trajectories(
    traj1: np.ndarray,
    traj2: np.ndarray,
    method: str = 'nearest'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align two trajectories to the same number of points.
    
    Args:
        traj1: Array of shape (N, 3) - (lon, lat, alt)
        traj2: Array of shape (M, 3) - (lon, lat, alt)
        method: Alignment method - 'interpolation' or 'nearest'
        
    Returns:
        Tuple of aligned arrays with same length
    """
    if method == 'nearest':
        # Find nearest neighbor alignment
        # For each point in traj1, find the closest point in traj2
        aligned_traj1, aligned_traj2 = align_by_nearest(traj1, traj2)
    elif method == 'bidirectional':
        # Find bidirectional matches (mutual nearest neighbors)
        aligned_traj1, aligned_traj2 = align_by_bidirectional(traj1, traj2)
    else:
        # Default: interpolation
        min_length = min(len(traj1), len(traj2))
        
        if len(traj1) != min_length:
            traj1 = resample_trajectory(traj1, min_length)
        
        if len(traj2) != min_length:
            traj2 = resample_trajectory(traj2, min_length)
        
        aligned_traj1, aligned_traj2 = traj1, traj2
    
    return aligned_traj1, aligned_traj2


def align_by_nearest(
    traj1: np.ndarray,
    traj2: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Align trajectories by finding nearest neighbors.
    For each point in traj1, find the closest point in traj2.
    
    Args:
        traj1: Reference trajectory (lon, lat, alt)
        traj2: Trajectory to align
        
    Returns:
        Tuple of (aligned_traj1, aligned_traj2) where aligned_traj2 contains
        the nearest points from traj2 for each point in traj1
    """
    aligned_traj1 = []
    aligned_traj2 = []
    
    for point1 in traj1:
        # Find the closest point in traj2
        min_dist = float('inf')
        closest_point = None
        
        for point2 in traj2:
            # Calculate 2D distance (lon, lat) in degrees
            dist = np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_point = point2
        
        if closest_point is not None:
            aligned_traj1.append(point1)
            aligned_traj2.append(closest_point)
    
    return np.array(aligned_traj1), np.array(aligned_traj2)


class TrajectoryAnalyzer:
    """Analyzer for comparing two trajectories."""
    
    def __init__(self, traj1: pd.DataFrame, traj2: pd.DataFrame, alignment_method: str = 'nearest'):
        """
        Initialize analyzer with two trajectory DataFrames.
        
        Args:
            traj1: First trajectory DataFrame (reference)
            traj2: Second trajectory DataFrame
            alignment_method: Method for aligning trajectories - 'interpolation' or 'nearest'
        """
        self.traj1 = traj1
        self.traj2 = traj2
        self.alignment_method = alignment_method
        self.traj1_name = traj1['name'].iloc[0] if 'name' in traj1.columns else "Trajectory 1"
        self.traj2_name = traj2['name'].iloc[0] if 'name' in traj2.columns else "Trajectory 2"
    
    def analyze(self) -> Dict:
        """
        Perform complete analysis of trajectory deviations.
        
        Returns:
            Dictionary with analysis results
        """
        # Extract coordinates and altitudes
        coords1 = self.traj1[['longitude', 'latitude']].values
        coords2 = self.traj2[['longitude', 'latitude']].values
        alts1 = self.traj1['altitude'].values
        alts2 = self.traj2['altitude'].values
        
        # Align trajectories
        full_traj1 = self.traj1[['longitude', 'latitude', 'altitude']].values
        full_traj2 = self.traj2[['longitude', 'latitude', 'altitude']].values
        
        aligned_traj1, aligned_traj2 = align_trajectories(full_traj1, full_traj2, method=self.alignment_method)
        
        # Calculate deviations
        lateral_dev = calculate_lateral_deviation(
            aligned_traj1[:, :2], 
            aligned_traj2[:, :2]
        )
        vertical_dev = calculate_vertical_deviation(
            aligned_traj1[:, 2], 
            aligned_traj2[:, 2]
        )
        
        # Calculate statistics
        results = {
            'trajectory_1': self.traj1_name,
            'trajectory_2': self.traj2_name,
            'lateral_deviations': lateral_dev,
            'vertical_deviations': vertical_dev,
            'mean_lateral_deviation': np.mean(lateral_dev),
            'max_lateral_deviation': np.max(lateral_dev),
            'min_lateral_deviation': np.min(lateral_dev),
            'std_lateral_deviation': np.std(lateral_dev),
            'mean_vertical_deviation': np.mean(vertical_dev),
            'max_vertical_deviation': np.max(vertical_dev),
            'min_vertical_deviation': np.min(vertical_dev),
            'std_vertical_deviation': np.std(vertical_dev),
            'num_points': len(lateral_dev),
            'aligned_trajectory_1': aligned_traj1,
            'aligned_trajectory_2': aligned_traj2
        }
        
        return results
    
    def get_comparison_dataframe(self) -> pd.DataFrame:
        """
        Get comparison results as a DataFrame.
        
        Returns:
            DataFrame with deviation metrics
        """
        results = self.analyze()
        
        data = {
            'Metric': [
                'Mean Lateral Deviation (m)',
                'Max Lateral Deviation (m)',
                'Min Lateral Deviation (m)',
                'Std Lateral Deviation (m)',
                'Mean Vertical Deviation (m)',
                'Max Vertical Deviation (m)',
                'Min Vertical Deviation (m)',
                'Std Vertical Deviation (m)',
                'Number of Points'
            ],
            'Value': [
                results['mean_lateral_deviation'],
                results['max_lateral_deviation'],
                results['min_lateral_deviation'],
                results['std_lateral_deviation'],
                results['mean_vertical_deviation'],
                results['max_vertical_deviation'],
                results['min_vertical_deviation'],
                results['std_vertical_deviation'],
                results['num_points']
            ]
        }
        
        return pd.DataFrame(data)

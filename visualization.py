"""
Visualization module for trajectory comparison.
Provides 2D and 3D visualization of trajectories and deviations.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
from typing import Dict, Optional, Tuple
import matplotlib.cm as cm


class TrajectoryVisualizer:
    """Visualizer for comparing trajectories."""
    
    def __init__(self, analysis_results: Dict):
        """
        Initialize visualizer with analysis results.
        
        Args:
            analysis_results: Dictionary from TrajectoryAnalyzer.analyze()
        """
        self.results = analysis_results
        self.traj1_name = analysis_results['trajectory_1']
        self.traj2_name = analysis_results['trajectory_2']
        self.traj1 = analysis_results['aligned_trajectory_1']
        self.traj2 = analysis_results['aligned_trajectory_2']
        self.lateral_dev = analysis_results['lateral_deviations']
        self.vertical_dev = analysis_results['vertical_deviations']
    
    def plot_2d_trajectories(self, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Plot 2D trajectories on a map.
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot trajectories
        ax.plot(
            self.traj1[:, 0], self.traj1[:, 1],
            'b-', label=self.traj1_name, linewidth=2, marker='o', markersize=4
        )
        ax.plot(
            self.traj2[:, 0], self.traj2[:, 1],
            'r--', label=self.traj2_name, linewidth=2, marker='s', markersize=4
        )
        
        # Add labels and title
        ax.set_xlabel('Longitude', fontsize=12)
        ax.set_ylabel('Latitude', fontsize=12)
        ax.set_title('2D Trajectory Comparison', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_3d_trajectories(self, figsize: Tuple[int, int] = (14, 10)) -> plt.Figure:
        """
        Plot 3D trajectories for comparison.
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        # Create color gradients based on altitude
        norm1 = Normalize(vmin=np.min(self.traj1[:, 2]), vmax=np.max(self.traj1[:, 2]))
        norm2 = Normalize(vmin=np.min(self.traj2[:, 2]), vmax=np.max(self.traj2[:, 2]))
        
        # Plot trajectory 1
        sc1 = ax.scatter(
            self.traj1[:, 0], self.traj1[:, 1], self.traj1[:, 2],
            c=self.traj1[:, 2], cmap='viridis', norm=norm1,
            s=30, label=self.traj1_name, alpha=0.8
        )
        ax.plot(
            self.traj1[:, 0], self.traj1[:, 1], self.traj1[:, 2],
            'b-', alpha=0.5, linewidth=1.5
        )
        
        # Plot trajectory 2
        sc2 = ax.scatter(
            self.traj2[:, 0], self.traj2[:, 1], self.traj2[:, 2],
            c=self.traj2[:, 2], cmap='plasma', norm=norm2,
            s=30, label=self.traj2_name, alpha=0.8, marker='s'
        )
        ax.plot(
            self.traj2[:, 0], self.traj2[:, 1], self.traj2[:, 2],
            'r--', alpha=0.5, linewidth=1.5
        )
        
        # Add colorbars
        cbar1 = fig.colorbar(sc1, ax=ax, shrink=0.5, aspect=10)
        cbar1.set_label(f'{self.traj1_name} Altitude (m)', fontsize=10)
        cbar2 = fig.colorbar(sc2, ax=ax, shrink=0.5, aspect=10)
        cbar2.set_label(f'{self.traj2_name} Altitude (m)', fontsize=10)
        
        # Add labels and title
        ax.set_xlabel('Longitude', fontsize=12, labelpad=10)
        ax.set_ylabel('Latitude', fontsize=12, labelpad=10)
        ax.set_zlabel('Altitude (m)', fontsize=12, labelpad=10)
        ax.set_title('3D Trajectory Comparison', fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        
        # Adjust viewing angle for better comparison
        ax.view_init(elev=20, azim=45)
        
        plt.tight_layout()
        return fig
    
    def plot_deviations(self, figsize: Tuple[int, int] = (14, 6)) -> plt.Figure:
        """
        Plot lateral and vertical deviations.
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Plot lateral deviations
        ax1.plot(self.lateral_dev, 'g-', linewidth=2, marker='o', markersize=4)
        ax1.axhline(y=self.results['mean_lateral_deviation'], 
                   color='r', linestyle='--', label=f'Mean: {self.results["mean_lateral_deviation"]:.2f}m')
        ax1.axhline(y=self.results['mean_lateral_deviation'] + self.results['std_lateral_deviation'],
                   color='orange', linestyle=':', label=f'Mean + Std: {self.results["mean_lateral_deviation"] + self.results["std_lateral_deviation"]:.2f}m')
        ax1.axhline(y=self.results['mean_lateral_deviation'] - self.results['std_lateral_deviation'],
                   color='orange', linestyle=':', label=f'Mean - Std: {self.results["mean_lateral_deviation"] - self.results["std_lateral_deviation"]:.2f}m')
        ax1.set_xlabel('Point Index', fontsize=10)
        ax1.set_ylabel('Lateral Deviation (m)', fontsize=10)
        ax1.set_title('Lateral Deviation Between Trajectories', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)
        
        # Plot vertical deviations
        ax2.plot(self.vertical_dev, 'm-', linewidth=2, marker='s', markersize=4)
        ax2.axhline(y=self.results['mean_vertical_deviation'], 
                   color='r', linestyle='--', label=f'Mean: {self.results["mean_vertical_deviation"]:.2f}m')
        ax2.axhline(y=self.results['mean_vertical_deviation'] + self.results['std_vertical_deviation'],
                   color='orange', linestyle=':', label=f'Mean + Std: {self.results["mean_vertical_deviation"] + self.results["std_vertical_deviation"]:.2f}m')
        ax2.axhline(y=self.results['mean_vertical_deviation'] - self.results['std_vertical_deviation'],
                   color='orange', linestyle=':', label=f'Mean - Std: {self.results["mean_vertical_deviation"] - self.results["std_vertical_deviation"]:.2f}m')
        ax2.set_xlabel('Point Index', fontsize=10)
        ax2.set_ylabel('Vertical Deviation (m)', fontsize=10)
        ax2.set_title('Vertical Deviation (Altitude Difference)', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        plt.suptitle('Trajectory Deviations', fontsize=14, fontweight='bold')
        plt.tight_layout()
        return fig
    
    def plot_3d_with_deviations(
        self, 
        figsize: Tuple[int, int] = (14, 10),
        deviation_scale: float = 1.0
    ) -> plt.Figure:
        """
        Plot 3D trajectories with deviation indicators.
        
        The deviations are shown as lines connecting corresponding points.
        
        Args:
            figsize: Figure size
            deviation_scale: Scale factor for deviation lines
            
        Returns:
            Matplotlib Figure object
        """
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot trajectories
        ax.plot(
            self.traj1[:, 0], self.traj1[:, 1], self.traj1[:, 2],
            'b-', label=self.traj1_name, linewidth=2, alpha=0.7
        )
        ax.plot(
            self.traj2[:, 0], self.traj2[:, 1], self.traj2[:, 2],
            'r--', label=self.traj2_name, linewidth=2, alpha=0.7
        )
        
        # Plot deviation lines between corresponding points
        for i in range(len(self.traj1)):
            ax.plot(
                [self.traj1[i, 0], self.traj2[i, 0]],
                [self.traj1[i, 1], self.traj2[i, 1]],
                [self.traj1[i, 2], self.traj2[i, 2]],
                'k-', alpha=0.3, linewidth=0.5
            )
        
        # Add labels and title
        ax.set_xlabel('Longitude', fontsize=12, labelpad=10)
        ax.set_ylabel('Latitude', fontsize=12, labelpad=10)
        ax.set_zlabel('Altitude (m)', fontsize=12, labelpad=10)
        ax.set_title('3D Trajectory Comparison with Deviation Lines', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(fontsize=10)
        
        # Adjust viewing angle
        ax.view_init(elev=25, azim=45)
        
        plt.tight_layout()
        return fig
    
    def plot_comparison_summary(self, figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Plot a summary bar chart of deviation metrics.
        
        Args:
            figsize: Figure size
            
        Returns:
            Matplotlib Figure object
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        metrics = [
            'Mean Lateral',
            'Max Lateral',
            'Mean Vertical',
            'Max Vertical'
        ]
        values = [
            self.results['mean_lateral_deviation'],
            self.results['max_lateral_deviation'],
            self.results['mean_vertical_deviation'],
            self.results['max_vertical_deviation']
        ]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8, width=0.6)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}m', ha='center', va='bottom', fontsize=10)
        
        ax.set_ylabel('Deviation (meters)', fontsize=12)
        ax.set_title('Trajectory Deviation Summary', fontsize=14, fontweight='bold')
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def save_all_plots(self, output_dir: str = 'output') -> None:
        """
        Save all visualizations to files.
        
        Args:
            output_dir: Directory to save plots
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        self.plot_2d_trajectories().savefig(f'{output_dir}/2d_trajectories.png', dpi=300)
        self.plot_3d_trajectories().savefig(f'{output_dir}/3d_trajectories.png', dpi=300)
        self.plot_deviations().savefig(f'{output_dir}/deviations.png', dpi=300)
        self.plot_3d_with_deviations().savefig(f'{output_dir}/3d_with_deviations.png', dpi=300)
        self.plot_comparison_summary().savefig(f'{output_dir}/summary.png', dpi=300)
        
        print(f"All plots saved to {output_dir}/")

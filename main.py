#!/usr/bin/env python3
"""
Trajectory Analyzer - Main CLI
Compare and visualize KML trajectory files from different sources.
"""

import argparse
import sys
import os
from typing import List

from kml_parser import KMLParser, parse_kml_files
from analysis import TrajectoryAnalyzer
from visualization import TrajectoryVisualizer


def main():
    parser = argparse.ArgumentParser(
        description='Trajectory Analyzer - Compare and visualize KML trajectory files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file1.kml file2.kml                    # Compare two trajectories
  %(prog)s file1.kml file2.kml --output results    # Save results to directory
  %(prog)s file1.kml file2.kml --show             # Show plots interactively
  %(prog)s file1.kml file2.kml --3d               # Show 3D visualization only
        """
    )
    
    parser.add_argument(
        'kml_files',
        nargs='+',
        help='KML files to compare (exactly 2 files required)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output',
        help='Output directory for saving plots and results (default: output)'
    )
    parser.add_argument(
        '--show', '-s',
        action='store_true',
        help='Show plots interactively'
    )
    parser.add_argument(
        '--no-show',
        action='store_true',
        help='Do not show plots interactively'
    )
    parser.add_argument(
        '--3d',
        action='store_true',
        help='Show only 3D visualization'
    )
    parser.add_argument(
        '--2d',
        action='store_true',
        help='Show only 2D visualization'
    )
    parser.add_argument(
        '--deviations',
        action='store_true',
        help='Show deviation plots'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save all plots to output directory'
    )
    parser.add_argument(
        '--csv',
        action='store_true',
        help='Save comparison results to CSV'
    )
    parser.add_argument(
        '--alignment', '-a',
        type=str,
        default='nearest',
        choices=['nearest', 'interpolation', 'bidirectional'],
        help='Alignment method: nearest (all ref points), bidirectional (only mutual matches), or interpolation'
    )
    parser.add_argument(
        '--filter-no-time',
        action='store_true',
        help='Filter out points without timestamps'
    )
    
    args = parser.parse_args()
    
    # Validate input
    if len(args.kml_files) != 2:
        print("Error: Exactly 2 KML files are required for comparison")
        sys.exit(1)
    
    if not all(os.path.exists(f) for f in args.kml_files):
        print("Error: One or more KML files do not exist")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 60)
    print("Trajectory Analyzer")
    print("=" * 60)
    print(f"Comparing: {args.kml_files[0]}")
    print(f"         vs {args.kml_files[1]}")
    print()
    
    # Parse KML files
    print("Parsing KML files...")
    try:
        trajectories = parse_kml_files(args.kml_files)
        traj1 = trajectories[args.kml_files[0]]
        traj2 = trajectories[args.kml_files[1]]
        
        # Filter points without timestamps if requested
        if args.filter_no_time:
            if 'timestamp' in traj1.columns and traj1['timestamp'].notna().any():
                traj1 = traj1[traj1['timestamp'].notna()].copy()
            if 'timestamp' in traj2.columns and traj2['timestamp'].notna().any():
                traj2 = traj2[traj2['timestamp'].notna()].copy()
        
        print(f"  {args.kml_files[0]}: {len(traj1)} points")
        print(f"  {args.kml_files[1]}: {len(traj2)} points")
    except Exception as e:
        print(f"Error parsing KML files: {e}")
        sys.exit(1)
    
    # Analyze trajectories
    print(f"\nAnalyzing trajectories with {args.alignment} alignment...")
    analyzer = TrajectoryAnalyzer(traj1, traj2, alignment_method=args.alignment)
    results = analyzer.analyze()
    
    # Print summary
    print(f"\n{'-' * 60}")
    print("DEVIATION SUMMARY")
    print(f"{'-' * 60}")
    print(f"Lateral Deviations:")
    print(f"  Mean:  {results['mean_lateral_deviation']:.2f} m")
    print(f"  Max:   {results['max_lateral_deviation']:.2f} m")
    print(f"  Min:   {results['min_lateral_deviation']:.2f} m")
    print(f"  Std:   {results['std_lateral_deviation']:.2f} m")
    print(f"\nVertical Deviations:")
    print(f"  Mean:  {results['mean_vertical_deviation']:.2f} m")
    print(f"  Max:   {results['max_vertical_deviation']:.2f} m")
    print(f"  Min:   {results['min_vertical_deviation']:.2f} m")
    print(f"  Std:   {results['std_vertical_deviation']:.2f} m")
    print(f"\nNumber of comparison points: {results['num_points']}")
    
    # Save CSV if requested
    if args.csv:
        csv_path = os.path.join(args.output, 'comparison_results.csv')
        comparison_df = analyzer.get_comparison_dataframe()
        comparison_df.to_csv(csv_path, index=False)
        print(f"\nComparison results saved to: {csv_path}")
    
    # Create visualizer
    visualizer = TrajectoryVisualizer(results)
    
    # Determine which plots to show
    plots_to_show = []
    
    # Get flag values (handle --3d and --2d which become args.3d and args.2d)
    show_3d = getattr(args, '3d', False)
    show_2d = getattr(args, '2d', False)
    
    if show_3d or (not any([show_2d, args.deviations, args.summary]) and args.show and not args.no_show):
        plots_to_show.append(('3D Trajectories', visualizer.plot_3d_trajectories()))
    
    if show_2d or (not any([show_3d, args.deviations, args.summary]) and args.show and not args.no_show):
        plots_to_show.append(('2D Trajectories', visualizer.plot_2d_trajectories()))
    
    if args.deviations or (not any([show_3d, show_2d, args.summary]) and args.show and not args.no_show):
        plots_to_show.append(('Deviations', visualizer.plot_deviations()))
    
    if args.summary or (not any([show_3d, show_2d, args.deviations]) and args.show and not args.no_show):
        plots_to_show.append(('3D with Deviations', visualizer.plot_3d_with_deviations()))
        plots_to_show.append(('Summary', visualizer.plot_comparison_summary()))
    
    # If no specific flags but --show, show all
    if args.show and not args.no_show and not any([show_3d, show_2d, args.deviations, args.summary]):
        plots_to_show = [
            ('2D Trajectories', visualizer.plot_2d_trajectories()),
            ('3D Trajectories', visualizer.plot_3d_trajectories()),
            ('3D with Deviations', visualizer.plot_3d_with_deviations()),
            ('Deviations', visualizer.plot_deviations()),
            ('Summary', visualizer.plot_comparison_summary())
        ]
    
    # Save plots if requested
    if args.save:
        visualizer.save_all_plots(args.output)
    
    # Show plots
    if args.show and not args.no_show:
        import matplotlib.pyplot as plt
        
        for title, fig in plots_to_show:
            print(f"\nDisplaying: {title}")
            plt.figure(fig.number)
            plt.show(block=False)
        
        if plots_to_show:
            print("\nPress Enter to close all plots...")
            input()
            plt.close('all')
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

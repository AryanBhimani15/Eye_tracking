from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import base64
import json
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Store sessions in memory (use Redis in production)
sessions = {}
study_sessions = {}  # New: Store complete rapid-fire studies

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cars')
def get_cars():
    """Return available car images for the study"""
    cars = [
        {
            "id": "bmw-m3",
            "name": "BMW M3 Competition",
            "year": "2024",
            "image": "https://cdn.dealeraccelerate.com/speedcollection/1/107/6100/1920x1440/2024-bmw-m3-competition",
            "thumbnail": "https://cdn.motor1.com/images/mgl/Kb703N/s3/bmw-m3-limousine-2024-und-bmw-m3-touring-2024.jpg"
        },
        {
            "id": "porsche-gt3",
            "name": "Porsche 911 GT3 RS",
            "year": "2024", 
            "image": "https://4kwallpapers.com/images/walls/thumbs_2t/24195.jpg",
            "thumbnail": "https://4kwallpapers.com/images/walls/thumbs_2t/24195.jpg"
        },
        {
            "id": "mercedes-amg-gt",
            "name": "Mercedes-AMG GT 63",
            "year": "2024",
            "image": "https://wallpaper.caricos.com/2024-Mercedes-AMG-GT-63-Coupe-4MATIC+-with-AMG-Aerodynamic-package-(Color-High-Tech-Silver-Metallic)---Front-Three-Quarter-3875102-1024x768.jpg",
            "thumbnail": "https://wallpaper.caricos.com/2024-Mercedes-AMG-GT-63-Coupe-4MATIC+-with-AMG-Aerodynamic-package-(Color-High-Tech-Silver-Metallic)---Front-Three-Quarter-3875102-1024x768.jpg"
        },
        {
            "id": "audi-r8",
            "name": "Audi R8 V10 Performance",
            "year": "2024",
            "image": "https://www.topgear.com/sites/default/files/2024/06/1%20Audi%20R8%20GT%20review.jpg",
            "thumbnail": "https://uploads.audi-mediacenter.com/system/production/media/70272/images/3c92d2acbf6ab5f85be8006f854786f0f0ff36be/A1813681_web_2880.jpg?1743603759"
        }
    ]
    return jsonify(cars)

@app.route('/api/study/start', methods=['POST'])
def start_study():
    """Initialize a new rapid-fire study session"""
    data = request.get_json(silent=True) or {}
    study_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + os.urandom(4).hex()

    study_sessions[study_id] = {
        'start_time': datetime.now().isoformat(),
        'individual_sessions': [],
        'metadata': {
            'user_agent': request.headers.get('User-Agent'),
            'screen_resolution': data.get('screen_resolution'),
            'study_type': 'rapid_fire',
            'duration_per_vehicle': 5.0
        }
    }

    return jsonify({
        'study_id': study_id,
        'status': 'started',
        'timestamp': study_sessions[study_id]['start_time']
    })

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """Initialize a single vehicle session within a study"""
    data = request.get_json(silent=True) or {}
    if not data.get('car_id'):
        return jsonify({'error': 'car_id is required'}), 400
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S_') + os.urandom(4).hex()

    sessions[session_id] = {
        'car_id': data.get('car_id'),
        'car_name': data.get('car_name'),
        'car_index': data.get('car_index', 0),
        'start_time': datetime.now().isoformat(),
        'gaze_points': [],
        'first_gaze': None,
        'metadata': {
            'user_agent': request.headers.get('User-Agent'),
            'screen_resolution': data.get('screen_resolution'),
            'image_dimensions': data.get('image_dimensions')
        }
    }

    return jsonify({
        'session_id': session_id,
        'status': 'started',
        'timestamp': sessions[session_id]['start_time']
    })

@app.route('/api/session/<session_id>/gaze', methods=['POST'])
def record_gaze(session_id):
    """Record a gaze point with enhanced data"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json(silent=True) or {}
    if data.get('x') is None or data.get('y') is None:
        return jsonify({'error': 'x and y are required'}), 400
    point = {
        'x': data.get('x'),
        'y': data.get('y'),
        'relative_x': data.get('relativeX'),
        'relative_y': data.get('relativeY'),
        'timestamp': data.get('timestamp'),
        'confidence': data.get('confidence', 1.0),
        'pupil_dilation': data.get('pupil_dilation'),
        'head_pose': data.get('head_pose')
    }

    sessions[session_id]['gaze_points'].append(point)

    # Capture first gaze if not set
    if sessions[session_id]['first_gaze'] is None:
        sessions[session_id]['first_gaze'] = point

    return jsonify({
        'status': 'recorded',
        'point_count': len(sessions[session_id]['gaze_points']),
        'first_gaze': sessions[session_id]['first_gaze']
    })

@app.route('/api/session/<session_id>/stop', methods=['POST'])
def stop_session(session_id):
    """End session and return comprehensive analysis"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = sessions[session_id]
    session['end_time'] = datetime.now().isoformat()

    points = session['gaze_points']

    # Calculate comprehensive statistics
    duration = 0
    if points:
        start_ts = points[0].get('timestamp')
        end_ts = points[-1].get('timestamp')
        if start_ts is not None and end_ts is not None:
            duration = (end_ts - start_ts) / 1000

    # Generate heatmap grid (100x100 for detailed analysis)
    heatmap_grid = generate_heatmap_grid(points)

    # Calculate attention metrics
    attention_metrics = calculate_attention_metrics(points)

    # Identify hotspots (top 10% density areas)
    hotspots = identify_hotspots(heatmap_grid)

    # Identify cold zones (areas with zero attention)
    cold_zones = identify_cold_zones(heatmap_grid)

    summary = {
        'session_id': session_id,
        'car_id': session['car_id'],
        'car_name': session['car_name'],
        'total_points': len(points),
        'duration_seconds': round(duration, 2),
        'first_gaze': session['first_gaze'],
        'heatmap_grid': heatmap_grid,
        'attention_metrics': attention_metrics,
        'hotspots': hotspots,
        'cold_zones': cold_zones,
        'gaze_path': generate_gaze_path(points),
        'status': 'completed'
    }

    session['summary'] = summary

    return jsonify(summary)

def generate_heatmap_grid(points, grid_size=50):
    """Generate high-resolution density grid for heatmap"""
    if not points:
        return [[0 for _ in range(grid_size)] for _ in range(grid_size)]

    grid = [[0 for _ in range(grid_size)] for _ in range(grid_size)]

    for pt in points:
        if 'relative_x' in pt and 'relative_y' in pt:
            gx = int(pt['relative_x'] * grid_size)
            gy = int(pt['relative_y'] * grid_size)
        else:
            gx = int((pt['x'] / 1920) * grid_size)  # fallback
            gy = int((pt['y'] / 1080) * grid_size)

        if 0 <= gx < grid_size and 0 <= gy < grid_size:
            # Apply Gaussian spread
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < grid_size and 0 <= ny < grid_size:
                        dist = (dx**2 + dy**2) ** 0.5
                        weight = max(0, 1 - dist / 2.5)
                        grid[ny][nx] += weight

    # Normalize
    max_val = max(max(row) for row in grid) if grid else 1
    if max_val > 0:
        grid = [[round(cell/max_val, 3) for cell in row] for row in grid]

    return grid

def calculate_attention_metrics(points):
    """Calculate detailed attention metrics"""
    if not points:
        return {}

    # Calculate dispersion (spread of gaze)
    x_coords = [p['x'] for p in points if 'x' in p]
    y_coords = [p['y'] for p in points if 'y' in p]

    if not x_coords or not y_coords:
        return {}

    x_mean = sum(x_coords) / len(x_coords)
    y_mean = sum(y_coords) / len(y_coords)

    x_var = sum((x - x_mean)**2 for x in x_coords) / len(x_coords)
    y_var = sum((y - y_mean)**2 for y in y_coords) / len(y_coords)

    dispersion = (x_var + y_var) ** 0.5

    # Calculate scan path length
    scan_path = 0
    for i in range(1, len(points)):
        if 'x' in points[i] and 'x' in points[i-1]:
            dx = points[i]['x'] - points[i-1]['x']
            dy = points[i]['y'] - points[i-1]['y']
            scan_path += (dx**2 + dy**2) ** 0.5

    return {
        'dispersion': round(dispersion, 2),
        'mean_x': round(x_mean, 2),
        'mean_y': round(y_mean, 2),
        'scan_path_length': round(scan_path, 2),
        'scan_path_efficiency': round(scan_path / len(points), 2) if points else 0
    }

def identify_hotspots(heatmap_grid, threshold=0.8):
    """Identify high-attention areas"""
    hotspots = []
    grid_size = len(heatmap_grid)

    for y in range(grid_size):
        for x in range(grid_size):
            if heatmap_grid[y][x] >= threshold:
                hotspots.append({
                    'x': x / grid_size,
                    'y': y / grid_size,
                    'intensity': heatmap_grid[y][x]
                })

    # Sort by intensity and return top 10
    hotspots.sort(key=lambda h: h['intensity'], reverse=True)
    return hotspots[:10]

def identify_cold_zones(heatmap_grid, threshold=0.05):
    """Identify areas with minimal attention"""
    cold_zones = []
    grid_size = len(heatmap_grid)

    # Find contiguous regions with low attention
    visited = [[False for _ in range(grid_size)] for _ in range(grid_size)]

    for y in range(grid_size):
        for x in range(grid_size):
            if not visited[y][x] and heatmap_grid[y][x] <= threshold:
                # BFS to find region
                region = []
                queue = [(x, y)]
                visited[y][x] = True

                while queue:
                    cx, cy = queue.pop(0)
                    region.append({'x': cx/grid_size, 'y': cy/grid_size})

                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < grid_size and 0 <= ny < grid_size:
                            if not visited[ny][nx] and heatmap_grid[ny][nx] <= threshold:
                                visited[ny][nx] = True
                                queue.append((nx, ny))

                if len(region) > 10:  # Only significant regions
                    cold_zones.append({
                        'size': len(region),
                        'center_x': sum(p['x'] for p in region) / len(region),
                        'center_y': sum(p['y'] for p in region) / len(region)
                    })

    return cold_zones[:5]  # Return top 5 largest cold zones

def generate_gaze_path(points):
    """Generate simplified gaze path for visualization"""
    if len(points) < 2:
        return []

    # Sample every Nth point to reduce complexity
    sample_rate = max(1, len(points) // 50)
    sampled = points[::sample_rate]

    return [
        {
            'x': p.get('relative_x', p.get('x', 0) / 1920),
            'y': p.get('relative_y', p.get('y', 0) / 1080),
            'index': i
        }
        for i, p in enumerate(sampled)
    ]

@app.route('/api/study/<study_id>/complete', methods=['POST'])
def complete_study(study_id):
    """Complete a full rapid-fire study and generate comparative analysis"""
    if study_id not in study_sessions:
        return jsonify({'error': 'Study not found'}), 404

    study = study_sessions[study_id]
    study['end_time'] = datetime.now().isoformat()

    # Generate comparative analysis
    comparison = generate_comparative_analysis(study)

    return jsonify({
        'study_id': study_id,
        'status': 'completed',
        'total_vehicles': len(study['individual_sessions']),
        'comparison': comparison
    })

def generate_comparative_analysis(study):
    """Generate comparison metrics across all vehicles in study"""
    sessions_data = study['individual_sessions']

    if not sessions_data:
        return {}

    comparison = {
        'attention_distribution': [],
        'first_gaze_comparison': [],
        'engagement_ranking': []
    }

    for session_data in sessions_data:
        session_id = session_data.get('session_id')
        if session_id in sessions:
            session = sessions[session_id]
            summary = session.get('summary', {})

            comparison['attention_distribution'].append({
                'car_id': session['car_id'],
                'car_name': session['car_name'],
                'total_points': summary.get('total_points', 0),
                'dispersion': summary.get('attention_metrics', {}).get('dispersion', 0)
            })

            if summary.get('first_gaze'):
                comparison['first_gaze_comparison'].append({
                    'car_id': session['car_id'],
                    'car_name': session['car_name'],
                    'first_gaze': summary['first_gaze']
                })

    # Rank by engagement (total gaze points)
    comparison['engagement_ranking'] = sorted(
        comparison['attention_distribution'],
        key=lambda x: x['total_points'],
        reverse=True
    )

    return comparison

@app.route('/api/session/<session_id>/export', methods=['GET'])
def export_session(session_id):
    """Export session data as JSON"""
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify(sessions[session_id])

@app.route('/api/study/<study_id>/export', methods=['GET'])
def export_study(study_id):
    """Export complete study data"""
    if study_id not in study_sessions:
        return jsonify({'error': 'Study not found'}), 404

    study = study_sessions[study_id]

    # Compile all session data
    full_data = {
        'study_metadata': study['metadata'],
        'start_time': study['start_time'],
        'end_time': study.get('end_time'),
        'vehicles': []
    }

    for session_ref in study['individual_sessions']:
        session_id = session_ref.get('session_id')
        if session_id in sessions:
            full_data['vehicles'].append(sessions[session_id])

    return jsonify(full_data)

@app.errorhandler(404)
def not_found(_):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    app.logger.exception('Unhandled server error: %s', e)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
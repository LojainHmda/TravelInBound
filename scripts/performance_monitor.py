#!/usr/bin/env python3
"""
Performance monitoring server for the travel booking platform
Runs on port 9000 and provides performance metrics and analysis
"""

import os
import time
import psutil
import threading
from flask import Flask, render_template_string, jsonify
from datetime import datetime, timedelta
import sqlite3
import requests
from collections import defaultdict

app = Flask(__name__)

# Performance metrics storage
metrics = {
    'cpu_usage': [],
    'memory_usage': [],
    'response_times': [],
    'database_queries': [],
    'active_connections': 0,
    'errors': []
}

# Performance monitoring template
MONITOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Platform Performance Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metrics-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px;
        }
        .metric-card { 
            background: #fff; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .metric-value { 
            font-size: 2em; 
            font-weight: bold; 
            color: #333;
        }
        .metric-label { 
            color: #666; 
            font-size: 0.9em;
            margin-top: 5px;
        }
        .chart-container { 
            margin: 20px 0; 
            height: 300px;
        }
        .alert { 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 4px;
        }
        .alert-warning { 
            background: #fff3cd; 
            border: 1px solid #ffeaa7; 
            color: #856404;
        }
        .alert-danger { 
            background: #f8d7da; 
            border: 1px solid #f5c6cb; 
            color: #721c24;
        }
        .recommendations {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
        }
        .status-good { border-left-color: #28a745; }
        .status-warning { border-left-color: #ffc107; }
        .status-critical { border-left-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Travel Platform Performance Monitor</h1>
        <p>Real-time performance monitoring for your travel booking platform</p>
        
        <div class="metrics-grid">
            <div class="metric-card {{ cpu_status }}">
                <div class="metric-value">{{ cpu_usage }}%</div>
                <div class="metric-label">CPU Usage</div>
            </div>
            <div class="metric-card {{ memory_status }}">
                <div class="metric-value">{{ memory_usage }}%</div>
                <div class="metric-label">Memory Usage</div>
            </div>
            <div class="metric-card {{ response_status }}">
                <div class="metric-value">{{ avg_response_time }}ms</div>
                <div class="metric-label">Avg Response Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ db_connections }}</div>
                <div class="metric-label">Database Connections</div>
            </div>
        </div>

        {% if performance_issues %}
        <div class="alert alert-warning">
            <strong>⚠️ Performance Issues Detected:</strong>
            <ul>
                {% for issue in performance_issues %}
                <li>{{ issue }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <div class="chart-container">
            <canvas id="performanceChart"></canvas>
        </div>

        <div class="recommendations">
            <h3>🔧 Performance Optimization Recommendations:</h3>
            <ul>
                {% for rec in recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
        </div>

        <div style="margin-top: 30px;">
            <h3>📊 Detailed Analysis</h3>
            <div id="detailed-metrics">
                <p><strong>Database Query Performance:</strong> {{ db_query_analysis }}</p>
                <p><strong>Memory Leaks Check:</strong> {{ memory_trend }}</p>
                <p><strong>Response Time Trends:</strong> {{ response_trend }}</p>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
        
        // Performance chart
        const ctx = document.getElementById('performanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: {{ chart_labels | safe }},
                datasets: [{
                    label: 'CPU Usage %',
                    data: {{ cpu_data | safe }},
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }, {
                    label: 'Memory Usage %',
                    data: {{ memory_data | safe }},
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

def collect_system_metrics():
    """Collect system performance metrics"""
    while True:
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Store metrics (keep last 50 readings)
            metrics['cpu_usage'].append({
                'timestamp': datetime.now(),
                'value': cpu_percent
            })
            metrics['memory_usage'].append({
                'timestamp': datetime.now(),
                'value': memory_percent
            })
            
            # Keep only last 50 readings
            if len(metrics['cpu_usage']) > 50:
                metrics['cpu_usage'] = metrics['cpu_usage'][-50:]
            if len(metrics['memory_usage']) > 50:
                metrics['memory_usage'] = metrics['memory_usage'][-50:]
                
        except Exception as e:
            metrics['errors'].append(f"Metrics collection error: {str(e)}")
        
        time.sleep(10)  # Collect every 10 seconds

def test_main_app_performance():
    """Test the main application response times"""
    try:
        start_time = time.time()
        response = requests.get('http://localhost:5000/', timeout=5)
        response_time = (time.time() - start_time) * 1000
        
        metrics['response_times'].append({
            'timestamp': datetime.now(),
            'value': response_time,
            'status_code': response.status_code
        })
        
        # Keep only last 20 readings
        if len(metrics['response_times']) > 20:
            metrics['response_times'] = metrics['response_times'][-20:]
            
    except Exception as e:
        metrics['errors'].append(f"App response test failed: {str(e)}")

def analyze_performance():
    """Analyze current performance and generate recommendations"""
    issues = []
    recommendations = []
    
    # CPU Analysis
    if metrics['cpu_usage']:
        avg_cpu = sum(m['value'] for m in metrics['cpu_usage'][-10:]) / min(10, len(metrics['cpu_usage']))
        if avg_cpu > 80:
            issues.append(f"High CPU usage: {avg_cpu:.1f}%")
            recommendations.append("Consider optimizing database queries and adding caching")
        elif avg_cpu > 60:
            recommendations.append("Monitor CPU usage - consider adding more efficient indexing")
    
    # Memory Analysis
    if metrics['memory_usage']:
        avg_memory = sum(m['value'] for m in metrics['memory_usage'][-10:]) / min(10, len(metrics['memory_usage']))
        if avg_memory > 85:
            issues.append(f"High memory usage: {avg_memory:.1f}%")
            recommendations.append("Check for memory leaks in Flask application")
        elif avg_memory > 70:
            recommendations.append("Monitor memory usage - consider connection pooling optimization")
    
    # Response Time Analysis
    if metrics['response_times']:
        avg_response = sum(m['value'] for m in metrics['response_times'][-10:]) / min(10, len(metrics['response_times']))
        if avg_response > 2000:
            issues.append(f"Slow response times: {avg_response:.0f}ms")
            recommendations.append("Optimize database queries and add proper indexing")
        elif avg_response > 1000:
            recommendations.append("Consider adding Redis caching for frequent queries")
    
    # Database specific recommendations for travel booking platform
    recommendations.extend([
        "Add database indexes on booking.reference_number and service_item.booking_id",
        "Implement pagination for large booking lists",
        "Cache frequently accessed customer and supplier data",
        "Optimize the finance dashboard queries with proper aggregation",
        "Consider using database connection pooling"
    ])
    
    return issues, recommendations

@app.route('/')
def performance_dashboard():
    """Main performance monitoring dashboard"""
    test_main_app_performance()
    
    issues, recommendations = analyze_performance()
    
    # Calculate current metrics
    current_cpu = metrics['cpu_usage'][-1]['value'] if metrics['cpu_usage'] else 0
    current_memory = metrics['memory_usage'][-1]['value'] if metrics['memory_usage'] else 0
    avg_response = sum(m['value'] for m in metrics['response_times'][-5:]) / max(1, len(metrics['response_times'][-5:])) if metrics['response_times'] else 0
    
    # Status indicators
    cpu_status = 'status-critical' if current_cpu > 80 else 'status-warning' if current_cpu > 60 else 'status-good'
    memory_status = 'status-critical' if current_memory > 85 else 'status-warning' if current_memory > 70 else 'status-good'
    response_status = 'status-critical' if avg_response > 2000 else 'status-warning' if avg_response > 1000 else 'status-good'
    
    # Chart data
    chart_labels = [m['timestamp'].strftime('%H:%M:%S') for m in metrics['cpu_usage'][-20:]]
    cpu_data = [m['value'] for m in metrics['cpu_usage'][-20:]]
    memory_data = [m['value'] for m in metrics['memory_usage'][-20:]]
    
    # Analysis
    db_query_analysis = "Database queries appear normal" if avg_response < 1000 else "Slow database queries detected"
    memory_trend = "Memory usage stable" if len(metrics['memory_usage']) < 10 else "Memory trend analysis available"
    response_trend = "Response times acceptable" if avg_response < 1000 else "Response times need optimization"
    
    return render_template_string(MONITOR_TEMPLATE,
        cpu_usage=f"{current_cpu:.1f}",
        memory_usage=f"{current_memory:.1f}",
        avg_response_time=f"{avg_response:.0f}",
        db_connections="Active",
        cpu_status=cpu_status,
        memory_status=memory_status,
        response_status=response_status,
        performance_issues=issues,
        recommendations=recommendations,
        chart_labels=chart_labels,
        cpu_data=cpu_data,
        memory_data=memory_data,
        db_query_analysis=db_query_analysis,
        memory_trend=memory_trend,
        response_trend=response_trend
    )

@app.route('/api/metrics')
def api_metrics():
    """API endpoint for current metrics"""
    return jsonify({
        'cpu_usage': metrics['cpu_usage'][-1]['value'] if metrics['cpu_usage'] else 0,
        'memory_usage': metrics['memory_usage'][-1]['value'] if metrics['memory_usage'] else 0,
        'response_times': [m['value'] for m in metrics['response_times'][-10:]],
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Start background metrics collection
    metrics_thread = threading.Thread(target=collect_system_metrics, daemon=True)
    metrics_thread.start()
    
    print("🚀 Performance Monitor starting on port 9000...")
    print("📊 Monitoring your travel platform performance...")
    print("🔗 Access dashboard at: http://localhost:9000")
    
    app.run(host='0.0.0.0', port=9000, debug=True)
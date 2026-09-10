import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
import random
import math

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')
DB_PATH = os.path.join(DB_DIR, 'smart_automation.db')

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        full_name TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Resources table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        capacity REAL NOT NULL,
        current_usage REAL NOT NULL DEFAULT 0.0,
        unit TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Optimal',
        location TEXT NOT NULL DEFAULT 'Main Campus',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Readings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER NOT NULL,
        value REAL NOT NULL,
        occupancy REAL DEFAULT 0.0,
        timestamp DATETIME NOT NULL,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_resource_time ON readings(resource_id, timestamp)")

    # 4. Insights table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER,
        type TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'MEDIUM',
        description TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL
    )
    """)

    # 5. Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER,
        severity TEXT NOT NULL DEFAULT 'MEDIUM',
        message TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        resolved_at DATETIME,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL
    )
    """)

    # 6. Automation Rules table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        trigger_condition TEXT NOT NULL,
        action_type TEXT NOT NULL,
        is_enabled INTEGER NOT NULL DEFAULT 1,
        auto_execute INTEGER NOT NULL DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Automation Actions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS automation_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        resource_id INTEGER,
        trigger TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Executed',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL
    )
    """)

    # 8. Recommendations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        expected_benefit TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'MEDIUM',
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL
    )
    """)

    # 9. System Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()

def seed_data(force=False):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM resources")
    count = cursor.fetchone()[0]
    if count > 0 and not force:
        conn.close()
        return

    if force:
        cursor.execute("DELETE FROM readings")
        cursor.execute("DELETE FROM insights")
        cursor.execute("DELETE FROM alerts")
        cursor.execute("DELETE FROM automation_actions")
        cursor.execute("DELETE FROM recommendations")
        cursor.execute("DELETE FROM automation_rules")
        cursor.execute("DELETE FROM system_settings")
        cursor.execute("DELETE FROM resources")
        cursor.execute("DELETE FROM users")
        conn.commit()

    # 1. Seed default user (admin / admin123)
    admin_pw_hash = hash_password("admin123")
    cursor.execute("""
    INSERT INTO users (username, password_hash, role, full_name)
    VALUES (?, ?, 'admin', 'Lead System Administrator')
    """, ("admin", admin_pw_hash))

    # 2. Seed System Settings
    settings = [
        ('electricity_threshold', '85', 'Electricity capacity threshold percentage for peak alert'),
        ('water_threshold', '75', 'Water flow threshold (L/min) for leakage alert'),
        ('network_threshold', '90', 'Network bandwidth utilization alert percentage'),
        ('occupancy_idle_timeout', '15', 'Minutes with zero occupancy before triggering energy-saving'),
        ('anomaly_z_score', '2.5', 'Statistical Z-score sensitivity for anomaly identification'),
        ('auto_execute_mode', 'true', 'Automatically execute smart automation actions when triggered'),
        ('simulation_interval', '5', 'Interval in seconds for simulated sensor streaming')
    ]
    cursor.executemany("INSERT OR REPLACE INTO system_settings (key, value, description) VALUES (?, ?, ?)", settings)

    # 3. Seed Resources
    resources_data = [
        ('Main Campus Power Grid', 'electricity', 500.0, 312.4, 'kWh', 'Optimal', 'Substation Alpha'),
        ('Central HVAC & Water Supply', 'water', 200.0, 68.2, 'L/min', 'Optimal', 'Utility Building B'),
        ('Advanced Computing Lab A', 'computing', 100.0, 58.0, 'Units', 'Optimal', 'Science Block 3F'),
        ('Smart Seminar Hall 101', 'room', 150.0, 35.0, 'Seats', 'Optimal', 'Academic Block 1F'),
        ('Campus Core Fiber Network', 'network', 1000.0, 580.0, 'Mbps', 'Optimal', 'Data Center Core'),
        ('Robotics & IoT Research Lab', 'computing', 50.0, 14.0, 'Units', 'Warning', 'Innovation Hub 2F')
    ]

    resource_ids = []
    for res in resources_data:
        cursor.execute("""
        INSERT INTO resources (name, type, capacity, current_usage, unit, status, location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, res)
        resource_ids.append(cursor.lastrowid)

    # 4. Seed Rules
    rules_data = [
        ("Peak Demand Electricity Load-Shedding", "electricity", "usage_pct > 85", "Shed non-critical circuits & alert facility manager", 1, 1),
        ("Zero-Occupancy Ghost Power Cutoff", "computing", "occupancy == 0 and usage_pct > 25", "Switch idle lab equipment to eco-sleep mode", 1, 1),
        ("Surge Water Leakage Emergency Cutoff", "water", "z_score > 2.8 or usage > 75", "Generate critical alert & simulate isolation valve cutoff", 1, 1),
        ("Dynamic Network QoS Bandwidth Throttling", "network", "usage_pct > 90", "Prioritize academic traffic and throttle non-essential streams", 1, 1),
        ("Consolidation of Underutilized Lab Nodes", "computing", "utilization < 20% for 3 days", "Recommend workstation server shutdown & node consolidation", 1, 1)
    ]
    cursor.executemany("""
    INSERT INTO automation_rules (rule_name, resource_type, trigger_condition, action_type, is_enabled, auto_execute)
    VALUES (?, ?, ?, ?, ?, ?)
    """, rules_data)

    # 5. Generate 7 days of realistic hourly readings for each resource
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    random.seed(42)

    for idx, r_id in enumerate(resource_ids):
        res_type = resources_data[idx][1]
        capacity = resources_data[idx][2]
        
        # 168 hours = 7 days
        for h in range(168, -1, -1):
            reading_time = now - timedelta(hours=h)
            hour_of_day = reading_time.hour
            day_of_week = reading_time.weekday()
            is_weekend = day_of_week >= 5

            diurnal = math.sin((hour_of_day - 6) * math.pi / 18)
            diurnal = max(0.15, (diurnal + 1) / 2)

            if is_weekend:
                diurnal *= 0.35

            noise = random.uniform(0.92, 1.08)

            if res_type == 'electricity':
                val = (110.0 + 260.0 * diurnal) * noise
                occupancy = int((40 + 220 * diurnal) * noise) if not is_weekend else int(15 * noise)
            elif res_type == 'water':
                val = (12.0 + 65.0 * diurnal) * noise
                occupancy = int((30 + 180 * diurnal) * noise) if not is_weekend else int(10 * noise)
            elif res_type == 'computing':
                if idx == 2:
                    val = (10.0 + 75.0 * diurnal) * noise
                    occupancy = int((5 + 85 * diurnal) * noise) if not is_weekend else 0
                else:
                    val = (8.0 + 18.0 * diurnal) * noise
                    occupancy = int((2 + 15 * diurnal) * noise) if not is_weekend else 0
            elif res_type == 'room':
                val = int((5 + 110 * diurnal) * noise) if not is_weekend else 0
                occupancy = val
            elif res_type == 'network':
                val = (180.0 + 580.0 * diurnal) * noise
                occupancy = int((50 + 350 * diurnal) * noise) if not is_weekend else 30

            val = round(min(capacity * 0.98, max(5.0, val)), 1)

            if h == 48 and res_type == 'water':
                val = round(capacity * 0.88, 1)
            elif h == 24 and res_type == 'electricity' and hour_of_day == 2:
                val = 380.0
                occupancy = 0

            cursor.execute("""
            INSERT INTO readings (resource_id, value, occupancy, timestamp)
            VALUES (?, ?, ?, ?)
            """, (r_id, val, occupancy, reading_time.strftime('%Y-%m-%d %H:%M:%S')))

    for r_id in resource_ids:
        cursor.execute("SELECT value FROM readings WHERE resource_id = ? ORDER BY timestamp DESC LIMIT 1", (r_id,))
        latest = cursor.fetchone()
        if latest:
            cursor.execute("UPDATE resources SET current_usage = ? WHERE id = ?", (latest[0], r_id))

    initial_insights = [
        (resource_ids[0], 'anomaly', 'HIGH', 'Off-peak electricity spike detected at 02:00 AM (380.0 kWh vs expected 115.0 kWh).', 'Investigate HVAC scheduling and auxiliary building sub-panels for unintended night loads.'),
        (resource_ids[1], 'wastage', 'CRITICAL', 'Continuous water flow signature detected between 01:00-04:00 AM indicating plumbing leak in Restroom Wing B.', 'Deploy automated isolation valve closure and trigger field inspection.'),
        (resource_ids[5], 'underutilization', 'MEDIUM', 'Robotics & IoT Research Lab maintained < 22% average utilization over the past 7 days.', 'Consolidate active compute nodes and schedule power standby for inactive developer rigs.'),
        (resource_ids[4], 'optimization', 'LOW', 'Campus Fiber Network bandwidth utilization is well-balanced with peak 68% during academic hours.', 'Current dynamic QoS profile is effective; maintain standard threshold.'),
        (resource_ids[2], 'optimization', 'MEDIUM', 'Computing Lab A shows 88% peak occupancy during 14:00-17:00 with zero ghost load at night.', 'High operational efficiency achieved through smart shutoff automation.')
    ]
    cursor.executemany("""
    INSERT INTO insights (resource_id, type, severity, description, recommendation, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now', '-2 hours'))
    """, initial_insights)

    initial_alerts = [
        (resource_ids[1], 'CRITICAL', 'Water flow threshold exceeded: 88 L/min sustained flow in Utility Building B', 'Active', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        (resource_ids[0], 'HIGH', 'Peak demand alert: Power grid approached 84% capacity during afternoon ramp', 'Active', (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')),
        (resource_ids[5], 'MEDIUM', 'Resource underutilization notice: Robotics lab average usage 28% below target', 'Active', (datetime.now() - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')),
        (resource_ids[4], 'LOW', 'Scheduled maintenance check: Bandwidth QoS auto-tune completed successfully', 'Resolved', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'))
    ]
    cursor.executemany("""
    INSERT INTO alerts (resource_id, severity, message, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, initial_alerts)

    initial_recs = [
        (resource_ids[0], 'Implement Peak Electricity Load-Shedding', 'Shift auxiliary charging stations and heavy HVAC compressor cycles to off-peak hours (pre-cooling protocol).', 'Estimated 18% reduction in peak demand electricity bills (~$1,250/mo)', 'HIGH', 'Pending'),
        (resource_ids[1], 'Automated Solenoid Valve Leak Isolation', 'Deploy rapid shut-off solenoid command to Block B secondary loop to halt continuous midnight water loss.', 'Immediate prevention of 4,200 Liters/day clean water loss', 'CRITICAL', 'Pending'),
        (resource_ids[2], 'Automate Idle Workstation Sleep State', 'Configure automated active directory wake-on-LAN and zero-occupancy sleep timeout after 15 min.', 'Saves ~240 kWh monthly and extends hardware component lifespan', 'MEDIUM', 'Applied'),
        (resource_ids[5], 'Consolidate IoT Research Server Racks', 'Migrate low-throughput test containers into a single physical virtualization host.', 'Reduces energy footprint by 45% for Innovation Hub', 'MEDIUM', 'Pending')
    ]
    cursor.executemany("""
    INSERT INTO recommendations (resource_id, title, description, expected_benefit, priority, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, initial_recs)

    initial_actions = [
        ("Surge Water Leakage Emergency Cutoff", resource_ids[1], "Flow > 75 L/min at 02:30", "Simulated auxiliary pipe valve isolation & alert dispatched to facility engineer", "Executed", (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')),
        ("Zero-Occupancy Ghost Power Cutoff", resource_ids[2], "Occupancy = 0 with 38 active units at 21:00", "Switched 38 idle terminals to Eco-Sleep mode", "Executed", (datetime.now() - timedelta(hours=14)).strftime('%Y-%m-%d %H:%M:%S')),
        ("Peak Demand Electricity Load-Shedding", resource_ids[0], "Grid load reached 418 kWh (83.6%) at 14:15", "Dimmed decorative foyer illumination and throttled chilled water pump #3 by 12%", "Executed", (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
        ("Dynamic Network QoS Bandwidth Throttling", resource_ids[4], "Core bandwidth reached 890 Mbps at 16:45", "Allocated 70% priority queue to Video Conferencing & LMS servers", "Simulated", (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'))
    ]
    cursor.executemany("""
    INSERT INTO automation_actions (rule_name, resource_id, trigger, action, status, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, initial_actions)

    conn.commit()
    conn.close()
    print("Database initialized and successfully seeded with realistic sample data!")

if __name__ == '__main__':
    seed_data(force=True)

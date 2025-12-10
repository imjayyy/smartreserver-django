# shop_api/database_manager.py
import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
import random
import time
import re
from typing import Dict, List, Tuple, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, base_path: str = None):
        """Initialize with your exact structure"""
        if base_path is None:
            # Root: C:\DjangoApp\DATABASE\
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.base_path = os.path.join(project_root, "DATABASE")
        else:
            self.base_path = base_path
        
        logger.info(f"DatabaseManager initialized with base path: {self.base_path}")
        
        # Create directories if they don't exist
        os.makedirs(self.base_path, exist_ok=True)
    
    def get_shop_path(self, shop_id: str) -> str:
        """Get path to shop directory: DATABASE/SHOP_ID/"""
        return os.path.join(self.base_path, shop_id)
    
    def shop_exists(self, shop_id: str) -> bool:
        """Check if a shop directory exists"""
        shop_path = self.get_shop_path(shop_id)
        return os.path.exists(shop_path)
    
    def _extract_shop_number(self, shop_id: str) -> str:
        """Extract shop number from shop_id (e.g., BILLYS-SHOP-0001 -> 0001)"""
        # Extract the last 4 digits or the number part
        match = re.search(r'(\d{4})$', shop_id)
        if match:
            return match.group(1)
        else:
            # Try to find any number in the shop_id
            numbers = re.findall(r'\d+', shop_id)
            if numbers:
                return numbers[-1].zfill(4)  # Pad with zeros to make 4 digits
            else:
                # Default to 0001 if no number found
                return "0001"
    
    def load_shop_context(self, shop_id: str) -> Dict[str, Any]:
        """Load shop details and services from JSON files using your naming pattern"""
        if not self.shop_exists(shop_id):
            raise FileNotFoundError(f"Shop {shop_id} not found in {self.base_path}")
        
        shop_path = self.get_shop_path(shop_id)
        shop_number = self._extract_shop_number(shop_id)
        
        # Load details.json (pattern: 0001details.json)
        details_patterns = [
            f"{shop_number}details.json",
            f"details{shop_number}.json",
            "details.json"
        ]
        
        details_file = None
        for pattern in details_patterns:
            potential_file = os.path.join(shop_path, pattern)
            if os.path.exists(potential_file):
                details_file = potential_file
                break
        
        if not details_file:
            # Try to find any file with "details" in the name
            for file in os.listdir(shop_path):
                if "detail" in file.lower() and file.endswith('.json'):
                    details_file = os.path.join(shop_path, file)
                    break
        
        if not details_file or not os.path.exists(details_file):
            raise FileNotFoundError(f"Details file not found for shop {shop_id}. Looked for: {details_patterns}")
        
        with open(details_file, 'r') as f:
            shop_details = json.load(f)
        
        # Load services.json (pattern: services0001.json)
        services_patterns = [
            f"services{shop_number}.json",
            f"{shop_number}services.json",
            "services.json"
        ]
        
        services_file = None
        for pattern in services_patterns:
            potential_file = os.path.join(shop_path, pattern)
            if os.path.exists(potential_file):
                services_file = potential_file
                break
        
        if not services_file:
            # Try to find any file with "services" in the name
            for file in os.listdir(shop_path):
                if "service" in file.lower() and file.endswith('.json'):
                    services_file = os.path.join(shop_path, file)
                    break
        
        if not services_file or not os.path.exists(services_file):
            raise FileNotFoundError(f"Services file not found for shop {shop_id}. Looked for: {services_patterns}")
        
        with open(services_file, 'r') as f:
            services = json.load(f)
        
        logger.info(f"Loaded shop {shop_id}: details from {os.path.basename(details_file)}, services from {os.path.basename(services_file)}")
        
        return {
            'shop_details': shop_details,
            'services': services
        }
    
    def get_reservation_db_path(self, shop_id: str) -> str:
        """Get path to shop's Reservation.db using your pattern"""
        shop_path = self.get_shop_path(shop_id)
        shop_number = self._extract_shop_number(shop_id)
        
        # Try patterns in order
        db_patterns = [
            f"Reservation{shop_number}.db",
            f"Reservation.db",
            f"{shop_number}reservation.db"
        ]
        
        for pattern in db_patterns:
            db_path = os.path.join(shop_path, pattern)
            if os.path.exists(db_path):
                return db_path
        
        # If no existing file, create with pattern: Reservation{shop_number}.db
        return os.path.join(shop_path, f"Reservation{shop_number}.db")
    
    @contextmanager
    def get_reservation_connection(self, shop_id: str):
        """Context manager for shop's Reservation.db connection"""
        db_path = self.get_reservation_db_path(shop_id)
        
        # Create shop directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create reservations table if it doesn't exist
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT,
                reservation_date DATE NOT NULL,
                reservation_time TIME NOT NULL,
                party_size INTEGER DEFAULT 1,
                service_type TEXT DEFAULT 'General',
                status TEXT DEFAULT 'confirmed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reservations_date_time 
            ON reservations(reservation_date, reservation_time)
        ''')
        
        conn.commit()
        
        try:
            yield conn
        finally:
            conn.close()
    
    def check_availability(self, shop_id: str, date: str, time: str) -> bool:
        """Check if a time slot is available in Reservation.db"""
        if not date or not time:
            return False
        
        try:
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()
                
                # Get shop policy
                shop_context = self.load_shop_context(shop_id)
                max_reservations = shop_context['shop_details'].get(
                    'reservation_policy', {}
                ).get('max_reservations_per_hour', 4)
                
                # Count reservations for the given date and time
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM reservations 
                    WHERE reservation_date = ? 
                      AND reservation_time = ? 
                      AND status = 'confirmed'
                ''', (date, time))
                
                result = cursor.fetchone()
                count = result['count'] if result else 0
                
                logger.info(f"Availability check for {shop_id}: {count}/{max_reservations} slots booked")
                return count < max_reservations
                
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False
    
    def save_reservation(self, shop_id: str, reservation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a reservation to shop's Reservation.db"""
        try:
            # Generate unique reservation ID
            reservation_id = f"RES{int(time.time())}{random.randint(1000, 9999)}"
            
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO reservations 
                    (reservation_id, customer_name, phone_number, email, 
                     reservation_date, reservation_time, party_size, service_type, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    reservation_id,
                    reservation_data.get('customer_name', 'Customer'),
                    reservation_data.get('phone_number'),
                    reservation_data.get('email', ''),
                    reservation_data.get('date'),
                    reservation_data.get('time'),
                    int(reservation_data.get('party_size', 1)),
                    reservation_data.get('service_type', 'General'),
                    'confirmed'
                ))
                
                conn.commit()
                
                logger.info(f"Reservation saved to {shop_id}: {reservation_id}")
                
                return {
                    'reservation_id': reservation_id,
                    'success': True,
                    'customer_name': reservation_data.get('customer_name', 'Customer'),
                    'date': reservation_data.get('date'),
                    'time': reservation_data.get('time'),
                    'party_size': reservation_data.get('party_size'),
                    'shop_id': shop_id
                }
                
        except Exception as e:
            logger.error(f"Error saving reservation: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_reservation(self, shop_id: str, reservation_id: str) -> Dict[str, Any]:
        """Cancel a reservation in Reservation.db"""
        try:
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()
                
                # Check if reservation exists
                cursor.execute('''
                    SELECT * FROM reservations 
                    WHERE reservation_id = ? AND status = 'confirmed'
                ''', (reservation_id,))
                
                reservation = cursor.fetchone()
                
                if not reservation:
                    return {'success': False, 'error': 'Reservation not found'}
                
                # Update status to cancelled
                cursor.execute('''
                    UPDATE reservations 
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE reservation_id = ?
                ''', (reservation_id,))
                
                conn.commit()
                
                logger.info(f"Reservation cancelled: {reservation_id} in {shop_id}")
                
                return {
                    'success': True,
                    'reservation_id': reservation_id,
                    'message': 'Reservation cancelled successfully'
                }
                
        except Exception as e:
            logger.error(f"Error cancelling reservation: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_all_shops(self) -> List[Dict[str, Any]]:
        """List all shops in DATABASE directory"""
        shops = []
        
        if not os.path.exists(self.base_path):
            return shops
        
        for item in os.listdir(self.base_path):
            # Skip "Django Main DB" folder
            if item == "Django Main DB":
                continue
                
            shop_path = os.path.join(self.base_path, item)
            if os.path.isdir(shop_path):
                # Try to load shop details using the new pattern
                try:
                    # Extract shop number
                    shop_number = self._extract_shop_number(item)
                    
                    # Look for details file
                    details_file = None
                    for file in os.listdir(shop_path):
                        if "detail" in file.lower() and file.endswith('.json'):
                            details_file = os.path.join(shop_path, file)
                            break
                    
                    if details_file and os.path.exists(details_file):
                        with open(details_file, 'r') as f:
                            shop_details = json.load(f)
                            
                        shops.append({
                            'shop_id': item,
                            'shop_name': shop_details.get('shop_name', 'Unknown Shop'),
                            'address': shop_details.get('address', ''),
                            'phone': shop_details.get('phone', ''),
                            'shop_number': shop_number
                        })
                except Exception as e:
                    logger.warning(f"Could not load shop {item}: {e}")
        
        return shops
    
    def get_django_db_path(self) -> str:
        """Get path to Django main database"""
        # Check if Django Main DB folder exists
        django_db_folder = os.path.join(self.base_path, "Django Main DB")
        if not os.path.exists(django_db_folder):
            os.makedirs(django_db_folder, exist_ok=True)
        
        # Return path to SQLite database in Django Main DB folder
        return os.path.join(django_db_folder, "django_main.db")
    
    # In database_manager.py, add these methods:

    def find_reservation_by_phone(self, shop_id: str, phone_number: str) -> Dict[str, Any]:
        """Find reservation by phone number"""
        try:
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                SELECT * FROM reservations 
                WHERE phone_number = ? AND status = 'confirmed'
                ORDER BY reservation_date DESC, reservation_time DESC
                LIMIT 1
                ''', (phone_number,))
            
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error finding reservation by phone: {e}")
            return None

    def find_reservation_by_email(self, shop_id: str, email: str) -> Dict[str, Any]:
        """Find reservation by email"""
        try:
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()
            
                cursor.execute('''
                    SELECT * FROM reservations 
                    WHERE email = ? AND status = 'confirmed'
                    ORDER BY reservation_date DESC, reservation_time DESC
                    LIMIT 1
                ''', (email,))
            
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error finding reservation by email: {e}")
            return None

    def cancel_reservation_enhanced(self, shop_id: str, 
                                   reservation_id: str = None, 
                                   phone_number: str = None, 
                                    email: str = None) -> Dict[str, Any]:
        """Cancel reservation using multiple search methods"""
        try:
            with self.get_reservation_connection(shop_id) as conn:
                cursor = conn.cursor()
            
                # Search by different criteria
                if reservation_id:
                    cursor.execute('''
                    SELECT * FROM reservations 
                    WHERE reservation_id = ? AND status = 'confirmed'
                    ''', (reservation_id,))
                elif phone_number:
                    cursor.execute('''
                    SELECT * FROM reservations 
                    WHERE phone_number = ? AND status = 'confirmed'
                    ORDER BY reservation_date DESC, reservation_time DESC
                    LIMIT 1
                    ''', (phone_number,))
                elif email:
                    cursor.execute('''
                    SELECT * FROM reservations 
                    WHERE email = ? AND status = 'confirmed'
                    ORDER BY reservation_date DESC, reservation_time DESC
                    LIMIT 1
                    ''', (email,))
                else:
                    return {'success': False, 'error': 'No search criteria provided'}

                reservation = cursor.fetchone()

                if not reservation:
                    return {'success': False, 'error': 'Reservation not found'}

                # Update status to cancelled
                cursor.execute('''
                UPDATE reservations 
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE reservation_id = ?
                ''', (reservation['reservation_id'],))

                conn.commit()

                logger.info(f"Reservation cancelled: {reservation['reservation_id']} in {shop_id}")

                return {
                'success': True,
                'reservation_id': reservation['reservation_id'],
                'customer_name': reservation['customer_name'],
                'date': reservation['reservation_date'],
                'time': reservation['reservation_time'],
                'message': 'Reservation cancelled successfully'
                }
            
        except Exception as e:
            logger.error(f"Error cancelling reservation: {e}")
            return {'success': False, 'error': str(e)}
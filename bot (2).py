import os
import logging
import asyncio
import requests
import json
import base64
import sqlite3
import re
import urllib.parse
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden

# Bot Configuration
BOT_TOKEN = "8402987208:AAHeFlNfEyqEAS7qp93inqbfSrMavMV60oQ*"

# Admin configuration - अपना Telegram ID यहाँ डालें
ADMIN_IDS = [8333354105]  # Replace with your Telegram user ID

# Database setup
DB_NAME = "bot_data.db"

# Bot status
BOT_ACTIVE = True

# Store groups where bot is added
bot_groups = []

# ALL APIs Configuration
ENCODED_MOBILE_API = "aHR0cHM6Ly9kZW1vbi50YWl0YW54LndvcmtlcnMuZGV2Lz9tb2JpbGU9"
ENCODED_AADHAAR_API = "aHR0cHM6Ly9yYWphbi1hYWRoYXItdG9mYW1pbHkudmVyY2VsLmFwcC9mZXRjaD9rZXk9UkFKQU4mYWFkaGFhcj17aWR9"
ENCODED_VOICE_API = "aHR0cHM6Ly9kZW1vbi50YWl0YW54LndvcmtlcnMuZGV2L3NldC1sZQ=="

# NEW APIs
VEHICLE_API_1 = "http://dark-op.dev-is.xyz/?key=wasdark&vehicle={vehicle}"
VEHICLE_API_2 = "https://hexavaultvehicleinfoweb.onrender.com/lookup?rc={rc}"
AADHAAR_API_NEW = "http://dark-op.dev-is.xyz/?key=wasdark&aadhaar={aadhaar}"
FAMILY_API = "https://addartofamily.vercel.app/fetch?aadhaar={aadhaar}&key=fxt"
PINCODE_API = "https://api.postalpincode.in/pincode/{pincode}"
UPI_API = "https://gaurav-kr-upi-info.vercel.app/api/upi?key=999&upi_id={upi_id}"

# NEW PERSONAL INFO APIs - ADDED
PERSONAL_AGGREGATE_API = "https://all-in-one-personal-api.vercel.app/api/aggregate?number={number}"
CALL_TRACE_API = "https://ab-calltraceapi.vercel.app/info?number={number}"
FAMILY_INFO_API = "https://addartofamily.vercel.app/fetch?aadhaar={aadhaar}&key=fxt"

# 🔥 NEW UPDATED APIs - NUMBER & AADHAAR (FIXED)
NEW_NUMBER_API = "https://ox-tawny.vercel.app/search_mobile?mobile={number}&api_key=gavravrandigey"
NEW_AADHAAR_API = "http://splexxo-ad-api.vercel.app/api/aadhaar?aadhaar={aadhaar}&key=SPLEXXO"

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id TEXT PRIMARY KEY,
            group_name TEXT,
            group_link TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User groups table (to track user's groups)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_groups (
            user_id INTEGER,
            group_id TEXT,
            group_name TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, group_id)
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, first_name: str, last_name: str = ""):
    """Add user to database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()

def add_group(group_id: str, group_name: str, group_link: str = ""):
    """Add group to database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO groups (group_id, group_name, group_link)
        VALUES (?, ?, ?)
    ''', (group_id, group_name, group_link))
    
    conn.commit()
    conn.close()

def add_user_group(user_id: int, group_id: str, group_name: str):
    """Add user's group to database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO user_groups (user_id, group_id, group_name)
        VALUES (?, ?, ?)
    ''', (user_id, group_id, group_name))
    
    conn.commit()
    conn.close()

def get_user_groups(user_id: int):
    """Get all groups for a user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_groups WHERE user_id = ? ORDER BY added_date DESC', (user_id,))
    groups = cursor.fetchall()
    
    conn.close()
    return groups

def get_all_groups():
    """Get all groups from database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM groups ORDER BY added_date DESC')
    groups = cursor.fetchall()
    
    conn.close()
    return groups

def get_group_count():
    """Get total group count"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM groups')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def remove_group(group_id: str):
    """Remove group"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM groups WHERE group_id = ?', (group_id,))
    
    conn.commit()
    conn.close()

# Initialize database
init_database()

# 🔥 IMPROVED PASSWORD GENERATION FUNCTIONS
def generate_password(length=12):
    """Generate strong random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

def generate_email_from_name(name, number):
    """Generate email from name and number - IMPROVED"""
    try:
        # Clean name for email - only keep alphabets and convert to lowercase
        clean_name = re.sub(r'[^a-zA-Z]', '', name).lower()
        
        # If name is too short, use default
        if len(clean_name) < 3:
            clean_name = "user"
        
        # Email providers
        providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        
        # Generate multiple email variations using the ACTUAL name
        emails = [
            f"{clean_name}{number}@{random.choice(providers)}",  # name + full number
            f"{clean_name}.{number}@{random.choice(providers)}",  # name.number
            f"{clean_name}{number[-4:]}@{random.choice(providers)}",  # name + last 4 digits
            f"{clean_name}{random.randint(1000,9999)}@{random.choice(providers)}"  # name + random
        ]
        
        return emails
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        # Return default emails if error
        return [f"user{number}@gmail.com", f"user.{number}@yahoo.com"]

def generate_facebook_credentials(number, name):
    """Generate Facebook ID and password - IMPROVED"""
    try:
        # Clean name for Facebook ID
        clean_name = re.sub(r'[^a-zA-Z]', '', name).lower()
        if len(clean_name) < 3:
            clean_name = "user"
        
        # Facebook ID variations using ACTUAL name and number
        facebook_ids = [
            f"{clean_name}.{number}",  # name.number
            f"{clean_name}{number}",  # namenumber
            f"fb.{clean_name}.{number}",  # fb.name.number
            f"{clean_name}_{number}",  # name_number
            f"{clean_name}{number[-6:]}",  # name + last 6 digits
            f"{clean_name}.official"  # name.official
        ]
        
        # Generate password based on name and number
        base_password = f"{clean_name}{number[-4:]}{random.randint(100,999)}"
        facebook_password = base_password + "".join(random.choices("!@#$%^&*", k=2))
        
        return {
            "facebook_id": random.choice(facebook_ids),
            "facebook_password": facebook_password
        }
    except Exception as e:
        logger.error(f"Error generating Facebook credentials: {e}")
        return {
            "facebook_id": f"user.{number}",
            "facebook_password": f"user{number}@123"
        }

# 🔥 COMPLETELY FIXED NEW API FUNCTIONS
def _call_new_number_api(number):
    """Call NEW Number API - COMPLETELY FIXED VERSION"""
    try:
        logger.info(f"Fetching NEW number info for: {number}")
        
        url = NEW_NUMBER_API.format(number=number)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Content-Type': 'application/json',
            'Referer': 'http://hackingsocietyai.great-site.net/',
            'Origin': 'http://hackingsocietyai.great-site.net'
        }
        
        # Use session to handle cookies and redirects
        session = requests.Session()
        resp = session.get(url, timeout=30, headers=headers, allow_redirects=True)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"New Number API Status Code {resp.status_code}"}
        
        response_text = resp.text.strip()
        
        # Check if we got the JavaScript redirect page
        if "aes.js" in response_text and "slowAES.decrypt" in response_text:
            logger.info("Detected JavaScript redirect, extracting redirect URL...")
            
            # Extract the redirect URL from JavaScript
            redirect_match = re.search(r'location\.href="([^"]+)"', response_text)
            if redirect_match:
                redirect_url = redirect_match.group(1)
                logger.info(f"Found redirect URL: {redirect_url}")
                
                # Follow the redirect with the same session (to maintain cookies)
                redirect_resp = session.get(redirect_url, timeout=30, headers=headers, allow_redirects=True)
                
                if redirect_resp.status_code == 200:
                    # Try to parse as JSON
                    try:
                        final_data = redirect_resp.json()
                        logger.info("✅ Successfully got JSON response from redirect")
                        return {"done": True, "results": final_data, "api_name": "New Number Information"}
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error from redirect: {e}")
                        # If not JSON, try to extract JSON from text
                        json_match = re.search(r'\{.*\}', redirect_resp.text, re.DOTALL)
                        if json_match:
                            try:
                                json_data = json.loads(json_match.group())
                                return {"done": True, "results": json_data, "api_name": "New Number Information"}
                            except Exception as json_err:
                                logger.error(f"Failed to extract JSON: {json_err}")
                        
                        # Return the text response
                        return {"done": True, "results": {"raw_response": redirect_resp.text[:500]}, "api_name": "New Number Information"}
        
        # If we get here, try direct JSON parsing
        try:
            json_data = resp.json()
            return {"done": True, "results": json_data, "api_name": "New Number Information"}
        except json.JSONDecodeError:
            # Try to find JSON in the response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group())
                    return {"done": True, "results": json_data, "api_name": "New Number Information"}
                except:
                    pass
        
        # If all else fails, return formatted text
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        formatted_data = {"response_lines": lines[:10]}  # Limit to first 10 lines
        
        return {"done": True, "results": formatted_data, "api_name": "New Number Information"}
        
    except requests.exceptions.Timeout:
        return {"done": False, "results": "New Number API timeout", "api_name": "New Number Information"}
    except Exception as e:
        logger.error(f"New Number API error: {str(e)}")
        return {"done": False, "results": f"New Number API request error: {str(e)}", "api_name": "New Number Information"}

def _call_new_aadhaar_api(aadhaar_number):
    """Call NEW Aadhaar API - FIXED VERSION"""
    try:
        logger.info(f"Fetching NEW Aadhaar info for: {aadhaar_number}")
        
        url = NEW_AADHAAR_API.format(aadhaar=aadhaar_number)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        session = requests.Session()
        resp = session.get(url, timeout=30, headers=headers)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"New Aadhaar API Status Code {resp.status_code}"}
        
        response_text = resp.text.strip()
        
        # Try direct JSON parsing first
        try:
            json_data = resp.json()
            return {"done": True, "results": json_data, "api_name": "New Aadhaar Information"}
        except json.JSONDecodeError:
            # Try to find JSON in response text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group())
                    return {"done": True, "results": json_data, "api_name": "New Aadhaar Information"}
                except:
                    pass
            
            # Return formatted text response
            lines = [line.strip() for line in response_text.split('\n') if line.strip()]
            formatted_data = {"response_lines": lines[:10]}
            return {"done": True, "results": formatted_data, "api_name": "New Aadhaar Information"}
        
    except requests.exceptions.Timeout:
        return {"done": False, "results": "New Aadhaar API timeout", "api_name": "New Aadhaar Information"}
    except Exception as e:
        logger.error(f"New Aadhaar API error: {str(e)}")
        return {"done": False, "results": f"New Aadhaar API request error: {str(e)}", "api_name": "New Aadhaar Information"}

# ALL API FUNCTIONS - FIXED VERSION
def decode_api(url):
    """Decode base64 encoded API URL"""
    try:
        return base64.b64decode(url).decode('utf-8')
    except:
        return None

def _call_mobile_api(number):
    """Call mobile API with encoded URL"""
    try:
        logger.info(f"Fetching mobile info for: {number}")
        
        mobile_api = decode_api(ENCODED_MOBILE_API)
        if not mobile_api:
            return {"done": False, "results": "API configuration error"}
            
        resp = requests.get(mobile_api + str(number), timeout=15)
        if resp.status_code != 200:
            return {"done": False, "results": f"Mobile API Status Code {resp.status_code}"}
        
        raw = resp.text.strip()
        start = raw.find('{')
        end = raw.rfind('}')
        
        if start == -1 or end == -1:
            return {"done": False, "results": "Mobile API Invalid response format"}
        
        clean = raw[start:end+1]
        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Mobile API JSON decode error: {str(e)}"}
        
        if not isinstance(data, dict):
            return {"done": False, "results": "Mobile API Invalid response format"}
            
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Mobile Information"}
        
    except Exception as e:
        logger.error(f"Mobile API error: {str(e)}")
        return {"done": False, "results": f"Mobile API request error: {str(e)}", "api_name": "Mobile Information"}

def _call_voice_api(number):
    """Call Voice/Set-le API - FIXED VERSION"""
    try:
        logger.info(f"Fetching voice info for: {number}")
        
        voice_api = decode_api(ENCODED_VOICE_API)
        if not voice_api:
            return {"done": False, "results": "Voice API configuration error"}
            
        resp = requests.post(
            voice_api,
            json={"number": str(number)},
            timeout=15
        )
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Voice API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            text_response = resp.text.strip()
            if text_response:
                return {"done": True, "results": {"voice_data": clean_text_value(text_response)}, "api_name": "Voice/Set-le Information"}
            return {"done": False, "results": f"Voice API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Voice/Set-le Information"}
        
    except Exception as e:
        logger.error(f"Voice API error: {str(e)}")
        return {"done": False, "results": f"Voice API request error: {str(e)}", "api_name": "Voice/Set-le Information"}

def _call_personal_aggregate_api(number):
    """Call Personal Aggregate API"""
    try:
        logger.info(f"Fetching personal aggregate info for: {number}")
        
        url = PERSONAL_AGGREGATE_API.format(number=number)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        resp = requests.get(url, timeout=20, headers=headers)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Personal Aggregate API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Personal Aggregate API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Personal Aggregate Information"}
        
    except Exception as e:
        logger.error(f"Personal Aggregate API error: {str(e)}")
        return {"done": False, "results": f"Personal Aggregate API request error: {str(e)}", "api_name": "Personal Aggregate Information"}

def _call_call_trace_api(number):
    """Call Call Trace API"""
    try:
        logger.info(f"Fetching call trace info for: {number}")
        
        url = CALL_TRACE_API.format(number=number)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        resp = requests.get(url, timeout=20, headers=headers)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Call Trace API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Call Trace API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Call Trace Information"}
        
    except Exception as e:
        logger.error(f"Call Trace API error: {str(e)}")
        return {"done": False, "results": f"Call Trace API request error: {str(e)}", "api_name": "Call Trace Information"}

# OTHER API FUNCTIONS (Vehicle, Aadhaar, Family, Pincode, UPI)
def _call_vehicle_api_1(vehicle_number):
    """Call Vehicle API 1"""
    try:
        logger.info(f"Fetching vehicle info from API 1 for: {vehicle_number}")
        
        url = VEHICLE_API_1.format(vehicle=vehicle_number)
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Vehicle API 1 Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Vehicle API 1 JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Vehicle Information"}
        
    except Exception as e:
        logger.error(f"Vehicle API 1 error: {str(e)}")
        return {"done": False, "results": f"Vehicle API 1 request error: {str(e)}", "api_name": "Vehicle Information"}

def _call_vehicle_api_2(rc_number):
    """Call Vehicle API 2"""
    try:
        logger.info(f"Fetching vehicle info from API 2 for: {rc_number}")
        
        url = VEHICLE_API_2.format(rc=rc_number)
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Vehicle API 2 Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Vehicle API 2 JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Vehicle Information"}
        
    except Exception as e:
        logger.error(f"Vehicle API 2 error: {str(e)}")
        return {"done": False, "results": f"Vehicle API 2 request error: {str(e)}", "api_name": "Vehicle Information"}

def _call_aadhaar_api_new(aadhaar_number):
    """Call New Aadhaar API"""
    try:
        logger.info(f"Fetching Aadhaar info from new API for: {aadhaar_number}")
        
        url = AADHAAR_API_NEW.format(aadhaar=aadhaar_number)
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Aadhaar API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Aadhaar API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Aadhaar Information"}
        
    except Exception as e:
        logger.error(f"Aadhaar API error: {str(e)}")
        return {"done": False, "results": f"Aadhaar API request error: {str(e)}", "api_name": "Aadhaar Information"}

def _call_family_api(aadhaar_number):
    """Call Family Information API"""
    try:
        logger.info(f"Fetching family info for Aadhaar: {aadhaar_number}")
        
        url = FAMILY_API.format(aadhaar=aadhaar_number)
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Family API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Family API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Family Information"}
        
    except Exception as e:
        logger.error(f"Family API error: {str(e)}")
        return {"done": False, "results": f"Family API request error: {str(e)}", "api_name": "Family Information"}

def _call_family_info_api(aadhaar_number):
    """Call Family Info API (Alternative)"""
    try:
        logger.info(f"Fetching family info for Aadhaar: {aadhaar_number}")
        
        url = FAMILY_INFO_API.format(aadhaar=aadhaar_number)
        resp = requests.get(url, timeout=15)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"Family Info API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Family Info API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "Family Information (Alternative)"}
        
    except Exception as e:
        logger.error(f"Family Info API error: {str(e)}")
        return {"done": False, "results": f"Family Info API request error: {str(e)}", "api_name": "Family Information (Alternative)"}

def _call_pincode_api(pincode):
    """Call Pincode API - FIXED VERSION"""
    try:
        logger.info(f"Fetching pincode info for: {pincode}")
        
        if not pincode or len(pincode) != 6:
            return {"done": False, "results": "Invalid pincode"}
            
        url = PINCODE_API.format(pincode=pincode)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, timeout=20, headers=headers)
            
        if resp.status_code != 200:
            return {"done": False, "results": f"Pincode API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"Pincode API JSON decode error: {str(e)}"}
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return {"done": False, "results": "No pincode data found"}
            
        post_office_data = data[0]
        
        if post_office_data.get('Status') != 'Success':
            error_msg = post_office_data.get('Message', 'Unknown error')
            return {"done": False, "results": f"Pincode API Error: {error_msg}"}
        
        post_offices = post_office_data.get('PostOffice', [])
        
        if not post_offices:
            return {"done": False, "results": "No post office found for this pincode"}
        
        pincode_info = {
            "pincode": pincode,
            "post_offices": []
        }
        
        for office in post_offices[:3]:
            clean_office = {
                "name": clean_text_value(office.get('Name', 'N/A')),
                "branch_type": clean_text_value(office.get('BranchType', 'N/A')),
                "district": clean_text_value(office.get('District', 'N/A')),
                "state": clean_text_value(office.get('State', 'N/A')),
                "country": clean_text_value(office.get('Country', 'India'))
            }
            pincode_info["post_offices"].append(clean_office)
        
        return {"done": True, "results": pincode_info, "api_name": "Pincode Information"}
        
    except Exception as e:
        logger.error(f"Pincode API error: {str(e)}")
        return {"done": False, "results": f"Pincode API request error: {str(e)}", "api_name": "Pincode Information"}

def _call_upi_api(upi_id):
    """Call UPI Information API"""
    try:
        logger.info(f"Fetching UPI info for: {upi_id}")
        
        url = UPI_API.format(upi_id=upi_id)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resp = requests.get(url, timeout=15, headers=headers)
        
        if resp.status_code != 200:
            return {"done": False, "results": f"UPI API Status Code {resp.status_code}"}
        
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            return {"done": False, "results": f"UPI API JSON decode error: {str(e)}"}
        
        data = clean_api_response(data)
        return {"done": True, "results": data, "api_name": "UPI Information"}
        
    except Exception as e:
        logger.error(f"UPI API error: {str(e)}")
        return {"done": False, "results": f"UPI API request error: {str(e)}", "api_name": "UPI Information"}

# DATA EXTRACTION FUNCTIONS
def extract_vehicle_numbers(data):
    """Extract vehicle numbers from data"""
    vehicle_numbers = []
    
    def search_vehicle(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    vehicle_pattern = r'[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{1,4}'
                    matches = re.findall(vehicle_pattern, value.upper())
                    vehicle_numbers.extend(matches)
                elif isinstance(value, (dict, list)):
                    search_vehicle(value)
        elif isinstance(obj, list):
            for item in obj:
                search_vehicle(item)
    
    search_vehicle(data)
    return list(set(vehicle_numbers))

def extract_aadhaar_numbers(data):
    """Extract Aadhaar numbers from data"""
    aadhaar_numbers = []
    
    def search_aadhaar(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.isdigit() and len(value) == 12:
                    aadhaar_numbers.append(value)
                elif isinstance(value, (dict, list)):
                    search_aadhaar(value)
        elif isinstance(obj, list):
            for item in obj:
                search_aadhaar(item)
    
    search_aadhaar(data)
    return list(set(aadhaar_numbers))

def extract_pincodes(data):
    """Extract pincodes from data"""
    pincodes = []
    
    def search_pincode(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    pincode_pattern = r'\b[1-9][0-9]{5}\b'
                    matches = re.findall(pincode_pattern, str(value))
                    pincodes.extend(matches)
                elif isinstance(value, (dict, list)):
                    search_pincode(value)
        elif isinstance(obj, list):
            for item in obj:
                search_pincode(item)
    
    search_pincode(data)
    return list(set(pincodes))

def extract_mobile_numbers(data):
    """Extract mobile numbers from data for UPI generation"""
    mobile_numbers = []
    
    def search_mobile(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    mobile_pattern = r'\b[6-9][0-9]{9}\b'
                    matches = re.findall(mobile_pattern, value)
                    mobile_numbers.extend(matches)
                elif isinstance(value, (dict, list)):
                    search_mobile(value)
        elif isinstance(obj, list):
            for item in obj:
                search_mobile(item)
    
    search_mobile(data)
    return list(set(mobile_numbers))

def extract_names(data):
    """Extract names from data for email generation - IMPROVED"""
    names = []
    
    def search_names(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                # More comprehensive name field detection
                if any(name_key in key.lower() for name_key in ['name', 'firstname', 'fullname', 'person', 'user', 'fname', 'first_name', 'holder']):
                    if isinstance(value, str) and len(value) > 2 and value != "N/A" and not value.isdigit():
                        # Clean the name - keep only alphabets and spaces
                        clean_name = re.sub(r'[^a-zA-Z\s]', '', value).strip()
                        if len(clean_name) >= 2:
                            names.append(clean_name)
                elif isinstance(value, (dict, list)):
                    search_names(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_names(item, f"{path}[{i}]")
    
    search_names(data)
    
    # Remove duplicates and return
    unique_names = []
    for name in names:
        if name not in unique_names and len(name) >= 2:
            unique_names.append(name)
    
    return unique_names

def generate_upi_ids(mobile_numbers):
    """Generate UPI IDs from mobile numbers"""
    upi_ids = []
    upi_providers = ['@ybl', '@paytm', '@oksbi', '@axl', '@ibl']
    
    for mobile in mobile_numbers:
        for provider in upi_providers:
            upi_ids.append(f"{mobile}{provider}")
    
    return upi_ids

def create_google_maps_link(address):
    """Create Google Maps link from address"""
    if not address or address == "N/A":
        return None
    
    cleaned_address = re.sub(r'[^\w\s,.-]', '', address)
    cleaned_address = ' '.join(cleaned_address.split())
    
    if len(cleaned_address) < 5:
        return None
    
    encoded_address = urllib.parse.quote(cleaned_address)
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
    
    return google_maps_url

def extract_addresses(data):
    """Extract addresses from data"""
    addresses = []
    
    def search_address(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if any(addr_key in key.lower() for addr_key in ['address', 'location', 'city', 'village', 'district', 'state', 'add', 'loc']):
                    if isinstance(value, str) and len(value) > 10 and value != "N/A":
                        addresses.append({
                            'field': key,
                            'address': value,
                            'full_path': current_path
                        })
                elif isinstance(value, (dict, list)):
                    search_address(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_address(item, f"{path}[{i}]")
    
    search_address(data)
    return addresses

# 🔥 IMPROVED COMPREHENSIVE SEARCH FUNCTION
def call_all_apis_comprehensive(number):
    """Call ALL APIs and return comprehensive results with IMPROVED features"""
    try:
        logger.info(f"🔍 STARTING COMPREHENSIVE SEARCH FOR: {number}")
        
        all_results = {
            "search_number": number,
            "timestamp": datetime.now().isoformat(),
            "mobile_api": {"done": False, "results": "Not called"},
            "voice_api": {"done": False, "results": "Not called"},
            "personal_aggregate_api": {"done": False, "results": "Not called"},
            "call_trace_api": {"done": False, "results": "Not called"},
            "new_number_api": {"done": False, "results": "Not called"},
            "new_aadhaar_api": {"done": False, "results": "Not called"},
            "vehicle_apis": [],
            "aadhaar_apis": [],
            "family_apis": [],
            "family_info_apis": [],
            "pincode_apis": [],
            "upi_apis": [],
            "google_maps_links": [],
            "extracted_data": {
                "vehicle_numbers": [],
                "aadhaar_numbers": [],
                "pincodes": [],
                "mobile_numbers": [],
                "addresses": [],
                "names": []
            },
            "generated_credentials": {
                "emails": [],
                "facebook_accounts": []
            }
        }
        
        # STEP 1: Call ALL Mobile APIs including NEW ones
        logger.info("📱 Calling Mobile API...")
        mobile_result = _call_mobile_api(number)
        all_results["mobile_api"] = mobile_result
        
        logger.info("🎤 Calling Voice API...")
        voice_result = _call_voice_api(number)
        all_results["voice_api"] = voice_result
        
        logger.info("👤 Calling Personal Aggregate API...")
        personal_aggregate_result = _call_personal_aggregate_api(number)
        all_results["personal_aggregate_api"] = personal_aggregate_result
        
        logger.info("📞 Calling Call Trace API...")
        call_trace_result = _call_call_trace_api(number)
        all_results["call_trace_api"] = call_trace_result
        
        logger.info("🔥 Calling NEW Number API...")
        new_number_result = _call_new_number_api(number)
        all_results["new_number_api"] = new_number_result
        
        # STEP 2: Extract data from ALL APIs
        combined_data = {}
        
        # Combine data from all primary APIs for extraction
        if mobile_result["done"]:
            combined_data.update(mobile_result["results"])
        if personal_aggregate_result["done"]:
            combined_data.update(personal_aggregate_result["results"])
        if call_trace_result["done"]:
            combined_data.update(call_trace_result["results"])
        if new_number_result["done"]:
            combined_data.update(new_number_result["results"])
        
        if combined_data:
            # Extract data from combined results
            vehicle_numbers = extract_vehicle_numbers(combined_data)
            aadhaar_numbers = extract_aadhaar_numbers(combined_data)
            pincodes = extract_pincodes(combined_data)
            mobile_numbers = extract_mobile_numbers(combined_data)
            addresses = extract_addresses(combined_data)
            names = extract_names(combined_data)
            
            all_results["extracted_data"] = {
                "vehicle_numbers": vehicle_numbers,
                "aadhaar_numbers": aadhaar_numbers,
                "pincodes": pincodes,
                "mobile_numbers": mobile_numbers,
                "addresses": addresses,
                "names": names
            }
            
            # 🔥 IMPROVED: Generate Email & Facebook Credentials
            primary_name = None
            if names:
                primary_name = names[0]  # Take the first name found
                logger.info(f"🎯 Primary name found: {primary_name}")
            else:
                # Try to extract name from new number API response specifically
                if new_number_result["done"]:
                    new_number_data = new_number_result["results"]
                    # Look for name in the expected JSON structure
                    if isinstance(new_number_data, dict):
                        if new_number_data.get('success') and new_number_data.get('data'):
                            data = new_number_data['data']
                            if data.get('success') and data.get('result'):
                                for item in data['result']:
                                    if item.get('name'):
                                        primary_name = item['name']
                                        logger.info(f"🎯 Name extracted from new number API: {primary_name}")
                                        break
            
            # Generate credentials based on extracted name
            if primary_name:
                logger.info(f"🔐 Generating credentials for: {primary_name}")
                
                # Generate emails using ACTUAL name
                generated_emails = generate_email_from_name(primary_name, number)
                email_passwords = [generate_password() for _ in generated_emails]
                
                all_results["generated_credentials"]["emails"] = [
                    {"email": email, "password": password} 
                    for email, password in zip(generated_emails, email_passwords)
                ]
                
                # Generate Facebook credentials using ACTUAL name
                facebook_creds = generate_facebook_credentials(number, primary_name)
                all_results["generated_credentials"]["facebook_accounts"] = [facebook_creds]
                
                logger.info(f"✅ Generated {len(generated_emails)} emails and Facebook credentials")
            else:
                # If no names found, use number-based credentials
                logger.info("ℹ️ No name found, using number-based credentials")
                default_emails = generate_email_from_name("user", number)
                email_passwords = [generate_password() for _ in default_emails]
                
                all_results["generated_credentials"]["emails"] = [
                    {"email": email, "password": password} 
                    for email, password in zip(default_emails, email_passwords)
                ]
                
                facebook_creds = generate_facebook_credentials(number, "user")
                all_results["generated_credentials"]["facebook_accounts"] = [facebook_creds]
            
            # Extract and call Vehicle APIs
            for vehicle_num in vehicle_numbers:
                vehicle_result_1 = _call_vehicle_api_1(vehicle_num)
                vehicle_result_2 = _call_vehicle_api_2(vehicle_num)
                all_results["vehicle_apis"].append({
                    "vehicle_number": vehicle_num,
                    "api1_result": vehicle_result_1,
                    "api2_result": vehicle_result_2
                })
            
            # Extract and call Aadhaar APIs including NEW one
            for aadhaar_num in aadhaar_numbers:
                aadhaar_result = _call_aadhaar_api_new(aadhaar_num)
                family_result = _call_family_api(aadhaar_num)
                family_info_result = _call_family_info_api(aadhaar_num)
                new_aadhaar_result = _call_new_aadhaar_api(aadhaar_num)
                
                all_results["aadhaar_apis"].append({
                    "aadhaar_number": aadhaar_num,
                    "aadhaar_result": aadhaar_result,
                    "family_result": family_result,
                    "new_aadhaar_result": new_aadhaar_result
                })
                
                all_results["new_aadhaar_api"] = new_aadhaar_result
            
            # Extract and call Pincode APIs
            for pincode in pincodes:
                pincode_result = _call_pincode_api(pincode)
                all_results["pincode_apis"].append({
                    "pincode": pincode,
                    "result": pincode_result
                })
            
            # Extract mobile numbers and generate UPI IDs
            upi_ids = generate_upi_ids(mobile_numbers)
            for upi_id in upi_ids:
                upi_result = _call_upi_api(upi_id)
                all_results["upi_apis"].append({
                    "upi_id": upi_id,
                    "result": upi_result
                })
            
            # Extract addresses and create Google Maps links
            unique_addresses = {}
            for addr_info in addresses:
                address = addr_info['address']
                if address not in unique_addresses and len(address) > 10:
                    maps_link = create_google_maps_link(address)
                    if maps_link:
                        unique_addresses[address] = {
                            'maps_link': maps_link,
                            'source_field': addr_info['field']
                        }
            
            all_results["google_maps_links"] = [
                {"address": addr, "maps_link": info['maps_link'], "source": info['source_field']}
                for addr, info in unique_addresses.items()
            ]
        
        logger.info(f"✅ COMPREHENSIVE SEARCH COMPLETED FOR: {number}")
        return {"done": True, "results": all_results}
        
    except Exception as e:
        logger.error(f"❌ Error in comprehensive search: {str(e)}")
        return {"done": False, "results": f"Comprehensive search error: {str(e)}"}

# 🔥 IMPROVED FILE GENERATION FUNCTION
def generate_text_file(comprehensive_data):
    """Generate a text file with all the collected information - IMPROVED"""
    try:
        if not comprehensive_data["done"]:
            return None
        
        data = comprehensive_data["results"]
        filename = f"search_results_{data['search_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("🤖 COMPREHENSIVE SEARCH RESULTS - ALL INFORMATION\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"🔍 Search Number: {data['search_number']}\n")
            f.write(f"🕒 Search Time: {data['timestamp']}\n")
            
            # Calculate total APIs processed
            total_apis = (1 if data['mobile_api']['done'] else 0) + (1 if data['voice_api']['done'] else 0)
            total_apis += (1 if data['personal_aggregate_api']['done'] else 0) + (1 if data['call_trace_api']['done'] else 0)
            total_apis += (1 if data['new_number_api']['done'] else 0) + (1 if data['new_aadhaar_api']['done'] else 0)
            total_apis += len(data['vehicle_apis']) * 2
            total_apis += len(data['aadhaar_apis']) * 3
            total_apis += len(data['family_info_apis'])
            total_apis += len(data['pincode_apis'])
            total_apis += len(data['upi_apis'])
            
            f.write(f"📊 Total APIs Processed: {total_apis}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("📋 EXTRACTED DATA SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"🚗 Vehicle Numbers Found: {len(data['extracted_data']['vehicle_numbers'])}\n")
            for i, vehicle in enumerate(data['extracted_data']['vehicle_numbers'], 1):
                f.write(f"   {i}. {vehicle}\n")
            
            f.write(f"\n🆔 Aadhaar Numbers Found: {len(data['extracted_data']['aadhaar_numbers'])}\n")
            for i, aadhaar in enumerate(data['extracted_data']['aadhaar_numbers'], 1):
                f.write(f"   {i}. {aadhaar}\n")
            
            f.write(f"\n📱 Mobile Numbers Found: {len(data['extracted_data']['mobile_numbers'])}\n")
            for i, mobile in enumerate(data['extracted_data']['mobile_numbers'], 1):
                f.write(f"   {i}. {mobile}\n")
            
            f.write(f"\n👤 Names Found: {len(data['extracted_data']['names'])}\n")
            for i, name in enumerate(data['extracted_data']['names'], 1):
                f.write(f"   {i}. {name}\n")
            
            f.write(f"\n📮 Pincodes Found: {len(data['extracted_data']['pincodes'])}\n")
            for i, pincode in enumerate(data['extracted_data']['pincodes'], 1):
                f.write(f"   {i}. {pincode}\n")
            
            f.write(f"\n💳 UPI IDs Generated: {len(data['upi_apis'])}\n")
            for i, upi_entry in enumerate(data['upi_apis'], 1):
                f.write(f"   {i}. {upi_entry['upi_id']}\n")
            
            f.write(f"\n🏠 Addresses Found: {len(data['extracted_data']['addresses'])}\n")
            for i, addr in enumerate(data['extracted_data']['addresses'], 1):
                f.write(f"   {i}. {addr['field']}: {addr['address'][:100]}...\n")
            
            # 🔥 IMPROVED: GENERATED CREDENTIALS SECTION
            f.write("\n" + "=" * 80 + "\n")
            f.write("🔐 GENERATED CREDENTIALS\n")
            f.write("=" * 80 + "\n\n")
            
            # Email Accounts - IMPROVED FORMAT
            f.write("📧 GENERATED EMAIL ACCOUNTS\n")
            f.write("-" * 50 + "\n")
            if data["generated_credentials"]["emails"]:
                for i, email_entry in enumerate(data["generated_credentials"]["emails"], 1):
                    f.write(f"   Email Account {i}:\n")
                    f.write(f"   ├─ Email: {email_entry['email']}\n")
                    f.write(f"   └─ Password: {email_entry['password']}\n\n")
            else:
                f.write("   ❌ No email accounts generated\n\n")
            
            # Facebook Accounts - IMPROVED FORMAT
            f.write("📘 FACEBOOK ACCOUNTS\n")
            f.write("-" * 50 + "\n")
            if data["generated_credentials"]["facebook_accounts"]:
                for i, fb_entry in enumerate(data["generated_credentials"]["facebook_accounts"], 1):
                    f.write(f"   Facebook Account {i}:\n")
                    f.write(f"   ├─ Facebook ID: {fb_entry['facebook_id']}\n")
                    f.write(f"   └─ Facebook Password: {fb_entry['facebook_password']}\n\n")
            else:
                f.write("   ❌ No Facebook accounts generated\n\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("📡 DETAILED API RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            # Mobile API
            f.write("📱 MOBILE INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["mobile_api"]["done"]:
                mobile_data = data["mobile_api"]["results"]
                write_formatted_data(f, mobile_data, "   ")
            else:
                f.write(f"   ❌ {data['mobile_api']['results']}\n")
            f.write("\n")
            
            # Voice API
            f.write("🎤 VOICE/SET-LE INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["voice_api"]["done"]:
                voice_data = data["voice_api"]["results"]
                write_formatted_data(f, voice_data, "   ")
            else:
                f.write(f"   ❌ {data['voice_api']['results']}\n")
            f.write("\n")
            
            # Personal Aggregate API
            f.write("👤 PERSONAL AGGREGATE INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["personal_aggregate_api"]["done"]:
                personal_data = data["personal_aggregate_api"]["results"]
                write_formatted_data(f, personal_data, "   ")
            else:
                f.write(f"   ❌ {data['personal_aggregate_api']['results']}\n")
            f.write("\n")
            
            # Call Trace API
            f.write("📞 CALL TRACE INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["call_trace_api"]["done"]:
                call_trace_data = data["call_trace_api"]["results"]
                write_formatted_data(f, call_trace_data, "   ")
            else:
                f.write(f"   ❌ {data['call_trace_api']['results']}\n")
            f.write("\n")
            
            # NEW Number API - IMPROVED FORMAT
            f.write("🔥 NEW NUMBER INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["new_number_api"]["done"]:
                new_number_data = data["new_number_api"]["results"]
                if new_number_data:
                    # Check if we have the expected JSON structure
                    if isinstance(new_number_data, dict):
                        if new_number_data.get('success') and new_number_data.get('data'):
                            api_data = new_number_data['data']
                            if api_data.get('success') and api_data.get('result'):
                                f.write("   ✅ SUCCESS: Data found!\n")
                                for i, item in enumerate(api_data['result'], 1):
                                    f.write(f"\n   ┌─ Record {i}:\n")
                                    f.write(f"   ├─ Name: {item.get('name', 'N/A')}\n")
                                    f.write(f"   ├─ Father Name: {item.get('father_name', 'N/A')}\n")
                                    f.write(f"   ├─ Address: {item.get('address', 'N/A')}\n")
                                    f.write(f"   ├─ Circle: {item.get('circle', 'N/A')}\n")
                                    f.write(f"   ├─ Alt Mobile: {item.get('alt_mobile', 'N/A')}\n")
                                    f.write(f"   └─ ID Number: {item.get('id_number', 'N/A')}\n")
                            else:
                                f.write("   ℹ️ No result data in response\n")
                        else:
                            f.write("   ℹ️ Unexpected JSON structure\n")
                            write_formatted_data(f, new_number_data, "   ")
                    else:
                        f.write("   ℹ️ Response is not in expected format\n")
                        write_formatted_data(f, new_number_data, "   ")
                else:
                    f.write("   ✅ API Called Successfully (No data returned)\n")
            else:
                f.write(f"   ❌ {data['new_number_api']['results']}\n")
            f.write("\n")
            
            # NEW Aadhaar API - IMPROVED FORMAT
            f.write("🔥 NEW AADHAAR INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["new_aadhaar_api"]["done"]:
                new_aadhaar_data = data["new_aadhaar_api"]["results"]
                if new_aadhaar_data:
                    f.write("   📊 Response Data:\n")
                    write_formatted_data(f, new_aadhaar_data, "   ")
                else:
                    f.write("   ✅ API Called Successfully (No data returned)\n")
            else:
                f.write(f"   ❌ {data['new_aadhaar_api']['results']}\n")
            f.write("\n")
            
            # Vehicle APIs
            f.write("🚗 VEHICLE INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["vehicle_apis"]:
                for vehicle_entry in data["vehicle_apis"]:
                    f.write(f"   🚙 Vehicle: {vehicle_entry['vehicle_number']}\n")
                    
                    f.write(f"   ├─ API 1 Results:\n")
                    if vehicle_entry["api1_result"]["done"]:
                        vehicle_data = vehicle_entry["api1_result"]["results"]
                        write_formatted_data(f, vehicle_data, "   │  ")
                    else:
                        f.write(f"   │  ❌ {vehicle_entry['api1_result']['results']}\n")
                    
                    f.write(f"   └─ API 2 Results:\n")
                    if vehicle_entry["api2_result"]["done"]:
                        vehicle_data = vehicle_entry["api2_result"]["results"]
                        write_formatted_data(f, vehicle_data, "      ")
                    else:
                        f.write(f"      ❌ {vehicle_entry['api2_result']['results']}\n")
                    f.write("\n")
            else:
                f.write("   ❌ No vehicle data found\n\n")
            
            # Aadhaar APIs
            f.write("🆔 AADHAAR INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["aadhaar_apis"]:
                for aadhaar_entry in data["aadhaar_apis"]:
                    f.write(f"   📄 Aadhaar: {aadhaar_entry['aadhaar_number']}\n")
                    
                    f.write(f"   ├─ Basic Aadhaar Results:\n")
                    if aadhaar_entry["aadhaar_result"]["done"]:
                        aadhaar_data = aadhaar_entry["aadhaar_result"]["results"]
                        write_formatted_data(f, aadhaar_data, "   │  ")
                    else:
                        f.write(f"   │  ❌ {aadhaar_entry['aadhaar_result']['results']}\n")
                    
                    f.write(f"   ├─ Family Results:\n")
                    if aadhaar_entry["family_result"]["done"]:
                        family_data = aadhaar_entry["family_result"]["results"]
                        write_formatted_data(f, family_data, "   │  ")
                    else:
                        f.write(f"   │  ❌ {aadhaar_entry['family_result']['results']}\n")
                    
                    f.write(f"   └─ New Aadhaar Results:\n")
                    if aadhaar_entry["new_aadhaar_result"]["done"]:
                        new_aadhaar_data = aadhaar_entry["new_aadhaar_result"]["results"]
                        write_formatted_data(f, new_aadhaar_data, "      ")
                    else:
                        f.write(f"      ❌ {aadhaar_entry['new_aadhaar_result']['results']}\n")
                    f.write("\n")
            else:
                f.write("   ❌ No Aadhaar data found\n\n")
            
            # Family Info APIs
            f.write("👨‍👩‍👧‍👦 FAMILY INFORMATION (ALTERNATIVE)\n")
            f.write("-" * 50 + "\n")
            if data["family_info_apis"]:
                for family_info_entry in data["family_info_apis"]:
                    f.write(f"   📄 Aadhaar: {family_info_entry['aadhaar_number']}\n")
                    
                    if family_info_entry["family_info_result"]["done"]:
                        family_info_data = family_info_entry["family_info_result"]["results"]
                        write_formatted_data(f, family_info_data, "   ")
                    else:
                        f.write(f"   ❌ {family_info_entry['family_info_result']['results']}\n")
                    f.write("\n")
            else:
                f.write("   ❌ No alternative family data found\n\n")
            
            # Pincode APIs
            f.write("📮 LOCATION INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["pincode_apis"]:
                for pincode_entry in data["pincode_apis"]:
                    f.write(f"   📍 Pincode: {pincode_entry['pincode']}\n")
                    
                    if pincode_entry["result"]["done"]:
                        pincode_data = pincode_entry["result"]["results"]
                        write_formatted_data(f, pincode_data, "   ")
                    else:
                        f.write(f"   ❌ {pincode_entry['result']['results']}\n")
                    f.write("\n")
            else:
                f.write("   ❌ No location data found\n\n")
            
            # UPI APIs
            f.write("💳 UPI INFORMATION\n")
            f.write("-" * 50 + "\n")
            if data["upi_apis"]:
                for upi_entry in data["upi_apis"]:
                    f.write(f"   💰 UPI ID: {upi_entry['upi_id']}\n")
                    
                    if upi_entry["result"]["done"]:
                        upi_data = upi_entry["result"]["results"]
                        write_formatted_data(f, upi_data, "   ")
                    else:
                        f.write(f"   ❌ {upi_entry['result']['results']}\n")
                    f.write("\n")
            else:
                f.write("   ❌ No UPI data found\n\n")
            
            # Google Maps Links
            f.write("🗺️ GOOGLE MAPS LINKS\n")
            f.write("-" * 50 + "\n")
            if data["google_maps_links"]:
                for i, maps_info in enumerate(data["google_maps_links"], 1):
                    f.write(f"   📍 Location {i}:\n")
                    f.write(f"   ├─ Source: {maps_info['source']}\n")
                    f.write(f"   ├─ Address: {maps_info['address'][:200]}...\n")
                    f.write(f"   └─ Maps Link: {maps_info['maps_link']}\n\n")
            else:
                f.write("   ❌ No address found for maps\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("🤖 Bot By: @gokuuuu_1\n")
            f.write("=" * 80 + "\n")
        
        return filename
        
    except Exception as e:
        logger.error(f"Error generating text file: {str(e)}")
        return None

def write_formatted_data(file_obj, data, indent=""):
    """Write formatted data to file"""
    if isinstance(data, dict):
        for key, value in data.items():
            if value is None or value == "" or value == "N/A":
                continue
                
            formatted_key = key.replace('_', ' ').title()
            
            if isinstance(value, dict):
                file_obj.write(f"{indent}{formatted_key}:\n")
                write_formatted_data(file_obj, value, indent + "    ")
            elif isinstance(value, list):
                file_obj.write(f"{indent}{formatted_key}:\n")
                for item in value:
                    if isinstance(item, dict):
                        write_formatted_data(file_obj, item, indent + "    ")
                    else:
                        file_obj.write(f"{indent}    - {item}\n")
            else:
                file_obj.write(f"{indent}{formatted_key}: {value}\n")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                write_formatted_data(file_obj, item, indent)
            else:
                file_obj.write(f"{indent}- {item}\n")

# FORMATTING FUNCTIONS
def clean_api_response(data):
    """Clean API response from unwanted fields"""
    if isinstance(data, dict):
        unwanted_fields = ['credit', 'developer', 'modded', 'created', 
                          'author', 'owner', 'credits', 'modified', 'by']
        
        cleaned_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            should_skip = any(unwanted_word in key_lower for unwanted_word in unwanted_fields)
            
            if not should_skip:
                if isinstance(value, dict):
                    cleaned_value = clean_api_response(value)
                    if cleaned_value:
                        cleaned_data[key] = cleaned_value
                elif isinstance(value, list):
                    cleaned_list = [clean_api_response(item) if isinstance(item, dict) else clean_text_value(item) for item in value]
                    cleaned_list = [item for item in cleaned_list if item not in [None, "", "N/A"]]
                    if cleaned_list:
                        cleaned_data[key] = cleaned_list
                else:
                    cleaned_value = clean_text_value(value)
                    if cleaned_value not in [None, "", "N/A"]:
                        cleaned_data[key] = cleaned_value
        return cleaned_data
    elif isinstance(data, list):
        cleaned_list = [clean_api_response(item) if isinstance(item, dict) else clean_text_value(item) for item in data]
        return [item for item in cleaned_list if item not in [None, "", "N/A"]]
    else:
        return clean_text_value(data)

def clean_text_value(value):
    """Clean text values"""
    if isinstance(value, str):
        unwanted_texts = ['@oxmzoo', 'oxmzoo', 'Credit:', 'Developer:', 'credit:', 'developer:']
        
        for text in unwanted_texts:
            value = value.replace(text, '')
        
        value = ' '.join(value.split())
        
        if not value or value == '':
            return "N/A"
            
        return value
    return value

# 🔥 IMPROVED SUMMARY MESSAGE
def format_summary_message(result):
    """Format summary message for Telegram with IMPROVED features"""
    if not result["done"]:
        return f"❌ *Error Occurred!*\n\n`{result['results']}`"
    
    data = result["results"]
    
    # Calculate total APIs processed
    total_apis = (1 if data['mobile_api']['done'] else 0) + (1 if data['voice_api']['done'] else 0)
    total_apis += (1 if data['personal_aggregate_api']['done'] else 0) + (1 if data['call_trace_api']['done'] else 0)
    total_apis += (1 if data['new_number_api']['done'] else 0) + (1 if data['new_aadhaar_api']['done'] else 0)
    total_apis += len(data['vehicle_apis']) * 2
    total_apis += len(data['aadhaar_apis']) * 3
    total_apis += len(data['family_info_apis'])
    total_apis += len(data['pincode_apis'])
    total_apis += len(data['upi_apis'])
    
    # Get primary name for display
    primary_name = "Not Found"
    if data['extracted_data']['names']:
        primary_name = data['extracted_data']['names'][0]
    
    summary_msg = f"""
✅ *COMPREHENSIVE SEARCH COMPLETED!*

🔍 *Search Number:* `{data['search_number']}`
👤 *Primary Name:* `{primary_name}`
🕒 *Search Time:* `{data['timestamp'][11:19]}`
📊 *APIs Processed:* `{total_apis}`

📈 *Data Extracted:*
• 🚗 Vehicles: `{len(data['extracted_data']['vehicle_numbers'])}`
• 🆔 Aadhaar: `{len(data['extracted_data']['aadhaar_numbers'])}`
• 📱 Mobiles: `{len(data['extracted_data']['mobile_numbers'])}`
• 👤 Names: `{len(data['extracted_data']['names'])}`
• 💳 UPI IDs: `{len(data['upi_apis'])}`
• 📮 Pincodes: `{len(data['extracted_data']['pincodes'])}`
• 🏠 Addresses: `{len(data['extracted_data']['addresses'])}`
• 🗺️ Maps Links: `{len(data.get('google_maps_links', []))}`

🔐 *Generated Credentials:*
• 📧 Emails: `{len(data['generated_credentials']['emails'])}`
• 📘 Facebook: `{len(data['generated_credentials']['facebook_accounts'])}`

🔥 *NEW APIs Status:*
• New Number API: `{'✅ SUCCESS' if data['new_number_api']['done'] else '❌ FAILED'}`
• New Aadhaar API: `{'✅ SUCCESS' if data['new_aadhaar_api']['done'] else '❌ FAILED'}`

📁 *Complete report has been generated and attached below.*
🤖 *Bot By:* @gokuuuu_1
    """
    
    return summary_msg

# MESSAGE HANDLER - IMPROVED
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in groups - only respond to numbers"""
    if not BOT_ACTIVE:
        return
    
    chat = update.effective_chat
    user_message = update.message.text.strip()
    
    # Only process in groups
    if chat.type not in ["group", "supergroup"]:
        return
    
    # Store group info
    group_name = chat.title or "Unknown Group"
    add_group(str(chat.id), group_name)
    
    # Only respond to numeric messages (10 or 12 digits)
    if user_message.isdigit():
        if len(user_message) == 10:
            # Mobile number detected - COMPREHENSIVE SEARCH
            search_type = 'full_search'
            search_value = user_message
        elif len(user_message) == 12:
            # Aadhaar number detected - SINGLE API SEARCH
            search_type = 'aadhaar'
            search_value = user_message
        else:
            return  # Ignore other digit lengths
    else:
        return  # Ignore non-numeric messages
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 *Starting Comprehensive Search...*\n\n"
        "📡 *APIs Being Called:*\n"
        "• 📱 Mobile Information\n"
        "• 🎤 Voice/Set-le Information\n"
        "• 👤 Personal Aggregate Information\n"
        "• 📞 Call Trace Information\n"
        "• 🔥 New Number Information\n"
        "• 🔥 New Aadhaar Information\n"
        "• 🚗 Vehicle Information (Multiple APIs)\n"
        "• 🆔 Aadhaar Information\n"
        "• 👨‍👩‍👧‍👦 Family Information (Multiple APIs)\n"
        "• 💳 UPI Information\n"
        "• 📮 Pincode Information\n"
        "• 🗺️ Google Maps Links\n\n"
        "🔐 *Generating Credentials:*\n"
        "• 📧 Email Accounts\n"
        "• 📘 Facebook Accounts\n\n"
        "⏳ This may take 20-30 seconds...",
        parse_mode='Markdown'
    )
    
    try:
        # Call comprehensive search
        comprehensive_result = call_all_apis_comprehensive(search_value)
        
        if comprehensive_result["done"]:
            # Generate text file
            text_filename = generate_text_file(comprehensive_result)
            
            # Prepare summary message
            summary_msg = format_summary_message(comprehensive_result)
            
            if text_filename:
                # Send summary message with file
                with open(text_filename, 'rb') as text_file:
                    await context.bot.send_document(
                        chat_id=chat.id,
                        document=text_file,
                        caption=summary_msg,
                        parse_mode='Markdown'
                    )
                
                # Clean up file
                try:
                    os.remove(text_filename)
                except:
                    pass
                
                # Delete processing message
                try:
                    await processing_msg.delete()
                except:
                    pass
            else:
                await context.bot.edit_message_text(
                    chat_id=processing_msg.chat_id,
                    message_id=processing_msg.message_id,
                    text="❌ *Error generating report file*",
                    parse_mode='Markdown'
                )
        else:
            await context.bot.edit_message_text(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id,
                text=f"❌ *Search Failed:* `{comprehensive_result['results']}`",
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Error in group message handler: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=processing_msg.chat_id,
            message_id=processing_msg.message_id,
            text=f"❌ *Unexpected Error:* `{str(e)}`",
            parse_mode='Markdown'
        )

# ... [REST OF THE CODE REMAINS THE SAME - button handlers, admin functions, etc.] ...
# The rest of the code (button handlers, admin functions, command handlers) remains exactly the same
# Only the API functions, email generation, and file generation have been improved

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Only allow admin buttons in private chat
    if data.startswith('admin_') and user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    if data == 'add_to_group':
        await handle_add_to_group(query, context)
    
    elif data == 'show_my_groups':
        await handle_show_my_groups(query, context)
    
    elif data.startswith('add_to_specific_group_'):
        group_id = data.replace('add_to_specific_group_', '')
        await handle_add_to_specific_group(query, context, group_id)
    
    elif data == 'back_to_add_group':
        await handle_add_to_group(query, context)
    
    elif data == 'admin_panel':
        await handle_admin_panel(query, context)
    
    elif data == 'admin_view_groups':
        await handle_admin_view_groups(query, context)
    
    elif data == 'admin_stats':
        await handle_admin_stats(query, context)
    
    elif data == 'admin_broadcast':
        await handle_admin_broadcast(query, context)
    
    elif data == 'admin_bot_settings':
        await handle_admin_bot_settings(query, context)
    
    else:
        await query.answer("❌ Unknown button!", show_alert=True)

async def handle_add_to_group(query, context):
    """Handle add to group button"""
    user_id = query.from_user.id
    
    add_text = """
👥 *ADD BOT TO YOUR GROUP*

🤖 *Choose an option to add this bot:*

🔹 *Option 1: Select from your groups*
Choose from the groups you admin

🔹 *Option 2: Create new group*
Create a new group and add bot as admin

📱 *Bot Features in Groups:*
• Respond to 10-digit mobile numbers
• Respond to 12-digit Aadhaar numbers
• Multi-API information lookup
• Complete file reports
• Vehicle information
• Family details
• UPI information
• Location details
• Google Maps links
• 🔥 NEW: Email & Facebook credentials generation
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 SELECT FROM MY GROUPS", callback_data="show_my_groups")],
        [InlineKeyboardButton("🆕 CREATE NEW GROUP", url="https://t.me/+")],
        [InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        add_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_show_my_groups(query, context):
    """Show user's groups for adding bot"""
    user_id = query.from_user.id
    
    groups_text = """
📋 *YOUR TELEGRAM GROUPS*

🤖 *To add bot to your group:*

1. *Go to your group settings*
2. *Click on "Administrators"*
3. *Click "Add Admin"*
4. *Search for @your_bot_username*
5. *Grant necessary permissions*
6. *Click "Done"*

✅ *Required Permissions:*
• Post Messages
• Edit Messages
• Delete Messages
• Pin Messages
• Invite Users via Link

📱 *After adding, users can:*
• Send 10-digit mobile numbers
• Send 12-digit Aadhaar numbers
• Get complete file reports with all information
• 🔥 NEW: Get generated email & Facebook credentials
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 REFRESH MY GROUPS", callback_data="show_my_groups")],
        [InlineKeyboardButton("📢 SHARE BOT LINK", 
                             url="https://t.me/share/url?url=Check%20out%20this%20awesome%20bot%20for%20mobile%20and%20Aadhaar%20information%20lookup!%20🤖")],
        [InlineKeyboardButton("🔙 BACK TO ADD MENU", callback_data="add_to_group")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        groups_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_add_to_specific_group(query, context, group_id):
    """Handle adding to specific group"""
    await query.answer("📋 Please add the bot manually to your group", show_alert=True)

# ADMIN HANDLER FUNCTIONS
async def handle_admin_panel(query, context):
    """Handle admin panel button"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    total_groups = get_group_count()
    bot_status = "✅ ACTIVE" if BOT_ACTIVE else "❌ INACTIVE"
    
    admin_text = f"""
🛠️ *BOT ADMIN PANEL* 🛠️

📊 *Bot Statistics:*
• 👥 Total Groups: `{total_groups}`
• 🤖 Bot Status: `{bot_status}`

🔥 *NEW Features Added:*
• 🔥 New Number API
• 🔥 New Aadhaar API  
• 📧 Email Generation
• 📘 Facebook Credentials

🔧 *Admin Actions:*
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 VIEW ALL GROUPS", callback_data="admin_view_groups"),
         InlineKeyboardButton("📊 STATISTICS", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 BROADCAST TO GROUPS", callback_data="admin_broadcast"),
         InlineKeyboardButton("➕ ADD TO GROUP", callback_data="add_to_group")],
        [InlineKeyboardButton("⚙️ BOT SETTINGS", callback_data="admin_bot_settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        admin_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_admin_view_groups(query, context):
    """Handle admin view groups button"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    groups = get_all_groups()
    
    if not groups:
        await query.edit_message_text("📭 *No groups found!*", parse_mode='Markdown')
        return
    
    group_text = "👥 *ALL GROUPS:*\n\n"
    
    for i, group in enumerate(groups[:20], 1):
        group_id, group_name, group_link, added_date = group
        group_text += f"{i}. **{group_name}**\n"
        group_text += f"   ├ ID: `{group_id}`\n"
        if group_link:
            group_text += f"   ├ Link: {group_link}\n"
        group_text += f"   └ Added: `{added_date[:10]}`\n\n"
    
    if len(groups) > 20:
        group_text += f"\n📋 *Showing 20 out of {len(groups)} groups*"
    
    keyboard = [
        [InlineKeyboardButton("🔄 REFRESH", callback_data="admin_view_groups")],
        [InlineKeyboardButton("🔙 ADMIN PANEL", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        group_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_admin_stats(query, context):
    """Handle admin stats button"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    total_groups = get_group_count()
    groups = get_all_groups()
    
    today = datetime.now().date()
    today_groups = 0
    for group in groups:
        added_date = datetime.strptime(group[3][:10], '%Y-%m-%d').date()
        if added_date == today:
            today_groups += 1
    
    stats_text = f"""
📊 *DETAILED STATISTICS*

👥 *GROUP STATS:*
• 📈 Total Groups: `{total_groups}`
• 📥 New Groups Today: `{today_groups}`

⚙️ *BOT STATUS:*
• 🤖 Bot: `{'✅ ACTIVE' if BOT_ACTIVE else '❌ INACTIVE'}`
• 🕒 Last Updated: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

🔥 *NEW FEATURES:*
• 📧 Email Generation: `ACTIVE`
• 📘 Facebook Credentials: `ACTIVE`
• 🔥 New APIs: `ACTIVE`
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 REFRESH", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 ADMIN PANEL", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_admin_broadcast(query, context):
    """Handle admin broadcast button"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    broadcast_text = """
📢 *BROADCAST TO ALL GROUPS*

💡 *How to send broadcast:*
Use command: `/broadcast your message here`

📝 *Example:*
`/broadcast Hello everyone! New update available.`

🔥 *NEW: Email & Facebook credentials generation added!*

⚠️ *This will send message to all groups!*
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 ADMIN PANEL", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        broadcast_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_admin_bot_settings(query, context):
    """Handle admin bot settings button"""
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("❌ Access Denied!", show_alert=True)
        return
    
    bot_status = "✅ ACTIVE" if BOT_ACTIVE else "❌ INACTIVE"
    
    settings_text = f"""
⚙️ *BOT SETTINGS*

🤖 *Current Status:*
• Bot: `{bot_status}`

🔥 *NEW Features Status:*
• Email Generation: `ACTIVE`
• Facebook Credentials: `ACTIVE`
• New Number API: `ACTIVE`
• New Aadhaar API: `ACTIVE`

🔧 *Available Commands:*

• *Turn bot ON:*
  `/bot on`

• *Turn bot OFF:*
  `/bot off`
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 ADMIN PANEL", callback_data="admin_panel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        settings_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# COMMAND HANDLERS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when command /start is issued."""
    if not BOT_ACTIVE:
        await update.message.reply_text(
            "🔧 *Bot is currently under maintenance!*\n\n"
            "Please try again later.\n"
            "Thank you for your patience! 🤖",
            parse_mode='Markdown'
        )
        return
    
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == "private":
        add_user(user.id, user.username, user.first_name, user.last_name)
        
        welcome_text = f"""
✨ *WELCOME {user.first_name}!* ✨

🤖 **COMPREHENSIVE DATA LOOKUP BOT**
*All-in-One Information Gathering Tool*

🚀 *HOW TO USE:*
1. Add this bot to your group
2. Users can send numbers directly:
   • 📱 10-digit Mobile Numbers (COMPLETE SEARCH)
   • 🆔 12-digit Aadhaar Numbers (AADHAAR + FAMILY INFO)

⚡ *NEW FEATURES:*
• Mobile & Voice Information
• 👤 Personal Aggregate Information
• 📞 Call Trace Information
• 🔥 New Number Information API
• 🔥 New Aadhaar Information API
• 🚗 Vehicle Information (2 APIs)
• 🆔 Aadhaar Details
• 👨‍👩‍👧‍👦 Family Information (Multiple APIs)
• 💳 UPI Information
• Location Details
• Google Maps Links
• 📧 Email Account Generation
• 📘 Facebook Credentials Generation
• 📁 Complete File Reports
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ ADD TO GROUP", callback_data="add_to_group")]
        ]
        
        if user.id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("🛠️ ADMIN PANEL", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        welcome_text = """
🤖 **COMPREHENSIVE DATA LOOKUP BOT**

📱 *Simply send:*
• 10-digit Mobile Number (Complete Search)
• 12-digit Aadhaar Number (Aadhaar + Family Info)

🔥 *NEW: Get generated email & Facebook credentials!*

⚡ *Get complete file report with ALL details including UPI information!*
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    # Only allow in private chat
    if chat.type != "private":
        return
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Access Denied!*", parse_mode='Markdown')
        return
    
    await handle_admin_panel(update, context)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast command - send to all groups"""
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    # Only allow in private chat
    if chat.type != "private":
        return
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Access Denied!*", parse_mode='Markdown')
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ *Please provide a message to broadcast!*\n\n"
            "Usage: `/broadcast your message`",
            parse_mode='Markdown'
        )
        return
    
    message_text = ' '.join(context.args)
    groups = get_all_groups()
    total_groups = len(groups)
    successful = 0
    failed = 0
    
    processing_msg = await update.message.reply_text(
        f"📢 *Starting Group Broadcast...*\n\n"
        f"• 📋 Total Groups: `{total_groups}`\n"
        f"• ⏳ Sending messages...",
        parse_mode='Markdown'
    )
    
    for group in groups:
        group_id = group[0]
        
        try:
            await context.bot.send_message(
                chat_id=group_id,
                text=message_text,
                parse_mode='Markdown'
            )
            successful += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to group {group_id}: {e}")
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    await processing_msg.edit_text(
        f"✅ *Broadcast Completed!*\n\n"
        f"• 📋 Total Groups: `{total_groups}`\n"
        f"• ✅ Successful: `{successful}`\n"
        f"• ❌ Failed: `{failed}`",
        parse_mode='Markdown'
    )

async def bot_control_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Control bot on/off"""
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    # Only allow in private chat
    if chat.type != "private":
        return
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ *Access Denied!*", parse_mode='Markdown')
        return
    
    if not context.args:
        status = "✅ ACTIVE" if BOT_ACTIVE else "❌ INACTIVE"
        await update.message.reply_text(
            f"🤖 *Bot Status:* `{status}`\n\n"
            "Usage: `/bot on` or `/bot off`",
            parse_mode='Markdown'
        )
        return
    
    action = context.args[0].lower()
    
    if action in ['on', 'start', 'active']:
        globals()['BOT_ACTIVE'] = True
        await update.message.reply_text("✅ *Bot turned ON!*", parse_mode='Markdown')
    elif action in ['off', 'stop', 'inactive']:
        globals()['BOT_ACTIVE'] = False
        await update.message.reply_text("❌ *Bot turned OFF!*", parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "❌ *Invalid action!*\n\n"
            "Usage: `/bot on` or `/bot off`",
            parse_mode='Markdown'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot."""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Admin command handlers
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("bot", bot_control_command))
    
    # Callback and message handlers
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Group message handler - ONLY responds to numbers
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, 
        handle_group_message
    ))
    
    # Private message handler - for admin commands only
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        lambda update, context: None
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    print("🤖 COMPREHENSIVE DATA LOOKUP BOT STARTING...")
    print("🚀 Bot is now running. Press Ctrl+C to stop.")
    print("🔧 Bot By: @Rolexjjjjjj")
    print(f"👑 Admin ID: {ADMIN_IDS[0]}")
    print("🎯 BOT WILL ONLY WORK IN GROUPS")
    print("📱 WILL ONLY RESPOND TO 10/12 DIGIT NUMBERS")
    print("🔍 COMPREHENSIVE API INTEGRATION: ACTIVE")
    print("🎤 VOICE API: FIXED & ACTIVE")
    print("🚗 VEHICLE API INTEGRATION: ACTIVE") 
    print("🆔 AADHAAR API INTEGRATION: ACTIVE")
    print("👨‍👩‍👧‍👦 FAMILY API INTEGRATION: ACTIVE")
    print("💳 UPI API INTEGRATION: ACTIVE")
    print("📮 PINCODE API: FIXED & ACTIVE")
    print("🗺️ GOOGLE MAPS INTEGRATION: ACTIVE")
    print("📁 FILE GENERATION: IMPROVED & ACTIVE")
    print("🔥 NEW APIs COMPLETELY FIXED:")
    print("   • 🔥 New Number API - JavaScript redirect handled")
    print("   • 🔥 New Aadhaar API - Proper JSON parsing")
    print("🔐 EMAIL & FACEBOOK GENERATION IMPROVED:")
    print("   • 📧 Email Generation - Uses ACTUAL name from number info")
    print("   • 📘 Facebook Credentials - Uses ACTUAL name + number")
    print("   • 🔑 Password Generation - Strong & realistic passwords")
    print("📊 SUMMARY MESSAGES + COMPLETE FILE REPORTS")
    
    application.run_polling()

if __name__ == '__main__':
    main()
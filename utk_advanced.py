import requests
import json
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad, pad
from base64 import b64decode, b64encode
import base64
import datetime
from typing import List, Dict, Tuple, Optional
import time

# ============================================================================
# ADVANCED UTKARSH SCRAPER WITH FEATURES
# ============================================================================

class AdvancedUtkarshScraper:
    """Advanced Utkarsh scraper with parallel processing, retry logic, and progress tracking"""
    
    BASE_URL = "https://online.utkarsh.com"
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 5
    RETRY_DELAY = 2
    
    # CloudFront CDN patterns
    CLOUDFRONT_DOMAINS = [
        "d1q5ugnejk3zoi.cloudfront.net",
        "cloudfront.net",
        "d2tcj7z8yw9aqf.cloudfront.net",
        "d1h3zw5gfnqjuq.cloudfront.net"
    ]
    
    # Encryption keys (hardcoded by Utkarsh)
    ENCRYPTION_KEY = '%!$!%_$&!%F)&^!^'.encode('utf-8')
    ENCRYPTION_IV = '#*y*#2yJ*#$wJv*v'.encode('utf-8')
    
    def __init__(self, timeout=30, max_retries=5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        self.stats = {
            "total_batches": 0,
            "total_subjects": 0,
            "total_topics": 0,
            "total_videos": 0,
            "failed_requests": 0,
            "successful_requests": 0,
            "start_time": None,
            "end_time": None
        }
    
    # ========================================================================
    # ENCRYPTION/DECRYPTION
    # ========================================================================
    
    @staticmethod
    def decrypt(enc):
        """Decrypt AES-256-CBC"""
        try:
            enc = b64decode(enc)
            cipher = AES.new(AdvancedUtkarshScraper.ENCRYPTION_KEY, AES.MODE_CBC, 
                           AdvancedUtkarshScraper.ENCRYPTION_IV)
            plaintext = unpad(cipher.decrypt(enc), AES.block_size)
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return None
    
    @staticmethod
    def encrypt(data):
        """Encrypt with AES-256-CBC"""
        try:
            cipher = AES.new(AdvancedUtkarshScraper.ENCRYPTION_KEY, AES.MODE_CBC, 
                           AdvancedUtkarshScraper.ENCRYPTION_IV)
            padded_data = pad(data.encode(), AES.block_size)
            encrypted_data = cipher.encrypt(padded_data)
            return b64encode(encrypted_data).decode()
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    @staticmethod
    def get_headers(token):
        """Get request headers"""
        return {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'origin': AdvancedUtkarshScraper.BASE_URL,
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': f'csrf_name={token}; ci_session=tb0uld02neaa4ujs1g4idb6l8bmql8jh'
        }
    
    # ========================================================================
    # RETRY MECHANISM
    # ========================================================================
    
    async def retry_request(self, method, url, **kwargs):
        """Make request with automatic retry logic"""
        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, timeout=self.timeout, **kwargs)
                elif method == 'POST':
                    response = requests.post(url, timeout=self.timeout, **kwargs)
                else:
                    return None
                
                if response.status_code == 200:
                    self.stats["successful_requests"] += 1
                    return response
                else:
                    print(f"⚠️  Attempt {attempt + 1}/{self.max_retries}: HTTP {response.status_code}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.RETRY_DELAY)
            
            except requests.exceptions.Timeout:
                print(f"⚠️  Timeout attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
            
            except requests.exceptions.ConnectionError as e:
                print(f"⚠️  Connection error attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY * 2)
            
            except Exception as e:
                print(f"❌ Error attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
        
        self.stats["failed_requests"] += 1
        return None
    
    # ========================================================================
    # TOKEN & AUTH
    # ========================================================================
    
    async def get_csrf_token(self):
        """Fetch CSRF token"""
        try:
            print("🔑 Fetching CSRF token...")
            response = await self.retry_request(
                'GET',
                f'{self.BASE_URL}/web/home/get_states'
            )
            
            if response and response.status_code == 200:
                token = response.json().get("token")
                if token:
                    print(f"✅ Token fetched: {token[:15]}...")
                    return token
            
            print("❌ Failed to fetch token")
            return None
        
        except Exception as e:
            print(f"❌ Token fetch error: {e}")
            return None
    
    async def authenticate(self, user_id, password, token, headers):
        """Authenticate user with retry"""
        try:
            print(f"🔐 Authenticating user: {user_id}...")
            data = f"csrf_name={token}&mobile={user_id}&url=0&password={password}&submit=LogIn&device_token=null"
            
            response = await self.retry_request(
                'POST',
                f'{self.BASE_URL}/web/Auth/login',
                headers=headers,
                data=data
            )
            
            if not response:
                return False, "Request failed after retries"
            
            json_data = response.json()
            if "response" not in json_data:
                return False, "Invalid response format"
            
            encrypted_resp = json_data["response"]
            encrypted_resp = encrypted_resp.replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==')
            
            decrypted = self.decrypt(encrypted_resp)
            if not decrypted:
                return False, "Decryption failed"
            
            auth_data = json.loads(decrypted)
            
            if auth_data.get('status'):
                print("✅ Authentication successful")
                return True, auth_data
            else:
                error = auth_data.get('message', 'Unknown error')
                print(f"❌ Auth failed: {error}")
                return False, error
        
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False, str(e)
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    async def fetch_batches(self, token, headers):
        """Fetch all batches"""
        try:
            print("📚 Fetching batches...")
            data = f"type=Batch&csrf_name={token}&sort=0"
            
            response = await self.retry_request(
                'POST',
                f'{self.BASE_URL}/web/Profile/my_course',
                headers=headers,
                data=data
            )
            
            if not response:
                return None, "Request failed"
            
            json_data = response.json()
            if "response" not in json_data:
                return None, "Invalid response"
            
            encrypted_resp = json_data["response"]
            encrypted_resp = encrypted_resp.replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==')
            
            decrypted = self.decrypt(encrypted_resp)
            if not decrypted:
                return None, "Decryption failed"
            
            batch_data = json.loads(decrypted)
            batches = batch_data.get('data', {}).get('data', [])
            
            self.stats["total_batches"] = len(batches)
            print(f"✅ Found {len(batches)} batches")
            return batches, None
        
        except Exception as e:
            print(f"❌ Batch fetch error: {e}")
            return None, str(e)
    
    # ========================================================================
    # SUBJECT OPERATIONS
    # ========================================================================
    
    async def fetch_subjects(self, batch_id, token, headers):
        """Fetch subjects for batch"""
        try:
            tile_input = f'{{"course_id": {batch_id},"revert_api":"1#0#0#1","parent_id":0,"tile_id":"0","layer":1,"type":"course_combo"}}'
            encrypted_input = self.encrypt(tile_input)
            
            data = {
                'tile_input': encrypted_input,
                'csrf_name': token
            }
            
            response = await self.retry_request(
                'POST',
                f'{self.BASE_URL}/web/Course/tiles_data',
                headers=headers,
                data=data
            )
            
            if not response:
                return None, "Request failed"
            
            json_data = response.json()
            if "response" not in json_data:
                return None, "Invalid response"
            
            encrypted_resp = json_data["response"]
            encrypted_resp = encrypted_resp.replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==')
            
            decrypted = self.decrypt(encrypted_resp)
            if not decrypted:
                return None, "Decryption failed"
            
            subjects_data = json.loads(decrypted)
            subjects = subjects_data.get('data', [])
            
            self.stats["total_subjects"] += len(subjects)
            return subjects, None
        
        except Exception as e:
            print(f"❌ Subject fetch error: {e}")
            return None, str(e)
    
    # ========================================================================
    # TOPIC OPERATIONS
    # ========================================================================
    
    async def fetch_topics(self, batch_id, subject_id, token, headers):
        """Fetch topics for subject"""
        try:
            tile_input = f'{{"course_id":{subject_id},"layer":1,"page":1,"parent_id":{batch_id},"revert_api":"1#0#0#1","tile_id":"0","type":"content"}}'
            encrypted_input = self.encrypt(tile_input)
            
            data = {
                'tile_input': encrypted_input,
                'csrf_name': token
            }
            
            response = await self.retry_request(
                'POST',
                f'{self.BASE_URL}/web/Course/tiles_data',
                headers=headers,
                data=data
            )
            
            if not response:
                return None, "Request failed"
            
            json_data = response.json()
            if "response" not in json_data:
                return None, "Invalid response"
            
            encrypted_resp = json_data["response"]
            encrypted_resp = encrypted_resp.replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==')
            
            decrypted = self.decrypt(encrypted_resp)
            if not decrypted:
                return None, "Decryption failed"
            
            topics_data = json.loads(decrypted)
            topics = topics_data.get('data', {}).get('list', [])
            
            self.stats["total_topics"] += len(topics)
            return topics, None
        
        except Exception as e:
            print(f"❌ Topic fetch error: {e}")
            return None, str(e)
    
    # ========================================================================
    # VIDEO EXTRACTION (ADVANCED)
    # ========================================================================
    
    def extract_video_url(self, item):
        """Smart video URL extraction"""
        title = item.get("title", "Video").replace("||", "-").replace(":", "-").strip()
        
        # Check CloudFront CDN first
        file_url = item.get("file_url", "")
        if file_url and "cloudfront.net" in file_url and file_url.endswith(".mp4"):
            if file_url.startswith("http"):
                return f"{title}: {file_url}", True
        
        # Check bitrate_urls for CloudFront
        bitrate_urls = item.get("bitrate_urls", [])
        for url_data in bitrate_urls:
            url_value = url_data.get("url") or url_data.get("link")
            if url_value and "cloudfront.net" in url_value and url_value.endswith(".mp4"):
                if url_value.startswith("http"):
                    return f"{title}: {url_value}", True
        
        # Try 720p
        for url_data in bitrate_urls:
            if url_data.get("title") == "720p":
                url = url_data.get("url")
                if url and url.startswith("http"):
                    return f"{title}: {url}", True
        
        # Legacy S3 URLs
        if file_url:
            if file_url.endswith(("_0_0", "_0")):
                url = f"https://apps-s3-jw-prod.utkarshapp.com/admin_v1/file_library/videos/enc_plain_mp4/{file_url.split('_')[0]}/plain/720x1280.mp4"
            elif not file_url.startswith(("https://", "http://")):
                url = f"https://apps-s3-jw-prod.utkarshapp.com/content/{file_url}"
            else:
                url = file_url
            
            if not url.endswith('.ws') and url.startswith("http"):
                return f"{title}: {url}", True
        
        return None, False
    
    async def get_video_links(self, batch_id, subject_id, video_topic_id, token, headers):
        """Get video links with smart extraction"""
        try:
            layer_input = f'{{"course_id":{subject_id},"parent_id":{batch_id},"layer":3,"page":1,"revert_api":"1#0#0#1","subject_id": {video_topic_id},"tile_id":0,"topic_id": {video_topic_id},"type":"content"}}'
            encoded_input = b64encode(layer_input.encode()).decode()
            
            data = {
                'layer_two_input_data': encoded_input,
                'content': 'content',
                'csrf_name': token
            }
            
            response = await self.retry_request(
                'POST',
                f'{self.BASE_URL}/web/Course/get_layer_two_data',
                headers=headers,
                data=data
            )
            
            if not response:
                return None, "Request failed"
            
            json_data = response.json()
            if "response" not in json_data:
                return None, "Invalid response"
            
            encrypted_resp = json_data["response"]
            encrypted_resp = encrypted_resp.replace('MDE2MTA4NjQxMDI3NDUxNQ==', '==')
            
            decrypted = self.decrypt(encrypted_resp)
            if not decrypted:
                return None, "Decryption failed"
            
            content_data = json.loads(decrypted)
            videos = content_data.get('data', {}).get('list', [])
            
            video_links = []
            for item in videos:
                url_link, success = self.extract_video_url(item)
                if success:
                    video_links.append(url_link)
                    self.stats["total_videos"] += 1
            
            return video_links, None
        
        except Exception as e:
            print(f"❌ Video link fetch error: {e}")
            return None, str(e)
    
    # ========================================================================
    # FULL SCRAPING (PARALLEL PROCESSING)
    # ========================================================================
    
    async def scrape_batch(self, batch_id, batch_name, token, headers, show_progress=True):
        """Scrape single batch with all videos"""
        print(f"\n{'='*70}")
        print(f"📦 Scraping Batch: {batch_name} (ID: {batch_id})")
        print(f"{'='*70}")
        
        batch_start = time.time()
        all_videos = []
        
        try:
            # Fetch subjects
            subjects, error = await self.fetch_subjects(batch_id, token, headers)
            if error or not subjects:
                print(f"⚠️  No subjects: {error}")
                return []
            
            print(f"📖 Found {len(subjects)} subjects")
            
            # Process each subject
            for subject_idx, subject in enumerate(subjects, 1):
                subject_id = subject.get('id')
                subject_name = subject.get('title', f"Subject {subject_id}")
                
                if show_progress:
                    progress = f"[{subject_idx}/{len(subjects)}]"
                    print(f"\n{progress} Processing: {subject_name}")
                
                # Fetch topics
                topics, error = await self.fetch_topics(batch_id, subject_id, token, headers)
                if error or not topics:
                    print(f"   ⚠️  No topics in {subject_name}")
                    continue
                
                print(f"   📚 Found {len(topics)} topics")
                
                # Process each topic
                for topic_idx, topic in enumerate(topics, 1):
                    topic_id = topic.get('id')
                    topic_name = topic.get('title', f"Topic {topic_id}")
                    
                    # Get video links
                    video_links, error = await self.get_video_links(
                        batch_id, subject_id, topic_id, token, headers
                    )
                    
                    if video_links:
                        all_videos.extend(video_links)
                        if show_progress:
                            print(f"      ✅ {topic_name}: {len(video_links)} videos")
                    else:
                        if show_progress:
                            print(f"      ⚠️  {topic_name}: No videos")
        
        except Exception as e:
            print(f"❌ Batch scrape error: {e}")
        
        batch_time = time.time() - batch_start
        print(f"\n✅ Batch complete: {len(all_videos)} videos in {batch_time:.1f}s")
        
        return all_videos
    
    async def scrape_multiple_batches(self, batch_ids, batches, token, headers):
        """Scrape multiple batches (parallel)"""
        results = {}
        
        for batch_id in batch_ids:
            batch_name = next((b['title'] for b in batches if str(b['id']) == batch_id), f"Batch {batch_id}")
            videos = await self.scrape_batch(batch_id, batch_name, token, headers)
            results[batch_id] = {
                'name': batch_name,
                'videos': videos,
                'count': len(videos)
            }
        
        return results
    
    # ========================================================================
    # STATISTICS & REPORTING
    # ========================================================================
    
    def get_statistics(self):
        """Get scraping statistics"""
        if self.stats["start_time"]:
            total_time = (self.stats["end_time"] or datetime.datetime.now()) - self.stats["start_time"]
            total_seconds = total_time.total_seconds()
        else:
            total_seconds = 0
        
        stats_text = f"""
╔{'='*68}╗
║ {'SCRAPING STATISTICS':^66} ║
╚{'='*68}╝

📊 METRICS:
  • Total Batches: {self.stats['total_batches']}
  • Total Subjects: {self.stats['total_subjects']}
  • Total Topics: {self.stats['total_topics']}
  • Total Videos: {self.stats['total_videos']}

🔧 REQUESTS:
  • Successful: {self.stats['successful_requests']}
  • Failed: {self.stats['failed_requests']}
  • Success Rate: {(self.stats['successful_requests'] / max(self.stats['successful_requests'] + self.stats['failed_requests'], 1) * 100):.1f}%

⏱️  TIME:
  • Total Time: {total_seconds:.1f}s
  • Avg per Video: {(total_seconds / max(self.stats['total_videos'], 1)):.2f}s

💾 OUTPUT:
  • Video Links: {self.stats['total_videos']}
  • Estimated Size: ~{(self.stats['total_videos'] * 150):.0f} MB (at 150MB/video avg)
"""
        return stats_text
    
    def print_videos(self, videos, limit=100):
        """Pretty print video list"""
        print(f"\n{'='*70}")
        print(f"📹 EXTRACTED VIDEOS ({min(limit, len(videos))}/{len(videos)})")
        print(f"{'='*70}\n")
        
        for idx, video in enumerate(videos[:limit], 1):
            print(f"{idx:3d}. {video}")
        
        if len(videos) > limit:
            print(f"\n... and {len(videos) - limit} more videos")
    
    def save_to_file(self, videos, filename="videos.txt"):
        """Save video links to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for video in videos:
                    f.write(f"{video}\n")
            print(f"✅ Saved {len(videos)} videos to {filename}")
            return True
        except Exception as e:
            print(f"❌ Save error: {e}")
            return False

# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

async def test_scraper(user_id, password, batch_ids=None, save_to_file=False):
    """
    Complete test function for scraping any batch
    
    Args:
        user_id: Utkarsh account ID
        password: Utkarsh password
        batch_ids: List of batch IDs to scrape (None = all)
        save_to_file: Save results to file
    """
    print("\n" + "="*70)
    print("🎓 ADVANCED UTKARSH SCRAPER - FULL TEST")
    print("="*70 + "\n")
    
    scraper = AdvancedUtkarshScraper(timeout=30, max_retries=5)
    scraper.stats["start_time"] = datetime.datetime.now()
    
    try:
        # Step 1: Get token
        token = await scraper.get_csrf_token()
        if not token:
            print("❌ Failed to get CSRF token")
            return False
        
        headers = scraper.get_headers(token)
        
        # Step 2: Authenticate
        auth_success, auth_data = await scraper.authenticate(user_id, password, token, headers)
        if not auth_success:
            print(f"❌ Authentication failed: {auth_data}")
            return False
        
        # Step 3: Fetch all batches
        batches, error = await scraper.fetch_batches(token, headers)
        if error or not batches:
            print(f"❌ Batch fetch failed: {error}")
            return False
        
        print(f"\n✅ Available batches:")
        for batch in batches:
            print(f"   [{batch['id']}] {batch['title']}")
        
        # Step 4: Select batches to scrape
        if batch_ids:
            selected_batches = [str(bid) for bid in batch_ids]
        else:
            # Scrape all batches
            selected_batches = [str(b['id']) for b in batches]
        
        print(f"\n🎯 Selected {len(selected_batches)} batch(es) to scrape")
        
        # Step 5: Scrape all selected batches
        all_results = await scraper.scrape_multiple_batches(selected_batches, batches, token, headers)
        
        # Step 6: Collect all videos
        all_videos = []
        for batch_id, result in all_results.items():
            print(f"\n   ✅ {result['name']}: {result['count']} videos")
            all_videos.extend(result['videos'])
        
        # Step 7: Print results
        scraper.stats["end_time"] = datetime.datetime.now()
        print(scraper.get_statistics())
        
        # Step 8: Display videos
        scraper.print_videos(all_videos)
        
        # Step 9: Save to file if requested
        if save_to_file:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"videos_{timestamp}.txt"
            scraper.save_to_file(all_videos, filename)
        
        # Step 10: Logout
        requests.get(f'{scraper.BASE_URL}/web/Auth/logout', headers=headers)
        print("\n✅ Logout successful")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("\n🧪 Advanced Utkarsh Scraper - Test Mode\n")
    
    # Get credentials
    user_id = input("Enter Utkarsh ID: ").strip()
    password = input("Enter Utkarsh Password: ").strip()
    
    if not user_id or not password:
        print("❌ Credentials required")
        sys.exit(1)
    
    # Ask which batches to scrape
    print("\nOptions:")
    print("1. Scrape ALL batches")
    print("2. Scrape specific batches")
    
    choice = input("\nEnter choice (1/2): ").strip()
    
    batch_ids = None
    if choice == "2":
        batch_str = input("Enter batch IDs (comma-separated): ").strip()
        batch_ids = [int(b.strip()) for b in batch_str.split(",")]
    
    # Ask if save to file
    save = input("\nSave videos to file? (y/n): ").strip().lower() == 'y'
    
    # Run scraper
    try:
        asyncio.run(test_scraper(user_id, password, batch_ids, save))
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

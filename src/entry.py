from workers import WorkerEntrypoint, Response
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import urllib.parse
import base64
import hashlib
import hmac

class SimpleEncryption:
    """Simple encryption using built-in Python libraries compatible with Workers runtime"""
    
    def __init__(self, key: str = "student-checkin-key-2024"):
        self.key = key.encode('utf-8')
        # Create a consistent key for XOR encryption
        self.encryption_key = hashlib.sha256(self.key).digest()
    
    def _xor_encrypt_decrypt(self, data: bytes, key: bytes) -> bytes:
        """XOR encryption/decryption - symmetric operation"""
        result = bytearray()
        key_len = len(key)
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % key_len])
        return bytes(result)
    
    def encrypt_name(self, name: str) -> str:
        """Encrypt a student name using XOR + Base64"""
        try:
            # Convert to bytes
            name_bytes = name.encode('utf-8')
            
            # XOR encrypt
            encrypted_bytes = self._xor_encrypt_decrypt(name_bytes, self.encryption_key)
            
            # Base64 encode for safe storage
            encoded = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            # Add a prefix to identify encrypted data
            return f"ENC:{encoded}"
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return name  # Fallback to plain text
    
    def decrypt_name(self, encrypted_name: str) -> str:
        """Decrypt a student name"""
        try:
            # Check if it's encrypted
            if not encrypted_name.startswith("ENC:"):
                return encrypted_name  # Plain text
            
            # Remove prefix and decode
            encoded_data = encrypted_name[4:]  # Remove "ENC:" prefix
            encrypted_bytes = base64.b64decode(encoded_data.encode('utf-8'))
            
            # XOR decrypt (same operation as encrypt)
            decrypted_bytes = self._xor_encrypt_decrypt(encrypted_bytes, self.encryption_key)
            
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_name  # Return as-is if decryption fails
    
    def is_encrypted(self, name: str) -> bool:
        """Check if a name is encrypted"""
        return name.startswith("ENC:")
    
    def format_display_name(self, full_name: str) -> str:
        """Format name as 'First Name L.' for privacy"""
        try:
            parts = full_name.strip().split()
            if len(parts) == 0:
                return "Unknown"
            elif len(parts) == 1:
                return parts[0]  # Just first name if only one name
            else:
                first_name = parts[0]
                last_initial = parts[-1][0].upper() if parts[-1] else ""
                return f"{first_name} {last_initial}." if last_initial else first_name
        except:
            return full_name  # Fallback to original if parsing fails

class DatabaseManager:
    def __init__(self, db_binding, encryption_manager: SimpleEncryption):
        self.db = db_binding
        self.encryption = encryption_manager
    
    async def execute_query(self, sql: str, params: list = None) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            if params:
                result = await self.db.prepare(sql).bind(*params).run()
            else:
                result = await self.db.prepare(sql).run()
            
            # Convert JsProxy objects to Python objects
            converted_result = {
                "success": True,
                "results": [],
                "meta": {}
            }
            
            async loadSpaceManagement() {
                try {
                    const response = await fetch('/spaces');
                    const data = await response.json();
                    const spaces = data.spaces || [];
                    
                    const container = document.getElementById('spaceManagement');
                    
                    if (spaces.length === 0) {
                        container.innerHTML = '<div class="status info">No spaces configured</div>';
                        return;
                    }
                    
                    container.innerHTML = spaces.map(space => `
                        <div class="space-management-item">
                            <div class="space-info">
                                <div class="space-title">${space.space_name}</div>
                                <div class="space-desc">${space.description || 'No description'}</div>
                            </div>
                            <div class="space-actions">
                                <button onclick="adminDashboard.editSpace(${space.space_id}, '${space.space_name.replace(/'/g, "\\'")}', '${(space.description || '').replace(/'/g, "\\'")}')">Edit</button>
                                <button class="danger" onclick="adminDashboard.deleteSpace(${space.space_id}, '${space.space_name.replace(/'/g, "\\'")}')">Delete</button>
                            </div>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('Failed to load spaces:', error);
                    document.getElementById('spaceManagement').innerHTML = 
                        '<div class="status error">Failed to load spaces</div>';
                }
            }
            
            showAddSpaceModal() {
                this.currentEditingSpaceId = null;
                document.getElementById('modalTitle').textContent = 'Add New Space';
                document.getElementById('spaceName').value = '';
                document.getElementById('spaceDescription').value = '';
                document.getElementById('spaceModal').style.display = 'block';
                document.getElementById('spaceName').focus();
            }
            
            editSpace(spaceId, spaceName, description) {
                this.currentEditingSpaceId = spaceId;
                document.getElementById('modalTitle').textContent = 'Edit Space';
                document.getElementById('spaceName').value = spaceName;
                document.getElementById('spaceDescription').value = description;
                document.getElementById('spaceModal').style.display = 'block';
                document.getElementById('spaceName').focus();
            }
            
            hideSpaceModal() {
                document.getElementById('spaceModal').style.display = 'none';
                this.currentEditingSpaceId = null;
            }
            
            async saveSpace() {
                const spaceName = document.getElementById('spaceName').value.trim();
                const description = document.getElementById('spaceDescription').value.trim();
                
                if (!spaceName) {
                    this.showSpaceStatus('Space name is required', 'error');
                    return;
                }
                
                try {
                    let response;
                    if (this.currentEditingSpaceId) {
                        // Update existing space
                        response = await fetch(`/spaces/${this.currentEditingSpaceId}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ space_name: spaceName, description })
                        });
                    } else {
                        // Create new space
                        response = await fetch('/spaces', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ space_name: spaceName, description })
                        });
                    }
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.showSpaceStatus(data.message, 'success');
                        this.hideSpaceModal();
                        await this.loadSpaceManagement();
                        await this.loadSpaceOccupancy(); // Refresh occupancy too
                    } else {
                        this.showSpaceStatus(data.message, 'error');
                    }
                } catch (error) {
                    this.showSpaceStatus('Failed to save space', 'error');
                }
            }
            
            async deleteSpace(spaceId, spaceName) {
                if (!confirm(`Are you sure you want to delete "${spaceName}"? This cannot be undone.`)) {
                    return;
                }
                
                try {
                    const response = await fetch(`/spaces/${spaceId}`, {
                        method: 'DELETE'
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.showSpaceStatus(data.message, 'success');
                        await this.loadSpaceManagement();
                        await this.loadSpaceOccupancy(); // Refresh occupancy too
                    } else {
                        this.showSpaceStatus(data.message, 'error');
                    }
                } catch (error) {
                    this.showSpaceStatus('Failed to delete space', 'error');
                }
            }
            
            showSpaceStatus(message, type) {
                const element = document.getElementById('spaceStatus');
                element.textContent = message;
                element.className = `status ${type}`;
                element.classList.remove('hidden');
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    element.classList.add('hidden');
                }, 5000);
            }
            
            # Convert results if they exist
            if hasattr(result, 'results') and result.results is not None:
                converted_result["results"] = []
                try:
                    results_list = list(result.results)
                    for row in results_list:
                        row_dict = {}
                        try:
                            if hasattr(row, 'toJs'):
                                js_obj = row.toJs()
                                row_dict = js_obj.to_py()
                            elif hasattr(row, 'to_py'):
                                row_dict = row.to_py()
                            else:
                                row_dict = dict(row)
                        except:
                            try:
                                row_dict = {"count": row.count} if hasattr(row, 'count') else {}
                            except:
                                row_dict = {}
                        
                        converted_result["results"].append(row_dict)
                except Exception as e:
                    converted_result["results"] = []
            
            # Convert meta if it exists
            if hasattr(result, 'meta') and result.meta is not None:
                try:
                    meta = result.meta
                    converted_result["meta"] = {}
                    
                    if hasattr(meta, 'duration'):
                        converted_result["meta"]["duration"] = float(meta.duration)
                    if hasattr(meta, 'changes'):
                        converted_result["meta"]["changes"] = int(meta.changes)
                    if hasattr(meta, 'last_row_id'):
                        converted_result["meta"]["last_row_id"] = int(meta.last_row_id)
                        
                except Exception as e:
                    converted_result["meta"] = {"conversion_error": str(e)}
            
            return converted_result
            
        except Exception as e:
            print(f"Database error: {e}")
            return {"success": False, "error": str(e)}
    
    # Student operations with encryption
    async def create_student(self, student_number: str, plain_name: str) -> bool:
        """Add a new student to the database with encrypted name"""
        encrypted_name = self.encryption.encrypt_name(plain_name)
        sql = "INSERT INTO students (student_number, encrypted_name) VALUES (?, ?)"
        result = await self.execute_query(sql, [student_number, encrypted_name])
        return result.get("success", False)
    
    async def get_student_by_number(self, student_number: str, decrypt_name: bool = True) -> Optional[Dict]:
        """Find a student by their student number"""
        sql = "SELECT * FROM students WHERE student_number = ?"
        result = await self.execute_query(sql, [student_number])
        
        if result.get("success") and result.get("results"):
            student = result["results"][0]
            if decrypt_name and student.get("encrypted_name"):
                # Add formatted display name for privacy
                full_name = self.encryption.decrypt_name(student["encrypted_name"])
                student["display_name"] = self.encryption.format_display_name(full_name)
            return student
        return None
    
    async def get_all_students(self, decrypt_names: bool = True) -> List[Dict]:
        """Get all students"""
        sql = "SELECT * FROM students ORDER BY student_number"
        result = await self.execute_query(sql)
        
        if result.get("success"):
            students = result.get("results", [])
            if decrypt_names:
                for student in students:
                    if student.get("encrypted_name"):
                        full_name = self.encryption.decrypt_name(student["encrypted_name"])
                        student["display_name"] = self.encryption.format_display_name(full_name)
            return students
        return []
    
    async def search_students(self, search_term: str) -> List[Dict]:
        """Search students by name or student number"""
        # For encrypted names, we need to get all students and search in memory
        all_students = await self.get_all_students(decrypt_names=True)
        
        matching_students = []
        search_lower = search_term.lower()
        
        for student in all_students:
            student_number = str(student.get("student_number", "")).lower()
            display_name = str(student.get("display_name", "")).lower()
            
            # Also search against full decrypted name for admin searches
            full_name = ""
            if student.get("encrypted_name"):
                full_name = self.encryption.decrypt_name(student["encrypted_name"]).lower()
            
            if (search_lower in student_number or 
                search_lower in display_name or 
                search_lower in full_name):
                matching_students.append(student)
        
        return matching_students
    
    # Space operations (unchanged)
    async def get_all_spaces(self) -> List[Dict]:
        """Get all available spaces"""
        sql = "SELECT * FROM spaces ORDER BY space_name"
        result = await self.execute_query(sql)
        
        if result.get("success"):
            return result.get("results", [])
        return []
    
    # Space CRUD operations
    async def create_space(self, space_name: str, description: str = "") -> bool:
        """Create a new space"""
        sql = "INSERT INTO spaces (space_name, description) VALUES (?, ?)"
        result = await self.execute_query(sql, [space_name, description])
        return result.get("success", False)
    
    async def update_space(self, space_id: int, space_name: str, description: str = "") -> bool:
        """Update an existing space"""
        sql = "UPDATE spaces SET space_name = ?, description = ? WHERE space_id = ?"
        result = await self.execute_query(sql, [space_name, description, space_id])
        return result.get("success", False) and result.get("meta", {}).get("changes", 0) > 0
    
    async def delete_space(self, space_id: int) -> Dict[str, Any]:
        """Delete a space (only if no active check-ins)"""
        # First check if there are any active check-ins for this space
        check_sql = "SELECT COUNT(*) as count FROM check_ins WHERE space_id = ? AND time_out IS NULL"
        check_result = await self.execute_query(check_sql, [space_id])
        
        if check_result.get("success") and check_result.get("results"):
            active_count = check_result["results"][0]["count"]
            if active_count > 0:
                return {"success": False, "error": f"Cannot delete space with {active_count} active check-ins"}
        
        # Delete the space
        sql = "DELETE FROM spaces WHERE space_id = ?"
        result = await self.execute_query(sql, [space_id])
        
        if result.get("success") and result.get("meta", {}).get("changes", 0) > 0:
            return {"success": True, "message": "Space deleted successfully"}
        else:
            return {"success": False, "error": "Space not found or could not be deleted"}
    
    # Check-in operations
    async def create_checkin(self, student_id: int, space_id: int) -> bool:
        """Create a new check-in record"""
        sql = "INSERT INTO check_ins (student_id, space_id, time_in) VALUES (?, ?, ?)"
        current_time = datetime.utcnow().isoformat()
        result = await self.execute_query(sql, [student_id, space_id, current_time])
        return result.get("success", False)
    
    async def get_student_current_checkin(self, student_id: int) -> Optional[Dict]:
        """Get student's current check-in if any"""
        sql = """SELECT ci.*, sp.space_name 
                 FROM check_ins ci
                 JOIN spaces sp ON ci.space_id = sp.space_id
                 WHERE ci.student_id = ? 
                 AND ci.time_out IS NULL 
                 ORDER BY ci.time_in DESC 
                 LIMIT 1"""
        result = await self.execute_query(sql, [student_id])
        
        if result.get("success") and result.get("results"):
            return result["results"][0]
        return None
    
    async def checkout_from_all_spaces(self, student_id: int) -> int:
        """Check out student from all spaces they're currently in"""
        sql = """UPDATE check_ins 
                 SET time_out = ? 
                 WHERE student_id = ? 
                 AND time_out IS NULL"""
        current_time = datetime.utcnow().isoformat()
        result = await self.execute_query(sql, [current_time, student_id])
        return result.get("meta", {}).get("changes", 0)
    
    async def checkout_all_students(self) -> int:
        """Check out all currently checked-in students"""
        sql = """UPDATE check_ins 
                 SET time_out = ? 
                 WHERE time_out IS NULL"""
        current_time = datetime.utcnow().isoformat()
        result = await self.execute_query(sql, [current_time])
        return result.get("meta", {}).get("changes", 0)
    
    async def checkout_student(self, student_id: int, space_id: int) -> bool:
        """Update check-in record with checkout time"""
        sql = """UPDATE check_ins 
                 SET time_out = ? 
                 WHERE student_id = ? 
                 AND space_id = ? 
                 AND time_out IS NULL 
                 ORDER BY time_in DESC 
                 LIMIT 1"""
        current_time = datetime.utcnow().isoformat()
        result = await self.execute_query(sql, [current_time, student_id, space_id])
        return result.get("success", False)
    
    async def get_current_checkins(self, space_id: Optional[int] = None) -> List[Dict]:
        """Get all current check-ins with decrypted names and grade info"""
        if space_id:
            sql = """SELECT ci.*, s.student_number, s.encrypted_name, s.grade, sp.space_name
                     FROM check_ins ci
                     JOIN students s ON ci.student_id = s.student_id
                     JOIN spaces sp ON ci.space_id = sp.space_id
                     WHERE ci.time_out IS NULL AND ci.space_id = ?
                     ORDER BY ci.time_in DESC"""
            result = await self.execute_query(sql, [space_id])
        else:
            sql = """SELECT ci.*, s.student_number, s.encrypted_name, s.grade, sp.space_name
                     FROM check_ins ci
                     JOIN students s ON ci.student_id = s.student_id
                     JOIN spaces sp ON ci.space_id = sp.space_id
                     WHERE ci.time_out IS NULL
                     ORDER BY ci.time_in DESC"""
            result = await self.execute_query(sql)
        
        if result.get("success"):
            checkins = result.get("results", [])
            # Decrypt names for display
            for checkin in checkins:
                if checkin.get("encrypted_name"):
                    full_name = self.encryption.decrypt_name(checkin["encrypted_name"])
                    checkin["display_name"] = self.encryption.format_display_name(full_name)
            return checkins
        return []
    
    async def is_student_checked_in(self, student_id: int, space_id: int) -> bool:
        """Check if a student is currently checked into a space"""
        sql = """SELECT COUNT(*) as count 
                 FROM check_ins 
                 WHERE student_id = ? 
                 AND space_id = ? 
                 AND time_out IS NULL"""
        result = await self.execute_query(sql, [student_id, space_id])
        
        if result.get("success") and result.get("results"):
            return result["results"][0]["count"] > 0
        return False

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Initialize simple encryption
        encryption_key = getattr(self.env, 'ENCRYPTION_KEY', None) or "student-checkin-secure-2024"
        encryption = SimpleEncryption(encryption_key)
        
        # Initialize database manager with encryption
        db = DatabaseManager(self.env.DB, encryption)
        
        # Get URL path to determine what action to take
        url = request.url
        path_parts = url.split('/')
        path = path_parts[-1] if len(path_parts) > 1 else ''
        
        # Handle query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        try:
            # Handle different endpoints
            if path == 'debug-db' and request.method == 'GET':
                return await self.debug_database(db)
            
            elif path == 'init-db' and request.method == 'GET':
                return await self.init_database(db)
            
            elif path == 'add-test-students' and request.method == 'GET':
                return await self.add_test_students(db)
            
            elif path == 'migrate-encryption' and request.method == 'GET':
                return await self.migrate_to_encryption(db)
            
            elif path == 'test-encryption' and request.method == 'GET':
                return await self.test_encryption(encryption)
            
            elif path == 'checkin' and request.method == 'POST':
                return await self.handle_checkin(db, request)
            
            elif path == 'checkout' and request.method == 'POST':
                return await self.handle_checkout(db, request)
            
            elif path == 'web' and request.method == 'GET':
                return await self.serve_web_interface()
            
            elif path == 'admin' and request.method == 'GET':
                return await self.serve_admin_dashboard()
            
            elif path == 'search' and request.method == 'GET':
                return await self.handle_search(db, request)
            
            elif path == 'bulk-checkout' and request.method == 'POST':
                return await self.bulk_checkout_all(db)
            
            elif path.startswith('checkin-') and request.method == 'GET':
                return await self.quick_checkin(db, path)
            
            elif path.startswith('checkout-') and request.method == 'GET':
                return await self.quick_checkout(db, path)
            
            elif path == 'students' and request.method == 'GET':
                return await self.list_students(db)
            
            elif path == 'spaces' and request.method == 'GET':
                return await self.list_spaces(db)
            
            elif path == 'spaces' and request.method == 'POST':
                return await self.create_space_endpoint(db, request)
            
            elif path.startswith('spaces/') and request.method == 'PUT':
                space_id = int(path.split('/')[-1])
                return await self.update_space_endpoint(db, request, space_id)
            
            elif path.startswith('spaces/') and request.method == 'DELETE':
                space_id = int(path.split('/')[-1])
                return await self.delete_space_endpoint(db, space_id)
            
            elif path == 'current-checkins' and request.method == 'GET':
                return await self.current_checkins(db)
            
            else:
                # Default response
                return Response(
                    json.dumps({
                        "message": "Student Check-in System API with Simple Encryption",
                        "security": "Student names encrypted using XOR cipher with Base64 encoding",
                        "compatibility": "Uses only built-in Python libraries for Workers compatibility",
                        "endpoints": {
                            "/web": "GET - Web interface for barcode scanning and check-ins",
                            "/admin": "GET - Admin dashboard for monitoring and search",
                            "/debug-db": "GET - Debug database connection",
                            "/init-db": "GET - Initialize database tables",
                            "/add-test-students": "GET - Add sample students (with encryption)",
                            "/migrate-encryption": "GET - Migrate existing plain text names to encrypted",
                            "/test-encryption": "GET - Test encryption/decryption functionality",
                            "/students": "GET - List all students (names decrypted for display)",
                            "/spaces": "GET - List all spaces",
                            "/spaces": "POST - Create new space (JSON: {space_name, description})",
                            "/spaces/{id}": "PUT - Update space (JSON: {space_name, description})",
                            "/spaces/{id}": "DELETE - Delete space (if no active check-ins)",
                            "/current-checkins": "GET - Show current check-ins",
                            "/search?q=term": "GET - Search students by name or number",
                            "/checkin-{student_number}-{space_id}": "GET - Quick checkin",
                            "/checkout-{student_number}-{space_id}": "GET - Quick checkout",
                            "/bulk-checkout": "POST - Check out all students"
                        }
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"error": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def test_encryption(self, encryption: SimpleEncryption):
        """Test encryption functionality"""
        try:
            test_names = ["Alice Johnson", "Bob Smith", "Maria García", "李明", "John O'Connor"]
            
            results = []
            for name in test_names:
                encrypted = encryption.encrypt_name(name)
                decrypted = encryption.decrypt_name(encrypted)
                is_encrypted = encryption.is_encrypted(encrypted)
                hmac_signature = encryption.create_hmac(name)
                
                results.append({
                    "original": name,
                    "encrypted": encrypted,
                    "decrypted": decrypted,
                    "is_encrypted": is_encrypted,
                    "match": name == decrypted,
                    "hmac": hmac_signature[:16] + "..."  # Show first 16 chars
                })
            
            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Simple encryption test completed",
                    "encryption_method": "XOR cipher with Base64 encoding",
                    "results": results,
                    "all_passed": all(r["match"] for r in results)
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def migrate_to_encryption(self, db: DatabaseManager):
        """Migrate existing plain text names to encrypted format"""
        try:
            # Get all students
            sql = "SELECT * FROM students"
            result = await db.execute_query(sql)
            
            if not result.get("success"):
                return Response(
                    json.dumps({"status": "error", "message": "Failed to fetch students"}),
                    status=500,
                    headers={"Content-Type": "application/json"}
                )
            
            students = result.get("results", [])
            migrated_count = 0
            
            for student in students:
                encrypted_name = student.get("encrypted_name", "")
                
                # Check if already encrypted
                if not db.encryption.is_encrypted(encrypted_name):
                    # Encrypt the plain text name
                    new_encrypted_name = db.encryption.encrypt_name(encrypted_name)
                    
                    # Update the database
                    update_sql = "UPDATE students SET encrypted_name = ? WHERE student_id = ?"
                    update_result = await db.execute_query(update_sql, [new_encrypted_name, student["student_id"]])
                    
                    if update_result.get("success"):
                        migrated_count += 1
            
            return Response(
                json.dumps({
                    "status": "success",
                    "message": f"Migration completed. {migrated_count} students migrated to encrypted names.",
                    "total_students": len(students),
                    "migrated": migrated_count
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def add_test_students(self, db: DatabaseManager):
        """Add test students with encrypted names"""
        try:
            test_students = [
                ("12345", "Alice Johnson"),
                ("23456", "Bob Smith"), 
                ("34567", "Carol Davis"),
                ("45678", "David Wilson"),
                ("56789", "Emma Brown"),
                ("67890", "Frank Miller"),
                ("78901", "Grace Lee"),
                ("89012", "Henry Taylor")
            ]
            
            added_students = []
            for student_number, name in test_students:
                # Check if student already exists
                existing = await db.get_student_by_number(student_number, decrypt_name=False)
                if existing:
                    continue  # Skip if already exists
                
                # The create_student method handles encryption automatically
                result = await db.create_student(student_number, name)
                if result:
                    added_students.append({
                        "student_number": student_number, 
                        "original_name": name,
                        "encrypted": True
                    })
            
            return Response(
                json.dumps({
                    "status": "success",
                    "message": f"Added {len(added_students)} test students with encrypted names",
                    "students_added": added_students
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def handle_search(self, db: DatabaseManager, request):
        """Handle search requests with encrypted name support"""
        try:
            url = str(request.url)
            
            if '?' not in url or 'q=' not in url:
                return Response(
                    json.dumps({"status": "error", "message": "Missing search parameter 'q'"}),
                    headers={"Content-Type": "application/json"}
                )
            
            # Extract search term
            query_string = url.split('?', 1)[1]
            params = {}
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    value = urllib.parse.unquote_plus(value)
                    params[key] = value
            
            search_term = params.get('q', '').strip()
            
            if not search_term:
                return Response(
                    json.dumps({"status": "error", "message": "Empty search term"}),
                    headers={"Content-Type": "application/json"}
                )
            
            # Search using the encrypted-aware search method
            students = await db.search_students(search_term)
            
            # Build results with current check-in status
            results = []
            for student in students:
                current_checkin = await db.get_student_current_checkin(student["student_id"])
                
                result = {
                    "student": {
                        "student_id": student["student_id"],
                        "student_number": student["student_number"],
                        "encrypted_name": student.get("display_name", student.get("encrypted_name", ""))
                    },
                    "current_location": None,
                    "check_in_time": None
                }
                
                if current_checkin:
                    result["current_location"] = current_checkin["space_name"]
                    result["check_in_time"] = current_checkin["time_in"]
                
                results.append(result)
            
            return Response(
                json.dumps({
                    "status": "success",
                    "search_term": search_term,
                    "results": results,
                    "count": len(results)
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    # Include all the remaining methods with the same implementations as before
    # (debug_database, init_database, quick_checkin, quick_checkout, etc.)
    
    async def debug_database(self, db: DatabaseManager):
        """Debug database connection and basic operations"""
        try:
            simple_result = await db.execute_query("SELECT 1 as test")
            tables_result = await db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            
            return Response(
                json.dumps({
                    "debug_info": {
                        "simple_query_success": simple_result.get("success", False),
                        "simple_query_results": simple_result.get("results", []),
                        "tables_success": tables_result.get("success", False),
                        "existing_tables": [row.get("name", "") for row in tables_result.get("results", [])],
                        "db_binding_exists": hasattr(self.env, 'DB'),
                        "encryption_enabled": True,
                        "encryption_type": "Simple XOR + Base64"
                    }
                }),
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            return Response(
                json.dumps({
                    "debug_error": str(e),
                    "error_type": type(e).__name__,
                    "has_db_binding": hasattr(self.env, 'DB')
                }),
                headers={"Content-Type": "application/json"}
            )
    
    async def init_database(self, db: DatabaseManager):
        """Initialize database with tables"""
        try:
            results = []
            
            # Create students table
            students_result = await db.execute_query("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_number TEXT UNIQUE NOT NULL,
                    encrypted_name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            results.append(f"Students table: {students_result}")
            
            # Create spaces table
            spaces_result = await db.execute_query("""
                CREATE TABLE IF NOT EXISTS spaces (
                    space_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    space_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            results.append(f"Spaces table: {spaces_result}")
            
            # Create check_ins table
            checkins_result = await db.execute_query("""
                CREATE TABLE IF NOT EXISTS check_ins (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    space_id INTEGER NOT NULL,
                    time_in DATETIME NOT NULL,
                    time_out DATETIME NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students (student_id),
                    FOREIGN KEY (space_id) REFERENCES spaces (space_id)
                )
            """)
            results.append(f"Check-ins table: {checkins_result}")
            
            return Response(
                json.dumps({
                    "status": "success",
                    "message": "Database initialized with simple encryption support",
                    "encryption_enabled": True,
                    "encryption_type": "XOR cipher with Base64 encoding",
                    "debug_results": results
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({
                    "status": "error", 
                    "message": str(e),
                    "error_type": type(e).__name__
                }),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def list_students(self, db: DatabaseManager):
        """List all students with decrypted names"""
        students = await db.get_all_students(decrypt_names=True)
        # For API response, use display_name as encrypted_name for compatibility
        for student in students:
            if "display_name" in student:
                student["encrypted_name"] = student["display_name"]
        
        return Response(
            json.dumps({"students": students}),
            headers={"Content-Type": "application/json"}
        )
    
    async def current_checkins(self, db: DatabaseManager):
        """Show current check-ins with decrypted names"""
        checkins = await db.get_current_checkins()
        # For API response, use display_name as encrypted_name for compatibility
        for checkin in checkins:
            if "display_name" in checkin:
                checkin["encrypted_name"] = checkin["display_name"]
        
        return Response(
            json.dumps({"current_checkins": checkins}),
            headers={"Content-Type": "application/json"}
        )
    
    async def quick_checkin(self, db: DatabaseManager, path):
        """Handle quick check-in with encrypted name support"""
        try:
            parts = path.split('-')
            if len(parts) != 3:
                return Response(
                    json.dumps({"status": "error", "message": "Invalid format"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            student_number = parts[1]
            space_id = int(parts[2])
            
            # Find student (with decrypted name)
            student = await db.get_student_by_number(student_number, decrypt_name=True)
            if not student:
                return Response(
                    json.dumps({"status": "error", "message": f"Student {student_number} not found"}),
                    status=404,
                    headers={"Content-Type": "application/json"}
                )
            
            student_id = student["student_id"]
            display_name = student.get("display_name", "Unknown")
            
            # Check if already checked in to this space
            is_checked_in_here = await db.is_student_checked_in(student_id, space_id)
            if is_checked_in_here:
                return Response(
                    json.dumps({"status": "error", "message": f"Student {student_number} already checked into this space"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Check if checked into another space and auto-checkout
            current_checkin = await db.get_student_current_checkin(student_id)
            previous_location = None
            
            if current_checkin:
                previous_location = current_checkin["space_name"]
                await db.checkout_from_all_spaces(student_id)
            
            # Create new check-in
            success = await db.create_checkin(student_id, space_id)
            if success:
                space = await db.get_space_by_id(space_id)
                
                if previous_location:
                    message = f"✅ Student {student_number} ({display_name}) moved from {previous_location} to {space['space_name'] if space else 'Unknown Space'}"
                else:
                    message = f"✅ Student {student_number} ({display_name}) checked into {space['space_name'] if space else 'Unknown Space'}"
                
                return Response(
                    json.dumps({
                        "status": "success",
                        "message": message,
                        "student": {"student_number": student_number, "display_name": display_name},
                        "space": space,
                        "previous_location": previous_location,
                        "action": "moved" if previous_location else "checked_in"
                    }),
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    json.dumps({"status": "error", "message": "Failed to create check-in"}),
                    status=500,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def quick_checkout(self, db: DatabaseManager, path):
        """Handle quick check-out with encrypted name support"""
        try:
            parts = path.split('-')
            if len(parts) != 3:
                return Response(
                    json.dumps({"status": "error", "message": "Invalid format"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            student_number = parts[1]
            space_id = int(parts[2])
            
            # Find student (with decrypted name)
            student = await db.get_student_by_number(student_number, decrypt_name=True)
            if not student:
                return Response(
                    json.dumps({"status": "error", "message": f"Student {student_number} not found"}),
                    status=404,
                    headers={"Content-Type": "application/json"}
                )
            
            display_name = student.get("display_name", "Unknown")
            
            # Check if actually checked in
            is_checked_in = await db.is_student_checked_in(student["student_id"], space_id)
            if not is_checked_in:
                return Response(
                    json.dumps({"status": "error", "message": f"Student {student_number} not currently checked into this space"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            # Check out
            success = await db.checkout_student(student["student_id"], space_id)
            if success:
                space = await db.get_space_by_id(space_id)
                return Response(
                    json.dumps({
                        "status": "success",
                        "message": f"✅ Student {student_number} ({display_name}) checked out of {space['space_name'] if space else 'Unknown Space'}",
                        "student": {"student_number": student_number, "display_name": display_name},
                        "space": space
                    }),
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    json.dumps({"status": "error", "message": "Failed to check out"}),
                    status=500,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def bulk_checkout_all(self, db: DatabaseManager):
        """Check out all currently checked-in students"""
        try:
            count = await db.checkout_all_students()
            
            return Response(
                json.dumps({
                    "status": "success",
                    "message": f"Successfully checked out {count} students",
                    "checked_out_count": count
                }),
                headers={"Content-Type": "application/json"}
            )
            
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def list_spaces(self, db: DatabaseManager):
        """List all spaces"""
        spaces = await db.get_all_spaces()
        return Response(
            json.dumps({"spaces": spaces}),
            headers={"Content-Type": "application/json"}
        )
    
    async def create_space_endpoint(self, db: DatabaseManager, request):
        """Create a new space"""
        try:
            body = await request.json()
            space_name = body.get("space_name", "").strip()
            description = body.get("description", "").strip()
            
            if not space_name:
                return Response(
                    json.dumps({"status": "error", "message": "Space name is required"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            success = await db.create_space(space_name, description)
            
            if success:
                return Response(
                    json.dumps({
                        "status": "success",
                        "message": f"Space '{space_name}' created successfully"
                    }),
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    json.dumps({"status": "error", "message": "Failed to create space (name may already exist)"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def update_space_endpoint(self, db: DatabaseManager, request, space_id: int):
        """Update an existing space"""
        try:
            body = await request.json()
            space_name = body.get("space_name", "").strip()
            description = body.get("description", "").strip()
            
            if not space_name:
                return Response(
                    json.dumps({"status": "error", "message": "Space name is required"}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
            
            success = await db.update_space(space_id, space_name, description)
            
            if success:
                return Response(
                    json.dumps({
                        "status": "success",
                        "message": f"Space updated successfully"
                    }),
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    json.dumps({"status": "error", "message": "Space not found or name already exists"}),
                    status=404,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def delete_space_endpoint(self, db: DatabaseManager, space_id: int):
        """Delete a space"""
        try:
            result = await db.delete_space(space_id)
            
            if result["success"]:
                return Response(
                    json.dumps({
                        "status": "success",
                        "message": result["message"]
                    }),
                    headers={"Content-Type": "application/json"}
                )
            else:
                return Response(
                    json.dumps({"status": "error", "message": result["error"]}),
                    status=400,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                headers={"Content-Type": "application/json"}
            )
    
    async def serve_web_interface(self):
        """Serve the main web interface with barcode scanning"""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Check-in System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Helvetica, Arial, sans-serif;
            background: #1a5f3f;
            min-height: 100vh;
            color: #000;
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: normal;
            margin-bottom: 8px;
            letter-spacing: 0;
        }
        
        .header p {
            font-size: 1.1rem;
            font-weight: normal;
        }
        
        .card {
            background: white;
            padding: 32px;
            margin-bottom: 30px;
            border: 1px solid #ddd;
        }
        
        .card h2 {
            color: #000;
            margin-bottom: 24px;
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .scanner-section {
            text-align: center;
        }
        
        #video {
            width: 100%;
            max-width: 400px;
            margin: 20px 0;
            border: 1px solid #ddd;
        }
        
        .controls {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin: 24px 0;
        }
        
        button {
            background: #2d7a54;
            color: white;
            border: none;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            font-family: Helvetica, Arial, sans-serif;
            transition: all 0.3s ease;
        }
        
        button:hover {
            background: #1a5f3f;
        }
        
        button:disabled {
            background: #999;
            cursor: not-allowed;
        }
        
        .manual-entry {
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #000;
        }
        
        input, select {
            width: 100%;
            max-width: 300px;
            padding: 16px;
            border: 1px solid #000;
            font-size: 16px;
            font-family: Helvetica, Arial, sans-serif;
        }
        
        input:focus, select:focus {
            outline: 2px solid #2d7a54;
            outline-offset: 0;
        }
        
        .status {
            margin: 20px 0;
            padding: 16px;
            font-weight: bold;
            text-align: center;
            border: 1px solid #ddd;
        }
        
        .status.success {
            background: #d1fae5;
            color: #000;
            border: 1px solid #a7f3d0;
        }
        
        .status.error {
            background: #fee2e2;
            color: #000;
            border: 1px solid #fecaca;
        }
        
        .status.info {
            background: #e0f2fe;
            color: #000;
            border: 1px solid #bae6fd;
        }
        
        .current-checkins {
            margin-top: 40px;
        }
        
        .checkin-item {
            background: #f8faf9;
            padding: 20px;
            margin: 12px 0;
            border-left: 4px solid #2d7a54;
        }
        
        .hidden {
            display: none;
        }
        
        .space-management-item {
            background: #f8faf9;
            padding: 20px;
            margin: 12px 0;
            border-left: 4px solid #2d7a54;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .space-info {
            flex-grow: 1;
        }
        
        .space-title {
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 4px;
        }
        
        .space-desc {
            color: #666;
            font-size: 0.9rem;
        }
        
        .space-actions {
            display: flex;
            gap: 8px;
        }
        
        .space-actions button {
            padding: 8px 16px;
            font-size: 14px;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 15% auto;
            padding: 32px;
            border: 1px solid #ddd;
            width: 80%;
            max-width: 500px;
        }
        
        .modal h3 {
            margin-bottom: 20px;
            color: #000;
        }
        
        .modal input, .modal textarea {
            width: 100%;
            padding: 12px;
            margin-bottom: 16px;
            border: 1px solid #000;
            font-family: Helvetica, Arial, sans-serif;
        }
        
        .modal textarea {
            height: 80px;
            resize: vertical;
        }
        
        .modal-buttons {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        
        .modal-buttons button {
            padding: 12px 24px;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 15px;
            }
            
            .controls {
                flex-direction: column;
                align-items: center;
            }
            
            button {
                width: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Student Check-in System</h1>
            <p>Scan your student ID or enter your student number</p>
        </div>
        
        <div class="card scanner-section">
            <h2>Barcode Scanner</h2>
            <video id="video" class="hidden"></video>
            <canvas id="canvas" class="hidden"></canvas>
            
            <div class="controls">
                <button id="startScanner">Start Scanner</button>
                <button id="stopScanner" disabled>Stop Scanner</button>
            </div>
            
            <div id="scanResult" class="status info hidden">
                Ready to scan - point camera at barcode
            </div>
        </div>
        
        <div class="card manual-entry">
            <h2>Manual Entry</h2>
            
            <div class="form-group">
                <label for="studentNumber">Student Number:</label>
                <input type="text" id="studentNumber" placeholder="Enter student number (e.g. 12345)">
            </div>
            
            <div class="form-group">
                <label for="spaceSelect">Space:</label>
                <div style="display: flex; gap: 10px; align-items: center; justify-content: center;">
                    <select id="spaceSelect">
                        <option value="">Loading spaces...</option>
                    </select>
                    <button type="button" id="clearSpaceBtn" style="padding: 8px 12px; font-size: 14px;">Clear</button>
                </div>
            </div>
            
            <div class="controls">
                <button id="checkinBtn">Check In</button>
                <button id="checkoutBtn">Check Out</button>
            </div>
            
            <div id="manualResult" class="status info hidden">
                Enter student number and select space
            </div>
        </div>
        
        <div class="card current-checkins">
            <h2>Current Check-ins</h2>
            <div id="currentCheckins">
                <div class="status info">Loading current check-ins...</div>
            </div>
            <button id="refreshBtn">Refresh Status</button>
        </div>
    </div>

    <!-- Space Management Modal -->
    <div id="spaceModal" class="modal">
        <div class="modal-content">
            <h3 id="modalTitle">Add New Space</h3>
            <input type="text" id="spaceName" placeholder="Space name (e.g., Library Study Hall)">
            <textarea id="spaceDescription" placeholder="Description (optional)"></textarea>
            <div class="modal-buttons">
                <button id="cancelSpaceBtn">Cancel</button>
                <button id="saveSpaceBtn">Save</button>
            </div>
        </div>
    </div>

    <!-- Include QuaggaJS for barcode scanning -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
    
    <script>
        class StudentCheckinApp {
            constructor() {
                this.isScanning = false;
                this.spaces = [];
                this.init();
            }
            
            async init() {
                this.setupEventListeners();
                await this.loadSpaces();
                await this.loadCurrentCheckins();
            }
            
            setupEventListeners() {
                document.getElementById('startScanner').addEventListener('click', () => this.startScanner());
                document.getElementById('stopScanner').addEventListener('click', () => this.stopScanner());
                document.getElementById('checkinBtn').addEventListener('click', () => this.manualCheckin());
                document.getElementById('checkoutBtn').addEventListener('click', () => this.manualCheckout());
                document.getElementById('refreshBtn').addEventListener('click', () => this.loadCurrentCheckins());
                document.getElementById('clearSpaceBtn').addEventListener('click', () => this.clearSpace());
                
                // Enter key support for student number input
                document.getElementById('studentNumber').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.manualCheckin();
                    }
                });
            }
            
            async loadSpaces() {
                try {
                    const response = await fetch('/spaces');
                    const data = await response.json();
                    this.spaces = data.spaces || [];
                    
                    const select = document.getElementById('spaceSelect');
                    select.innerHTML = '<option value="">Select a space...</option>';
                    
                    this.spaces.forEach(space => {
                        const option = document.createElement('option');
                        option.value = space.space_id;
                        option.textContent = space.space_name;
                        select.appendChild(option);
                    });
                } catch (error) {
                    console.error('Failed to load spaces:', error);
                    this.showStatus('manualResult', 'Failed to load spaces', 'error');
                }
            }
            
            async loadCurrentCheckins() {
                try {
                    const response = await fetch('/current-checkins');
                    const data = await response.json();
                    const checkins = data.current_checkins || [];
                    
                    const container = document.getElementById('currentCheckins');
                    
                    if (checkins.length === 0) {
                        container.innerHTML = '<div class="status info">No students currently checked in</div>';
                    } else {
                        container.innerHTML = checkins.map(checkin => `
                            <div class="checkin-item">
                                <strong>${checkin.encrypted_name}</strong> (#${checkin.student_number})${checkin.grade ? ` - Grade ${checkin.grade}` : ''}<br>
                                Location: ${checkin.space_name}<br>
                                Since: ${new Date(checkin.time_in).toLocaleTimeString()}
                            </div>
                        `).join('');
                    }
                } catch (error) {
                    console.error('Failed to load current check-ins:', error);
                    document.getElementById('currentCheckins').innerHTML = 
                        '<div class="status error">Failed to load current check-ins</div>';
                }
            }
            
            async startScanner() {
                try {
                    const video = document.getElementById('video');
                    const scanResult = document.getElementById('scanResult');
                    
                    video.classList.remove('hidden');
                    scanResult.classList.remove('hidden');
                    this.showStatus('scanResult', 'Starting camera...', 'info');
                    
                    await Quagga.init({
                        inputStream: {
                            name: "Live",
                            type: "LiveStream",
                            target: video,
                            constraints: {
                                width: 400,
                                height: 300,
                                facingMode: "environment"
                            }
                        },
                        decoder: {
                            readers: ["code_128_reader", "code_39_reader", "ean_reader", "ean_8_reader"]
                        }
                    });
                    
                    Quagga.start();
                    this.isScanning = true;
                    
                    document.getElementById('startScanner').disabled = true;
                    document.getElementById('stopScanner').disabled = false;
                    
                    this.showStatus('scanResult', 'Camera ready - point at barcode to scan', 'info');
                    
                    Quagga.onDetected((data) => {
                        const code = data.codeResult.code;
                        this.showStatus('scanResult', `Scanned: ${code}`, 'success');
                        this.processScannedCode(code);
                    });
                    
                } catch (error) {
                    console.error('Scanner error:', error);
                    this.showStatus('scanResult', 'Failed to start camera. Please check permissions.', 'error');
                }
            }
            
            stopScanner() {
                if (this.isScanning) {
                    Quagga.stop();
                    this.isScanning = false;
                    
                    document.getElementById('video').classList.add('hidden');
                    document.getElementById('scanResult').classList.add('hidden');
                    document.getElementById('startScanner').disabled = false;
                    document.getElementById('stopScanner').disabled = true;
                }
            }
            
            processScannedCode(code) {
                // Auto-fill the student number field
                document.getElementById('studentNumber').value = code;
                this.showStatus('scanResult', `Student number ${code} detected - ready to check in`, 'success');
                
                // Check if space is already selected
                const spaceSelect = document.getElementById('spaceSelect');
                if (spaceSelect.value) {
                    // Space already selected, ready to check in
                    this.showStatus('manualResult', `Ready to check in student ${code}`, 'info');
                } else {
                    // No space selected, prompt user to select
                    this.showStatus('manualResult', 'Select a space to complete check-in', 'info');
                    spaceSelect.focus();
                }
            }
            
            async manualCheckin() {
                const studentNumber = document.getElementById('studentNumber').value.trim();
                const spaceId = document.getElementById('spaceSelect').value;
                
                if (!studentNumber || !spaceId) {
                    this.showStatus('manualResult', 'Please enter student number and select a space', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`/checkin-${studentNumber}-${spaceId}`);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        // Show different messages based on action type
                        if (data.action === 'moved') {
                            this.showStatus('manualResult', 
                                `${data.message} (automatically checked out of previous location)`, 
                                'success');
                        } else {
                            this.showStatus('manualResult', data.message, 'success');
                        }
                        
                        // Clear student number but keep space selected
                        document.getElementById('studentNumber').value = '';
                        
                        // Focus back to student number for next entry
                        document.getElementById('studentNumber').focus();
                        
                        await this.loadCurrentCheckins();
                    } else {
                        this.showStatus('manualResult', data.message, 'error');
                    }
                } catch (error) {
                    this.showStatus('manualResult', 'Check-in failed. Please try again.', 'error');
                }
            }
            
            async manualCheckout() {
                const studentNumber = document.getElementById('studentNumber').value.trim();
                const spaceId = document.getElementById('spaceSelect').value;
                
                if (!studentNumber || !spaceId) {
                    this.showStatus('manualResult', 'Please enter student number and select a space', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`/checkout-${studentNumber}-${spaceId}`);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.showStatus('manualResult', data.message, 'success');
                        
                        // Clear student number but keep space selected
                        document.getElementById('studentNumber').value = '';
                        
                        // Focus back to student number for next entry
                        document.getElementById('studentNumber').focus();
                        
                        await this.loadCurrentCheckins();
                    } else {
                        this.showStatus('manualResult', data.message, 'error');
                    }
                } catch (error) {
                    this.showStatus('manualResult', 'Check-out failed. Please try again.', 'error');
                }
            }
            
            clearSpace() {
                document.getElementById('spaceSelect').value = '';
                this.showStatus('manualResult', 'Space cleared - select a new space', 'info');
            }
            
            showStatus(elementId, message, type) {
                const element = document.getElementById(elementId);
                element.textContent = message;
                element.className = `status ${type}`;
                element.classList.remove('hidden');
            }
        }
        
        // Initialize the app when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new StudentCheckinApp();
        });
    </script>
</body>
</html>"""
        
        return Response(
            html_content,
            headers={"Content-Type": "text/html"}
        )
    
    async def serve_admin_dashboard(self):
        """Serve the admin dashboard for monitoring and search"""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Student Check-in System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Helvetica, Arial, sans-serif;
            background: #1a5f3f;
            min-height: 100vh;
            color: #000;
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: normal;
            margin-bottom: 8px;
            letter-spacing: 0;
        }
        
        .header p {
            font-size: 1.1rem;
            font-weight: normal;
        }
        
        .nav-links {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            margin: 0 20px;
            padding: 12px 24px;
            border: 1px solid white;
            display: inline-block;
            font-weight: normal;
            transition: all 0.3s ease;
        }
        
        .nav-links a:hover {
            background: white;
            color: #1a5f3f;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            padding: 32px;
            box-shadow: none;
            border: 1px solid #ddd;
        }
        
        .card h2 {
            color: #000;
            margin-bottom: 24px;
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .search-section {
            text-align: center;
        }
        
        .search-box {
            width: 100%;
            max-width: 400px;
            padding: 16px;
            border: 1px solid #000;
            font-size: 16px;
            margin-bottom: 20px;
            font-family: Helvetica, Arial, sans-serif;
        }
        
        .search-box:focus {
            outline: 2px solid #2d7a54;
            outline-offset: 0;
        }
        
        .search-results {
            margin-top: 20px;
        }
        
        .space-card {
            background: #f8faf9;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #2d7a54;
        }
        
        .space-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .space-name {
            font-weight: bold;
            font-size: 1.25rem;
            color: #000;
        }
        
        .occupancy-badge {
            background: #2d7a54;
            color: white;
            padding: 6px 16px;
            font-size: 0.875rem;
            font-weight: bold;
        }
        
        .occupancy-badge.empty {
            background: #999;
        }
        
        .occupancy-badge.low {
            background: #059669;
        }
        
        .occupancy-badge.medium {
            background: #d97706;
        }
        
        .occupancy-badge.high {
            background: #dc2626;
        }
        
        .student-list {
            margin-top: 16px;
        }
        
        .student-item {
            background: white;
            padding: 16px;
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid #ddd;
        }
        
        .student-info {
            flex-grow: 1;
        }
        
        .student-name {
            font-weight: bold;
            color: #000;
            margin-bottom: 4px;
        }
        
        .student-details {
            font-size: 0.875rem;
            color: #000;
        }
        
        .time-badge {
            background: #f3f4f6;
            color: #000;
            padding: 4px 12px;
            font-size: 0.75rem;
            font-weight: normal;
        }
        
        .controls {
            display: flex;
            gap: 12px;
            justify-content: center;
            flex-wrap: wrap;
            margin: 24px 0;
        }
        
        button {
            background: #2d7a54;
            color: white;
            border: none;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            font-family: Helvetica, Arial, sans-serif;
            transition: all 0.3s ease;
        }
        
        button:hover {
            background: #1a5f3f;
        }
        
        button:disabled {
            background: #999;
            cursor: not-allowed;
        }
        
        button.danger {
            background: #dc2626;
        }
        
        button.danger:hover {
            background: #b91c1c;
        }
        
        .status {
            margin: 20px 0;
            padding: 16px;
            font-weight: bold;
            text-align: center;
            border: 1px solid #ddd;
        }
        
        .status.success {
            background: #d1fae5;
            color: #000;
            border: 1px solid #a7f3d0;
        }
        
        .status.error {
            background: #fee2e2;
            color: #000;
            border: 1px solid #fecaca;
        }
        
        .status.info {
            background: #e0f2fe;
            color: #000;
            border: 1px solid #bae6fd;
        }
        
        .hidden {
            display: none;
        }
        
        .stats-summary {
            background: #2d7a54;
            color: white;
            padding: 32px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .stats-summary h2 {
            color: white;
            margin-bottom: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 24px;
            margin-top: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            display: block;
            margin-bottom: 4px;
        }
        
        .stat-label {
            font-size: 0.875rem;
            font-weight: normal;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 15px;
            }
            
            .controls {
                flex-direction: column;
                align-items: center;
            }
            
            button {
                width: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Admin Dashboard</h1>
            <p>Monitor spaces and manage student check-ins</p>
        </div>
        
        <div class="nav-links">
            <a href="/web">Student Interface</a>
            <a href="/admin">Admin Dashboard</a>
            <a href="/">API Endpoints</a>
        </div>
        
        <div class="stats-summary">
            <h2>System Overview</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <span id="totalStudents" class="stat-number">-</span>
                    <span class="stat-label">Total Students</span>
                </div>
                <div class="stat-item">
                    <span id="activeCheckins" class="stat-number">-</span>
                    <span class="stat-label">Currently Checked In</span>
                </div>
                <div class="stat-item">
                    <span id="totalSpaces" class="stat-number">-</span>
                    <span class="stat-label">Available Spaces</span>
                </div>
                <div class="stat-item">
                    <span id="occupiedSpaces" class="stat-number">-</span>
                    <span class="stat-label">Occupied Spaces</span>
                </div>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card search-section">
                <h2>Student Search</h2>
                <input type="text" id="searchBox" class="search-box" placeholder="Search by name or student number...">
                <button id="searchBtn">Search</button>
                <button id="clearSearchBtn">Clear</button>
                
                <div id="searchResults" class="search-results">
                    <div class="status info">Enter a student name or number to search</div>
                </div>
            </div>
            
            <div class="card">
                <h2>Admin Controls</h2>
                <div class="controls">
                    <button id="refreshBtn">Refresh Data</button>
                    <button id="exportBtn">Export CSV</button>
                    <button id="bulkCheckoutBtn" class="danger">Check Out All</button>
                </div>
                
                <div id="adminStatus" class="status info hidden">
                    Admin actions will appear here
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Space Management</h2>
            <div class="controls">
                <button id="addSpaceBtn">Add New Space</button>
                <button id="refreshSpacesBtn">Refresh Spaces</button>
            </div>
            
            <div id="spaceManagement">
                <div class="status info">Loading spaces...</div>
            </div>
            
            <div id="spaceStatus" class="status info hidden">
                Space actions will appear here
            </div>
        </div>
        
        <div class="card">
            <h2>Space Occupancy</h2>
            <div id="spaceOccupancy">
                <div class="status info">Loading space data...</div>
            </div>
        </div>
    </div>

    <script>
        class AdminDashboard {
            constructor() {
                this.refreshInterval = null;
                this.currentEditingSpaceId = null;
                this.init();
            }
            
            async init() {
                this.setupEventListeners();
                await this.loadAllData();
                this.startAutoRefresh();
            }
            
            setupEventListeners() {
                document.getElementById('searchBtn').addEventListener('click', () => this.performSearch());
                document.getElementById('clearSearchBtn').addEventListener('click', () => this.clearSearch());
                document.getElementById('refreshBtn').addEventListener('click', () => this.loadAllData());
                document.getElementById('exportBtn').addEventListener('click', () => this.exportData());
                document.getElementById('bulkCheckoutBtn').addEventListener('click', () => this.bulkCheckout());
                
                // Space management
                document.getElementById('addSpaceBtn').addEventListener('click', () => this.showAddSpaceModal());
                document.getElementById('refreshSpacesBtn').addEventListener('click', () => this.loadSpaceManagement());
                document.getElementById('cancelSpaceBtn').addEventListener('click', () => this.hideSpaceModal());
                document.getElementById('saveSpaceBtn').addEventListener('click', () => this.saveSpace());
                
                // Enter key support for search
                document.getElementById('searchBox').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.performSearch();
                    }
                });
                
                // Real-time search as user types
                document.getElementById('searchBox').addEventListener('input', () => {
                    clearTimeout(this.searchTimeout);
                    this.searchTimeout = setTimeout(() => {
                        const query = document.getElementById('searchBox').value.trim();
                        if (query.length >= 2) {
                            this.performSearch();
                        } else if (query.length === 0) {
                            this.clearSearch();
                        }
                    }, 300);
                });
                
                // Modal click outside to close
                document.getElementById('spaceModal').addEventListener('click', (e) => {
                    if (e.target === document.getElementById('spaceModal')) {
                        this.hideSpaceModal();
                    }
                });
            }
            
            async loadAllData() {
                await Promise.all([
                    this.loadStats(),
                    this.loadSpaceOccupancy(),
                    this.loadSpaceManagement()
                ]);
            }
            
            async loadStats() {
                try {
                    const [studentsResponse, checkinsResponse, spacesResponse] = await Promise.all([
                        fetch('/students'),
                        fetch('/current-checkins'),
                        fetch('/spaces')
                    ]);
                    
                    const studentsData = await studentsResponse.json();
                    const checkinsData = await checkinsResponse.json();
                    const spacesData = await spacesResponse.json();
                    
                    const totalStudents = studentsData.students?.length || 0;
                    const activeCheckins = checkinsData.current_checkins?.length || 0;
                    const totalSpaces = spacesData.spaces?.length || 0;
                    
                    // Count occupied spaces
                    const occupiedSpaces = new Set(
                        checkinsData.current_checkins?.map(checkin => checkin.space_id) || []
                    ).size;
                    
                    document.getElementById('totalStudents').textContent = totalStudents;
                    document.getElementById('activeCheckins').textContent = activeCheckins;
                    document.getElementById('totalSpaces').textContent = totalSpaces;
                    document.getElementById('occupiedSpaces').textContent = occupiedSpaces;
                    
                } catch (error) {
                    console.error('Failed to load stats:', error);
                }
            }
            
            async loadSpaceOccupancy() {
                try {
                    const [spacesResponse, checkinsResponse] = await Promise.all([
                        fetch('/spaces'),
                        fetch('/current-checkins')
                    ]);
                    
                    const spacesData = await spacesResponse.json();
                    const checkinsData = await checkinsResponse.json();
                    
                    const spaces = spacesData.spaces || [];
                    const checkins = checkinsData.current_checkins || [];
                    
                    // Group checkins by space
                    const checkinsBySpace = {};
                    checkins.forEach(checkin => {
                        if (!checkinsBySpace[checkin.space_id]) {
                            checkinsBySpace[checkin.space_id] = [];
                        }
                        checkinsBySpace[checkin.space_id].push(checkin);
                    });
                    
                    const container = document.getElementById('spaceOccupancy');
                    
                    if (spaces.length === 0) {
                        container.innerHTML = '<div class="status info">No spaces configured</div>';
                        return;
                    }
                    
                    container.innerHTML = spaces.map(space => {
                        const spaceCheckins = checkinsBySpace[space.space_id] || [];
                        const count = spaceCheckins.length;
                        
                        let badgeClass = 'empty';
                        if (count > 0) badgeClass = 'low';
                        if (count > 5) badgeClass = 'medium';
                        if (count > 10) badgeClass = 'high';
                        
                        const studentsList = spaceCheckins.length > 0 
                            ? spaceCheckins.map(checkin => `
                                <div class="student-item">
                                    <div class="student-info">
                                        <div class="student-name">${checkin.encrypted_name}</div>
                                        <div class="student-details">#${checkin.student_number}${checkin.grade ? ` - Grade ${checkin.grade}` : ''}</div>
                                    </div>
                                    <div class="time-badge">
                                        ${new Date(checkin.time_in).toLocaleTimeString()}
                                    </div>
                                </div>
                            `).join('')
                            : '<div class="status info">No students currently checked in</div>';
                        
                        return `
                            <div class="space-card">
                                <div class="space-header">
                                    <div class="space-name">${space.space_name}</div>
                                    <div class="occupancy-badge ${badgeClass}">
                                        ${count} student${count !== 1 ? 's' : ''}
                                    </div>
                                </div>
                                <div class="student-list">
                                    ${studentsList}
                                </div>
                            </div>
                        `;
                    }).join('');
                    
                } catch (error) {
                    console.error('Failed to load space occupancy:', error);
                    document.getElementById('spaceOccupancy').innerHTML = 
                        '<div class="status error">Failed to load space data</div>';
                }
            }
            
            async performSearch() {
                const query = document.getElementById('searchBox').value.trim();
                
                if (!query) {
                    this.showSearchStatus('Please enter a search term', 'error');
                    return;
                }
                
                try {
                    const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.displaySearchResults(data.results);
                    } else {
                        this.showSearchStatus(data.message, 'error');
                    }
                } catch (error) {
                    console.error('Search error:', error);
                    this.showSearchStatus('Search failed. Please try again.', 'error');
                }
            }
            
            displaySearchResults(results) {
                const container = document.getElementById('searchResults');
                
                if (results.length === 0) {
                    container.innerHTML = '<div class="status info">No students found</div>';
                    return;
                }
                
                container.innerHTML = results.map(result => {
                    const locationInfo = result.current_location 
                        ? `Currently in: <strong>${result.current_location}</strong><br>Since: ${new Date(result.check_in_time).toLocaleString()}`
                        : 'Not currently checked in';
                        
                    return `
                        <div class="student-item">
                            <div class="student-info">
                                <div class="student-name">${result.student.encrypted_name}</div>
                                <div class="student-details">
                                    #${result.student.student_number}<br>
                                    ${locationInfo}
                                </div>
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            clearSearch() {
                document.getElementById('searchBox').value = '';
                document.getElementById('searchResults').innerHTML = 
                    '<div class="status info">Enter a student name or number to search</div>';
            }
            
            showSearchStatus(message, type) {
                document.getElementById('searchResults').innerHTML = 
                    `<div class="status ${type}">${message}</div>`;
            }
            
            async exportData() {
                try {
                    const response = await fetch('/current-checkins');
                    const data = await response.json();
                    const checkins = data.current_checkins || [];
                    
                    if (checkins.length === 0) {
                        this.showAdminStatus('No data to export', 'info');
                        return;
                    }
                    
                    // Create CSV content
                    const headers = ['Student Name', 'Student Number', 'Space', 'Check-in Time'];
                    const csvContent = [
                        headers.join(','),
                        ...checkins.map(checkin => [
                            `"${checkin.encrypted_name}"`,
                            checkin.student_number,
                            `"${checkin.space_name}"`,
                            `"${new Date(checkin.time_in).toLocaleString()}"`
                        ].join(','))
                    ].join('\\n');
                    
                    // Download CSV
                    const blob = new Blob([csvContent], { type: 'text/csv' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `checkins-${new Date().toISOString().split('T')[0]}.csv`;
                    a.click();
                    window.URL.revokeObjectURL(url);
                    
                    this.showAdminStatus(`Exported ${checkins.length} records`, 'success');
                } catch (error) {
                    this.showAdminStatus('Export failed', 'error');
                }
            }
            
            async bulkCheckout() {
                if (!confirm('Are you sure you want to check out ALL students? This cannot be undone.')) {
                    return;
                }
                
                try {
                    const response = await fetch('/bulk-checkout', { method: 'POST' });
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        this.showAdminStatus(`${data.checked_out_count} students checked out`, 'success');
                        await this.loadAllData();
                    } else {
                        this.showAdminStatus(data.message, 'error');
                    }
                } catch (error) {
                    this.showAdminStatus('Bulk checkout failed', 'error');
                }
            }
            
            showAdminStatus(message, type) {
                const element = document.getElementById('adminStatus');
                element.textContent = message;
                element.className = `status ${type}`;
                element.classList.remove('hidden');
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    element.classList.add('hidden');
                }, 5000);
            }
            
            startAutoRefresh() {
                // Refresh data every 30 seconds
                this.refreshInterval = setInterval(() => {
                    this.loadAllData();
                }, 30000);
            }
            
            stopAutoRefresh() {
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                    this.refreshInterval = null;
                }
            }
        }
        
        // Initialize the dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            window.adminDashboard = new AdminDashboard();
        });
        
        // Clean up when page unloads
        window.addEventListener('beforeunload', () => {
            if (window.adminDashboard) {
                window.adminDashboard.stopAutoRefresh();
            }
        });
    </script>
</body>
</html>"""
        
        return Response(
            html_content,
            headers={"Content-Type": "text/html"}
        )
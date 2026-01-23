"""
PostgreSQL Database Manager for Career Agent System
Handles all database operations for persistent storage
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os


class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations
    """
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 user: str = None,
                 password: str = None):
        """
        Initialize database connection pool
        
        Args:
            host: Database host (default: localhost)
            port: Database port (default: 5432)
            database: Database name
            user: Database user
            password: Database password
            
        You can also set environment variables:
            DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
        """
        
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", 5432))
        self.database = database or os.getenv("DB_NAME", "career_agent")
        self.user = user or os.getenv("DB_USER", "abdullah")
        self.password = password or os.getenv("DB_PASSWORD", "")
        
        # Create connection pool
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {e}")
    
    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections"""
        self.pool.closeall()
    
    # ========== USER MANAGEMENT ==========
    
    def create_user(self, user_id: str, user_name: str = None) -> str:
        """
        Create a new user if they don't exist
        
        Args:
            user_id: UUID for the user
            user_name: Optional name for the user
            
        Returns:
            user_id
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if user exists
                cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                if cur.fetchone():
                    return user_id
                
                # Create user if doesn't exist
                cur.execute("""
                    INSERT INTO users (user_id, created_at)
                    VALUES (%s, NOW())
                    ON CONFLICT (user_id) DO NOTHING
                """, (user_id,))
                conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            # User might already exist, which is fine
            return user_id
        finally:
            self.return_connection(conn)
    
    # ========== JOURNEY MANAGEMENT ==========
    
    def create_journey(self,
                      user_id: str,
                      desired_role: str,
                      target_role: str,
                      student_profile: Dict,
                      market_snapshot: Dict,
                      roadmap: List[Dict],
                      feasibility_verdict: str = None) -> str:
        """
        Create a new learning journey
        
        Returns:
            session_id (UUID as string)
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO journeys (
                        user_id, desired_role, target_role,
                        student_profile, market_snapshot, roadmap,
                        total_steps, feasibility_verdict,
                        start_date, last_activity
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING session_id
                """, (
                    user_id,
                    desired_role,
                    target_role,
                    Json(student_profile),
                    Json(market_snapshot),
                    Json(roadmap),
                    len(roadmap),
                    feasibility_verdict,
                    datetime.now(),
                    datetime.now()
                ))
                
                result = cur.fetchone()
                session_id = str(result['session_id'])
                
                # Create step_progress entries for all steps
                for i, step in enumerate(roadmap, start=1):
                    cur.execute("""
                        INSERT INTO step_progress (session_id, step_number, status)
                        VALUES (%s, %s, %s)
                    """, (session_id, i, 'not_started'))
                
                # Log activity
                self._log_activity(cur, session_id, user_id, "journey_started", {
                    "target_role": target_role,
                    "total_steps": len(roadmap)
                })
                
                conn.commit()
                return session_id
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to create journey: {e}")
        finally:
            self.return_connection(conn)
    
    def get_journey(self, session_id: str) -> Optional[Dict]:
        """Get journey details by session_id"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM journeys WHERE session_id = %s
                """, (session_id,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
        finally:
            self.return_connection(conn)
    
    def update_journey_status(self, session_id: str, status: str):
        """Update journey status (active, paused, completed, abandoned)"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE journeys
                    SET status = %s, last_activity = %s
                    WHERE session_id = %s
                """, (status, datetime.now(), session_id))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    def get_user_journeys(self, user_id: str, status: str = None) -> List[Dict]:
        """Get all journeys for a user"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if status:
                    cur.execute("""
                        SELECT * FROM journeys
                        WHERE user_id = %s AND status = %s
                        ORDER BY last_activity DESC
                    """, (user_id, status))
                else:
                    cur.execute("""
                        SELECT * FROM journeys
                        WHERE user_id = %s
                        ORDER BY last_activity DESC
                    """, (user_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ========== STEP PROGRESS ==========
    
    def record_step_completion(self,
                              session_id: str,
                              step_number: int,
                              time_spent_hours: float = None):
        """Mark a step as completed"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Update step status
                cur.execute("""
                    UPDATE step_progress
                    SET status = 'completed',
                        completed_at = %s,
                        time_spent_hours = COALESCE(time_spent_hours, 0) + COALESCE(%s, 0)
                    WHERE session_id = %s AND step_number = %s
                    RETURNING *
                """, (datetime.now(), time_spent_hours, session_id, step_number))
                
                # Update journey
                cur.execute("""
                    UPDATE journeys
                    SET current_step = %s,
                        completed_steps = array_append(completed_steps, %s),
                        last_activity = %s
                    WHERE session_id = %s
                """, (step_number + 1, step_number, datetime.now(), session_id))
                
                # Log activity
                self._log_activity(cur, session_id, None, "step_completed", {
                    "step_number": step_number,
                    "time_spent": time_spent_hours
                })
                
                conn.commit()
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to record step completion: {e}")
        finally:
            self.return_connection(conn)
    
    def get_step_progress(self, session_id: str) -> List[Dict]:
        """Get progress for all steps in a journey"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM step_progress
                    WHERE session_id = %s
                    ORDER BY step_number
                """, (session_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ========== BLOCKERS ==========
    
    def record_blocker(self,
                      session_id: str,
                      step_number: int,
                      reason: str,
                      category: str = None,
                      alternate_paths: List[Dict] = None) -> int:
        """Record a blocker on a step"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if blocker already exists for this step
                cur.execute("""
                    SELECT id, attempts FROM blockers
                    WHERE session_id = %s AND step_number = %s AND resolved = FALSE
                """, (session_id, step_number))
                
                existing = cur.fetchone()
                
                if existing:
                    # Update existing blocker
                    cur.execute("""
                        UPDATE blockers
                        SET attempts = attempts + 1,
                            last_reported = %s,
                            reason = %s,
                            alternate_paths = COALESCE(%s, alternate_paths)
                        WHERE id = %s
                        RETURNING id
                    """, (datetime.now(), reason, Json(alternate_paths) if alternate_paths else None, existing['id']))
                    blocker_id = cur.fetchone()['id']
                else:
                    # Create new blocker
                    cur.execute("""
                        INSERT INTO blockers (
                            session_id, step_number, reason, category,
                            alternate_paths, first_reported, last_reported
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        session_id, step_number, reason, category,
                        Json(alternate_paths) if alternate_paths else None,
                        datetime.now(), datetime.now()
                    ))
                    blocker_id = cur.fetchone()['id']
                
                # Update step status to blocked
                cur.execute("""
                    UPDATE step_progress
                    SET status = 'blocked'
                    WHERE session_id = %s AND step_number = %s
                """, (session_id, step_number))
                
                # Update journey motivation
                cur.execute("""
                    UPDATE journeys
                    SET motivation_level = GREATEST(motivation_level - 0.2, 0.1),
                        last_activity = %s
                    WHERE session_id = %s
                """, (datetime.now(), session_id))
                
                # Log activity
                self._log_activity(cur, session_id, None, "blocker_reported", {
                    "step_number": step_number,
                    "reason": reason,
                    "blocker_id": blocker_id
                })
                
                conn.commit()
                return blocker_id
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to record blocker: {e}")
        finally:
            self.return_connection(conn)
    
    def get_active_blockers(self, session_id: str) -> List[Dict]:
        """Get all unresolved blockers for a journey"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blockers
                    WHERE session_id = %s AND resolved = FALSE
                    ORDER BY last_reported DESC
                """, (session_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    def get_blocker(self, blocker_id: int) -> Optional[Dict]:
        """Get a specific blocker by ID"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blockers WHERE id = %s
                """, (blocker_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            self.return_connection(conn)
    
    def get_blocker_by_step(self, session_id: str, step_number: int) -> Optional[Dict]:
        """Get blocker for a specific step"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM blockers
                    WHERE session_id = %s AND step_number = %s AND resolved = FALSE
                    ORDER BY last_reported DESC
                    LIMIT 1
                """, (session_id, step_number))
                result = cur.fetchone()
                return dict(result) if result else None
        finally:
            self.return_connection(conn)
    
    def update_blocker_alternate_paths(self, blocker_id: int, alternate_paths: List[Dict]):
        """Update alternate paths for a blocker"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE blockers
                    SET alternate_paths = %s
                    WHERE id = %s
                """, (Json(alternate_paths), blocker_id))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    def resolve_blocker(self, blocker_id: int, resolution_note: str = None):
        """Mark a blocker as resolved"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE blockers
                    SET resolved = TRUE,
                        resolved_at = %s,
                        resolution_note = %s
                    WHERE id = %s
                """, (datetime.now(), resolution_note, blocker_id))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    # ========== RE-EVALUATIONS ==========
    
    def create_reevaluation(self,
                           session_id: str,
                           trigger_type: str,
                           trigger_severity: str,
                           trigger_details: Dict,
                           action_taken: str,
                           market_comparison: Dict = None,
                           alternatives_suggested: List[Dict] = None) -> int:
        """
        Record a re-evaluation event
        
        Returns:
            reevaluation_id
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO reevaluations (
                        session_id, trigger_type, trigger_severity,
                        trigger_details, action_taken,
                        market_comparison, alternatives_suggested
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    session_id,
                    trigger_type,
                    trigger_severity,
                    Json(trigger_details),
                    action_taken,
                    Json(market_comparison) if market_comparison else None,
                    Json(alternatives_suggested) if alternatives_suggested else None
                ))
                
                reevaluation_id = cur.fetchone()['id']
                
                # Log activity
                self._log_activity(cur, session_id, None, "reevaluation_triggered", {
                    "trigger_type": trigger_type,
                    "action": action_taken,
                    "reevaluation_id": reevaluation_id
                })
                
                conn.commit()
                return reevaluation_id
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to create re-evaluation: {e}")
        finally:
            self.return_connection(conn)
    
    def update_reevaluation_decision(self,
                                    reevaluation_id: int,
                                    student_decision: str):
        """Update with student's decision after re-evaluation"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE reevaluations
                    SET student_decision = %s,
                        decision_date = %s
                    WHERE id = %s
                """, (student_decision, datetime.now(), reevaluation_id))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    def get_reevaluations(self, session_id: str) -> List[Dict]:
        """Get all re-evaluations for a journey"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM reevaluations
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                """, (session_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ========== REROUTES ==========
    
    def create_reroute(self,
                      session_id: str,
                      from_role: str,
                      to_role: str,
                      reason_type: str,
                      reason_details: str,
                      new_roadmap: List[Dict],
                      new_market_snapshot: Dict = None) -> int:
        """
        Record a path reroute
        
        Returns:
            reroute_id
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Create reroute record
                cur.execute("""
                    INSERT INTO reroutes (
                        session_id, from_role, to_role,
                        reason_type, reason_details,
                        new_roadmap, new_market_snapshot,
                        reroute_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    session_id,
                    from_role,
                    to_role,
                    reason_type,
                    reason_details,
                    Json(new_roadmap),
                    Json(new_market_snapshot) if new_market_snapshot else None,
                    datetime.now()
                ))
                
                reroute_id = cur.fetchone()['id']
                
                # Update journey with new path
                cur.execute("""
                    UPDATE journeys
                    SET target_role = %s,
                        roadmap = %s,
                        market_snapshot = %s,
                        total_steps = %s,
                        current_step = 0,
                        completed_steps = '{}',
                        motivation_level = 1.0,
                        last_activity = %s
                    WHERE session_id = %s
                """, (
                    to_role,
                    Json(new_roadmap),
                    Json(new_market_snapshot) if new_market_snapshot else None,
                    len(new_roadmap),
                    datetime.now(),
                    session_id
                ))
                
                # Reset step progress
                cur.execute("""
                    DELETE FROM step_progress WHERE session_id = %s
                """, (session_id,))
                
                for i in range(1, len(new_roadmap) + 1):
                    cur.execute("""
                        INSERT INTO step_progress (session_id, step_number, status)
                        VALUES (%s, %s, 'not_started')
                    """, (session_id, i))
                
                # Log activity
                self._log_activity(cur, session_id, None, "path_rerouted", {
                    "from_role": from_role,
                    "to_role": to_role,
                    "reason": reason_type,
                    "reroute_id": reroute_id
                })
                
                conn.commit()
                return reroute_id
                
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to create reroute: {e}")
        finally:
            self.return_connection(conn)
    
    def get_reroutes(self, session_id: str) -> List[Dict]:
        """Get all reroutes for a journey"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM reroutes
                    WHERE session_id = %s
                    ORDER BY reroute_date DESC
                """, (session_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ========== SKILLS LEARNED ==========
    
    def add_skill_learned(self,
                         session_id: str,
                         skill_name: str,
                         proficiency_level: str,
                         learned_from_step: int = None,
                         project_proof: str = None):
        """Record a skill that student has learned"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO skills_learned (
                        session_id, skill_name, proficiency_level,
                        learned_from_step, project_proof,
                        learned_date
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id, skill_name)
                    DO UPDATE SET
                        proficiency_level = EXCLUDED.proficiency_level,
                        learned_date = EXCLUDED.learned_date
                """, (
                    session_id,
                    skill_name,
                    proficiency_level,
                    learned_from_step,
                    project_proof,
                    datetime.now()
                ))
                conn.commit()
        finally:
            self.return_connection(conn)
    
    def get_skills_learned(self, session_id: str) -> List[Dict]:
        """Get all skills learned in this journey"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM skills_learned
                    WHERE session_id = %s
                    ORDER BY learned_date DESC
                """, (session_id,))
                
                return [dict(row) for row in cur.fetchall()]
        finally:
            self.return_connection(conn)
    
    # ========== HELPER FUNCTIONS ==========
    
    def _log_activity(self, cursor, session_id, user_id, action, details):
        """Internal helper to log activities"""
        cursor.execute("""
            INSERT INTO activity_log (session_id, user_id, action, details)
            VALUES (%s, %s, %s, %s)
        """, (session_id, user_id, action, Json(details)))
    
    def get_journey_summary(self, session_id: str) -> Dict:
        """
        Get complete journey summary with all related data
        This is what you'd send to frontend
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get journey
                cur.execute("SELECT * FROM journeys WHERE session_id = %s", (session_id,))
                journey = dict(cur.fetchone())
                
                # Get step progress
                cur.execute("""
                    SELECT * FROM step_progress
                    WHERE session_id = %s
                    ORDER BY step_number
                """, (session_id,))
                steps = [dict(row) for row in cur.fetchall()]
                
                # Get active blockers
                cur.execute("""
                    SELECT * FROM blockers
                    WHERE session_id = %s AND resolved = FALSE
                """, (session_id,))
                blockers = [dict(row) for row in cur.fetchall()]
                
                # Get re-evaluations
                cur.execute("""
                    SELECT * FROM reevaluations
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """, (session_id,))
                reevaluations = [dict(row) for row in cur.fetchall()]
                
                # Get reroutes
                cur.execute("""
                    SELECT * FROM reroutes
                    WHERE session_id = %s
                    ORDER BY reroute_date DESC
                """, (session_id,))
                reroutes = [dict(row) for row in cur.fetchall()]
                
                # Get skills learned
                cur.execute("""
                    SELECT * FROM skills_learned
                    WHERE session_id = %s
                """, (session_id,))
                skills = [dict(row) for row in cur.fetchall()]
                
                # Calculate progress metrics
                completed_count = len(journey['completed_steps'])
                progress_percentage = (completed_count / journey['total_steps'] * 100) if journey['total_steps'] > 0 else 0
                
                return {
                    "journey": journey,
                    "progress": {
                        "completed_steps": completed_count,
                        "total_steps": journey['total_steps'],
                        "progress_percentage": round(progress_percentage, 1),
                        "current_step": journey['current_step'],
                        "motivation_level": float(journey['motivation_level'])
                    },
                    "steps": steps,
                    "blockers": blockers,
                    "reevaluations": reevaluations,
                    "reroutes": reroutes,
                    "skills_learned": skills
                }
                
        finally:
            self.return_connection(conn)
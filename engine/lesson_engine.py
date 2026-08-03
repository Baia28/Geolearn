# The Active State. It holds the LessonSession Class
# This is what tracks the active queue, 
# reaction times, and handles adaptive mistakes.

import time
from engine.db_managers import ProgressDBManager, ContentDBManager
from engine.wave_generator import WaveGenerator

class LessonSession:
    def __init__(self, db_name="content_poolbook.db", phase_num=None, unit_num=None, lesson_num=None):
        """
        Initializes the lesson engine session. If Phase/Unit/Lesson coordinates are omitted,
        the system automatically queries progress history to load the first incomplete lesson.
        """
        self.progress_db = ProgressDBManager()
        self.content_db = ContentDBManager(db_name)
        self.generator = WaveGenerator(self.content_db, self.progress_db)

        # 1. Coordinate Discovery / Automated Routing
        if phase_num is None or unit_num is None or lesson_num is None:
            completed_ids = self.progress_db.get_completed_lesson_ids()
            resolved_id, p, u, l = self.content_db.find_next_incomplete_lesson_coordinates(completed_ids)
            self.phase_num = p
            self.unit_num = u
            self.lesson_num = l
            self.lesson_id = resolved_id
        else:
            self.phase_num = phase_num
            self.unit_num = unit_num
            self.lesson_num = lesson_num
            self.lesson_id = self.content_db.resolve_lesson_id(phase_num, unit_num, lesson_num)

        # 2. Game State Properties
        self.queue = []            
        self.total_exercises = 0   
        self.completed_count = 0
        self.card_start_time = None
        
        # 3. Assemble the learning deck
        self._build_session()

    def _build_session(self):
        """Generates the randomized, staggered micro-batched deck from the Wave Generator."""
        if self.lesson_id:
            self.queue = self.generator.build_lesson_queue(self.phase_num, self.unit_num, self.lesson_num)
            self.total_exercises = len(self.queue)
        else:
            print(f"⚠️ Cannot build lesson queue: lesson_id resolution failed.")
            self.queue = []
            self.total_exercises = 0

    def get_next_exercise(self):
        """
        Returns the active card from the top of the queue and starts 
        the high-precision stopwatch timer for response latency calculations.
        """
        if not self.queue:
            return None
        self.card_start_time = time.perf_counter()
        return self.queue[0]

    def submit_answer(self, is_correct, user_input=None):
        """
        Evaluates performance on the active card, calculates latency metrics, 
        records interaction data to user progress database, and adaptively modifies 
        the learning queue.
        """
        if not self.queue:
            return {"status": "empty", "progress": 1.0}

        # Calculate exact thinking duration in milliseconds
        elapsed_time = time.perf_counter() - (self.card_start_time or time.perf_counter())
        latency_ms = int(elapsed_time * 1000)

        # Peek at active card parameters
        active_card = self.queue[0]
        content_id = active_card.get("content_id")
        activity_type = active_card.get("activity", "unknown")
        is_review = active_card.get("is_review_item", False)

        # Sanitize text string IDs into numeric IDs for database constraints
        clean_content_id = None
        if isinstance(content_id, int):
            clean_content_id = content_id
        elif isinstance(content_id, str):
            # Parse 'pair_XX' -> XX
            if content_id.startswith("pair_"):
                try:
                    clean_content_id = int(content_id.split("_")[1])
                except (ValueError, IndexError):
                    pass
            # Parse 'diag_XX_live', 'diag_XX_rp', or 'diag_XX_comp' -> XX
            elif content_id.startswith("diag_"):
                try:
                    clean_content_id = int(content_id.split("_")[1])
                except (ValueError, IndexError):
                    pass

        # Log metrics to database (Skips purely passive study references)
        if activity_type != "dialogue_passive":
            # Optimize DB storage: Only log input strings for mistakes (to analyze errors later)
            optimized_user_input = user_input if not is_correct else None

            self.progress_db.log_user_response(
                phase_num=self.phase_num,
                unit_num=self.unit_num,
                lesson_num=self.lesson_num,
                activity_code=activity_type,
                content_id=clean_content_id,
                is_correct=is_correct,
                is_review=is_review,
                latency_ms=latency_ms,
                user_input=optimized_user_input
            )

        if is_correct:
            # 1. Sibling prune check (must handle before popping completes)
            self.handle_correct_answer(active_card)
            
            # 2. Cycle card off stack
            self.queue.pop(0)
            self.completed_count += 1
            status = "correct"

            # 3. Check for ultimate lesson completion
            if not self.queue and self.lesson_id:
                self.progress_db.mark_lesson_completed(self.lesson_id)
        else:
            status = "incorrect"
            failed_card = self.queue.pop(0)
            
            # --- ADAPTIVE CORRECTION MUTATION ENGINE ---
            # If the user struggles with an item, mutate it to its opposite reinforcement
            # mode so they approach the concept from a different cognitive angle.
            old_activity = failed_card.get("activity")
            mutated = False

            if isinstance(content_id, int):
                # Switch recognition directions
                if old_activity == "mc_geo_to_eng":
                    failed_card["activity"] = "mc_eng_to_geo"
                    distractors = self.content_db.get_distractors(self.lesson_id, content_id, limit=2)
                    failed_card["distractors"] = [d[1] for d in distractors] # Georgian text distractors
                    mutated = True
                elif old_activity == "mc_eng_to_geo":
                    failed_card["activity"] = "mc_geo_to_eng"
                    distractors = self.content_db.get_distractors(self.lesson_id, content_id, limit=2)
                    failed_card["distractors"] = [d[0] for d in distractors] # English text distractors
                    mutated = True
                
                # Switch audio identification modes
                elif old_activity == "audio_mc_to_eng":
                    failed_card["activity"] = "audio_mc_to_geo"
                    distractors = self.content_db.get_distractors(self.lesson_id, content_id, limit=2)
                    failed_card["distractors"] = [d[1] for d in distractors]
                    mutated = True
                elif old_activity == "audio_mc_to_geo":
                    failed_card["activity"] = "audio_mc_to_eng"
                    distractors = self.content_db.get_distractors(self.lesson_id, content_id, limit=2)
                    failed_card["distractors"] = [d[0] for d in distractors]
                    mutated = True
                
                # Switch active production typing / dictation
                elif old_activity == "type_georgian":
                    failed_card["activity"] = "audio_dictation"
                    mutated = True
                elif old_activity == "audio_dictation":
                    failed_card["activity"] = "type_georgian"
                    mutated = True

            if mutated:
                print(f"🔄 Adaptive Mutation: Swapped failed '{old_activity}' to equivalent '{failed_card['activity']}' for Word ID: {content_id}")

            # Re-queue the mutated card 3 slots down so it reinforces shortly, avoiding immediate repetition
            insert_index = min(3, len(self.queue))
            self.queue.insert(insert_index, failed_card)

        total = max(self.total_exercises, 1)
        return {"status": status, "progress": max(0.0, min(self.completed_count / total, 1.0))}

    def handle_correct_answer(self, completed_card):
        """
        Triggered on successful validation. Searches the active deck and surgically
        prunes sibling direction cards if adaptive mastery on the tag has been proved.
        """
        pair_tag = completed_card.get("adaptive_pair_tag")
        if not pair_tag:
            return

        # Scan deck starting at index 1 (since index 0 is currently completing)
        for idx in range(1, len(self.queue)):
            upcoming_card = self.queue[idx]
            if upcoming_card.get("adaptive_pair_tag") == pair_tag:
                pruned_card = self.queue.pop(idx)
                pruned_id = pruned_card.get("content_id")
                
                # Sibling passed without exposure: force register to SRS registry as new review item
                if isinstance(pruned_id, int):
                    self.progress_db.register_pruned_card_to_srs(pruned_id)
                
                self.total_exercises -= 1
                print(f"⚡ Adaptive Engine: Sibling tag '{pair_tag}' mastery confirmed! Pruned redundant card from position {idx}.")
                break

    def get_progress_percentage(self):
        """Calculates exact progression decimals for visual progress components."""
        if self.total_exercises == 0:
            return 0.0
        return min(self.completed_count / self.total_exercises, 1.0)
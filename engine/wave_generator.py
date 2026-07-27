# The Interleaver. It takes words from the database
# and builds the progressive sequence
# of Wave 1 -> Wave 2 -> Wave 3 exercises.

import random

class WaveGenerator:
    def __init__(self, content_db_mgr, progress_db_mgr):
        """
        Initializes the generator with isolated database managers.
        """
        self.content_db = content_db_mgr
        self.progress_db = progress_db_mgr

    def build_lesson_queue(self, phase_num, unit_num, lesson_num):
        """
        Builds a customized, highly interleaved learning deck for a lesson.
        """
        lesson_id = self.content_db.resolve_lesson_id(phase_num, unit_num, lesson_num)
        if not lesson_id:
            print(f"⚠️ Failed to resolve lesson_id for Phase {phase_num} Unit {unit_num} Lesson {lesson_num}")
            return []

        raw_steps = self.content_db.get_lesson_structure(lesson_id)
        
        # Buckets for raw components
        vocab_list = []
        convo_pairs = []
        dialogues = []
        
        # 1. Gather raw data from steps
        for step_order, comp_type, assoc_id in raw_steps:
            if comp_type == 'monologue':
                word_data = self.content_db.get_word_details(assoc_id)
                if word_data:
                    vocab_list.append((step_order, word_data))
                    
                # AUTOMATIC PAIR DETECTOR:
                # If this monologue item is ALSO a prompt in convo_pairs, grab its pair data too!
                pair_data = self.content_db.get_convo_pair_details(assoc_id)
                if pair_data:
                    convo_pairs.append((step_order, assoc_id, pair_data))

            elif comp_type == 'convo_pair':
                pair_data = self.content_db.get_convo_pair_details(assoc_id)
                if pair_data:
                    convo_pairs.append((step_order, assoc_id, pair_data))

            elif comp_type == 'dialogue':
                dialogue_data = self.content_db.get_dialogue_details(assoc_id)
                if dialogue_data:
                    dialogues.append((step_order, assoc_id, dialogue_data))

        # 2. Build the Core Vocabulary Stream using Micro-Batches
        vocab_stream = self._generate_chunked_vocab_stream(vocab_list, lesson_id)
        
        # 3. Build Conversational Cards
        convo_cards = self._generate_convo_cards(convo_pairs, lesson_id)
        print(f"🕵️ DEBUG: Successfully generated {len(convo_cards)} convo cards!")

        # 4. Build Match Matrices
        matrix_cards = self._generate_matrix_cards(vocab_list)
        
        # 5. Build Dialogue Milestone challenges
        dialogue_cards = self._generate_dialogue_cards(dialogues, lesson_id)

        # 6. Interleave and stitch core components
        # Order: Vocabs -> Conversational Pair Checks -> Matrix Grids -> Reading Dialogues
        core_learning_stream = vocab_stream + convo_cards
        
        # 7. Inject Spaced Repetition (SRS) reviews directly into the learning timeline
        final_learning_stream = self._interleave_srs_reviews(core_learning_stream)

        # Combine final timeline
        # Matrix grids and dialogues are always placed at the end as ultimate comprehension checks.
        return final_learning_stream + matrix_cards + dialogue_cards


    def _generate_chunked_vocab_stream(self, vocab_list, lesson_id):
        word_queues = {}
        
        for step_order, word_row in vocab_list:
            c_id = word_row[0]
            geo = word_row[1]
            eng = word_row[2]
            trans = word_row[3] if len(word_row) > 3 else ""
            image_src = word_row[4] if len(word_row) > 4 else None
            audio_src = word_row[5] if len(word_row) > 5 else None

            display_trans = trans if not self.progress_db.should_fade_transliteration(c_id) else None

            word_data = {
                "id": c_id, 
                "geo": geo, 
                "eng": eng, 
                "trans": display_trans,
                "image": image_src,
                "audio": audio_src
            }
            
            distractors = self.content_db.get_distractors(lesson_id, c_id, limit=2)
            cards_for_this_word = []
            
            # Long phrases
            if len(geo.split()) >= 3:
                cards_for_this_word.append({
                    "content_id": c_id,
                    "activity": "mc_geo_to_eng",
                    "target": word_data,
                    "distractors": [d[0] for d in distractors]
                })
                cards_for_this_word.append({
                    "content_id": c_id,
                    "activity": "type_georgian",
                    "target": word_data
                })
                word_queues[c_id] = cards_for_this_word
                continue

            # --- WAVE 1: Core Recognition (MIX Geo->Eng AND Eng->Geo!) ---
            chosen_rec_style = random.choice(["mc_geo_to_eng", "mc_eng_to_geo"])
            
            if chosen_rec_style == "mc_geo_to_eng":
                rec_distractors = [d[0] for d in distractors] # English options
            else:
                rec_distractors = [d[1] for d in distractors] # Georgian options

            cards_for_this_word.append({
                "content_id": c_id,
                "activity": chosen_rec_style,
                "target": word_data,
                "distractors": rec_distractors
            })

            # --- WAVE 2: Audio Training ---
            chosen_audio_style = random.choice(["audio_mc_to_eng", "audio_mc_to_geo"])
            chosen_audio_distractors = (
                [d[0] for d in distractors] if chosen_audio_style == "audio_mc_to_eng" 
                else [d[1] for d in distractors]
            )
            cards_for_this_word.append({
                "content_id": c_id,
                "activity": chosen_audio_style,
                "target": word_data,
                "distractors": chosen_audio_distractors
            })

            # --- WAVE 3: Production ---
            last_style_used = self.progress_db.get_last_production_activity_code(c_id)
            next_production_style = "type_georgian" if last_style_used == "audio_dictation" else "audio_dictation"
            cards_for_this_word.append({
                "content_id": c_id,
                "activity": next_production_style,
                "target": word_data
            })

            word_queues[c_id] = cards_for_this_word

        # Interleave batch...
        interleaved_batch = []
        last_id = None
        
        while word_queues:
            valid_ids = [cid for cid in word_queues.keys() if cid != last_id]
            chosen_id = random.choice(valid_ids) if valid_ids else list(word_queues.keys())[0]
            
            next_card = word_queues[chosen_id].pop(0)
            interleaved_batch.append(next_card)
            last_id = chosen_id
            
            if not word_queues[chosen_id]:
                del word_queues[chosen_id]

        return interleaved_batch

    def _generate_convo_cards(self, convo_pairs, lesson_id):
        """
        Builds conversational cards testing stimulus-response pairing context.
        Supports single or multiple valid responses dynamically.
        """
        cards = []
        for step_order, assoc_id, pair_data in convo_pairs:
            if not pair_data or not isinstance(pair_data, dict):
                continue

            prompt_info = pair_data.get('prompt', {})
            correct_info = pair_data.get('correct_response', {})
            distractors_list = pair_data.get('distractors', [])

            cards.append({
                "content_id": f"pair_{assoc_id}",
                "activity": "mc_geo_pair_geo",
                "target": {
                    "prompt_geo": prompt_info.get('georgian', ''),
                    "prompt_eng": prompt_info.get('english', ''),
                    "correct_geo": correct_info.get('georgian', ''),
                    "correct_eng": correct_info.get('english', '')
                },
                "distractors": [d['georgian'] for d in distractors_list],
                "all_valid_responses": pair_data.get('all_valid_responses', [])
            })

        return self._space_out_activities(cards)

    def generate_geo_pair_card(db_manager, lesson_id):
        """Assembles a UI-ready exercise dictionary for mc_geo_pair_geo."""
        target_data, distractors = db_manager.get_convo_pair_for_lesson(lesson_id, distractor_limit=3)
        
        if not target_data:
            return None

        return {
            "type": "receptive",
            "mode": "mc_geo_pair_geo",
            "target_data": target_data,
            "distractors": distractors
        }

    def _generate_matrix_cards(self, vocab_list):
        """
        Dynamically divides vocabulary words into evenly distributed matrices (2 to 5 pairs).
        """
        if not vocab_list:
            return []
            
        total_words = len(vocab_list)
        
        import math
        num_matrices = max(1, math.ceil(total_words / 5.0))
        
        base_size = total_words // num_matrices
        remainder = total_words % num_matrices
        
        sizes = []
        for i in range(num_matrices):
            size = base_size + (1 if i < remainder else 0)
            sizes.append(size)
            
        matrix_cards = []
        current_index = 0
        
        for size in sizes:
            vocab_buffer = []
            for _ in range(size):
                if current_index < total_words:
                    step_order, word_row = vocab_list[current_index]
                    # SAFE UNPACKING: Handles optional image/audio elements without crashing
                    c_id = word_row[0]
                    geo = word_row[1]
                    eng = word_row[2]
                    vocab_buffer.append({"id": c_id, "geo": geo, "eng": eng})
                    current_index += 1
                    
            if vocab_buffer:
                matrix_cards.append({
                    "content_id": "matrix_block",
                    "activity": "match_matrix_3x3",
                    "targets": vocab_buffer
                })
                
        return matrix_cards

    def _generate_dialogue_cards(self, dialogues, lesson_id):
        """
        Builds reading references and a step-by-step interactive live dialogue.
        """
        cards = []
        for step_order, assoc_id, dialogue_data in dialogues:
            dialogue_id = dialogue_data[0]
            diag_code = dialogue_data[1]
            
            lines = self.content_db.get_dialogue_lines(dialogue_id)
            
            # Step A: Passive Reading reference slide
            cards.append({
                "content_id": f"diag_{dialogue_id}",
                "activity": "dialogue_passive",
                "target": {"id": dialogue_id, "code": diag_code, "lines": lines}
            })
            
            # Step B: Live Interactive Chat Simulator
            if len(lines) >= 2:
                interactive_steps = []
                
                for idx, line in enumerate(lines):
                    speaker, geo, trans, eng = line
                    
                    if idx % 2 == 0:
                        interactive_steps.append({
                            "type": "prompt", 
                            "speaker": speaker, 
                            "text": geo
                        })
                    else:
                        distractors = self.content_db.get_convo_distractors(lesson_id, 0, limit=2)
                        interactive_steps.append({
                            "type": "choice",
                            "speaker": speaker,
                            "correct": geo,
                            "distractors": [d[0] for d in distractors]
                        })
                
                cards.append({
                    "content_id": f"diag_{dialogue_id}_live",
                    "activity": "dialogue_interactive",
                    "target": {"steps": interactive_steps}
                })
                
        return cards

    def _interleave_srs_reviews(self, core_learning_stream):
        """
        Smoothly injects up to 3 urgent SRS review cards into the learning timeline,
        ensuring they appear exactly every 3 learning steps.
        """
        urgent_ids = self.progress_db.get_urgent_review_items(limit=3)
        if not urgent_ids:
            return core_learning_stream

        final_stream = []
        active_step_counter = 0

        for card in core_learning_stream:
            final_stream.append(card)
            
            if card.get("activity") not in ["dialogue_passive"]:
                active_step_counter += 1

            if active_step_counter >= 3 and urgent_ids:
                rev_id = urgent_ids.pop(0)
                word_details = self.content_db.get_word_details(rev_id)
                if word_details:
                    # SAFE UNPACKING: Grab first 4 items regardless of tuple length
                    _, geo, eng, trans = word_details[:4]
                    final_stream.append({
                        "content_id": rev_id,
                        "activity": "type_georgian",
                        "is_review_item": True,
                        "target": {"id": rev_id, "eng": eng, "geo": geo, "trans": trans}
                    })
                active_step_counter = 0

        while urgent_ids:
            rev_id = urgent_ids.pop(0)
            word_details = self.content_db.get_word_details(rev_id)
            if word_details:
                # SAFE UNPACKING: Grab first 4 items regardless of tuple length
                _, geo, eng, trans = word_details[:4]
                final_stream.append({
                    "content_id": rev_id,
                    "activity": "type_georgian",
                    "is_review_item": True,
                    "target": {"id": rev_id, "eng": eng, "geo": geo, "trans": trans}
                })

        return final_stream

    def _space_out_activities(self, activities):
        """
        Guarantees consecutive exercises do not target the exact same content_id.
        """
        if len(activities) <= 1:
            return activities

        random.shuffle(activities)
        spaced_list = []
        leftovers = []
        
        while activities:
            card = activities.pop(0)
            card_id = card.get("content_id")
            last_id = spaced_list[-1].get("content_id") if spaced_list else None
            
            if card_id != last_id:
                spaced_list.append(card)
            else:
                found_idx = -1
                for idx, next_card in enumerate(activities):
                    if next_card.get("content_id") != last_id:
                        found_idx = idx
                        break
                
                if found_idx != -1:
                    spaced_list.append(activities.pop(found_idx))
                    activities.insert(0, card)
                else:
                    leftovers.append(card)
        
        for card in leftovers:
            card_id = card.get("content_id")
            inserted = False
            for idx in range(len(spaced_list) + 1):
                prev_id = spaced_list[idx-1].get("content_id") if idx > 0 else None
                next_id = spaced_list[idx].get("content_id") if idx < len(spaced_list) else None
                if card_id != prev_id and card_id != next_id:
                    spaced_list.insert(idx, card)
                    inserted = True
                    break
            if not inserted:
                spaced_list.append(card)
                
        return spaced_list

    def _safe_stitch_waves(self, ordered_waves):
        """
        Combines batches together sequentially while ensuring boundaries do not collide.
        """
        stitched_stream = []
        for wave in ordered_waves:
            while wave:
                card = wave.pop(0)
                if stitched_stream and stitched_stream[-1].get("content_id") == card.get("content_id"):
                    found = False
                    for i, alternate in enumerate(wave):
                        if alternate.get("content_id") != stitched_stream[-1].get("content_id"):
                            stitched_stream.append(wave.pop(i))
                            wave.insert(0, card)
                            found = True
                            break
                    if not found:
                        stitched_stream.append(card)
                else:
                    stitched_stream.append(card)
        return stitched_stream
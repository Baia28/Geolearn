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
        """
        Splits vocabulary into micro-batches of 2 or 3 words, generates Waves 1-3 
        for each batch, shuffles them locally, and stitches them together safely.
        """
        all_vocab_cards = []
        
        # Micro-batching (Chunk size of 3 is optimal for working memory)
        chunk_size = 3
        for i in range(0, len(vocab_list), chunk_size):
            chunk = vocab_list[i:i + chunk_size]
            batch_cards = []
            
            for step_order, word_row in chunk:
                c_id, geo, eng, trans = word_row
                
                # Respective fade settings
                display_trans = trans if not self.progress_db.should_fade_transliteration(c_id) else None
                word_data = {"id": c_id, "geo": geo, "eng": eng, "trans": display_trans}
                
                # Fetch standard distractors
                distractors = self.content_db.get_distractors(lesson_id, c_id, limit=2)
                
                # --- Phrase Check ---
                # If word sequence is 3+ words, skip audio/dictation, routing only to recognition & writing
                if len(eng.split()) >= 3:
                    batch_cards.append({
                        "content_id": c_id,
                        "activity": "mc_geo_to_eng",
                        "target": word_data,
                        "distractors": [d[0] for d in distractors]
                    })
                    batch_cards.append({
                        "content_id": c_id,
                        "activity": "type_georgian",
                        "target": word_data
                    })
                    continue

                # --- WAVE 1: Adaptive Recognition ---
                batch_cards.append({
                    "content_id": c_id,
                    "activity": "mc_geo_to_eng",
                    "target": word_data,
                    "distractors": [d[0] for d in distractors],
                    "adaptive_pair_tag": f"recog_sibling_{c_id}"
                })
                batch_cards.append({
                    "content_id": c_id,
                    "activity": "mc_eng_to_geo",
                    "target": word_data,
                    "distractors": [d[1] for d in distractors],
                    "adaptive_pair_tag": f"recog_sibling_{c_id}",
                    "is_conditional_backup": True
                })

                # --- WAVE 2: Audio Training ---
                chosen_audio_style = random.choice(["audio_mc_to_eng", "audio_mc_to_geo"])
                chosen_distractors = (
                    [d[0] for d in distractors] if chosen_audio_style == "audio_mc_to_eng" 
                    else [d[1] for d in distractors]
                )
                batch_cards.append({
                    "content_id": c_id,
                    "activity": chosen_audio_style,
                    "target": word_data,
                    "distractors": chosen_distractors
                })

                # --- WAVE 3: Production ---
                last_style_used = self.progress_db.get_last_production_activity_code(c_id)
                next_production_style = "type_georgian" if last_style_used == "audio_dictation" else "audio_dictation"
                
                batch_cards.append({
                    "content_id": c_id,
                    "activity": next_production_style,
                    "target": word_data
                })

            # Shuffle and space cards inside this micro-batch
            spaced_batch = self._space_out_activities(batch_cards)
            all_vocab_cards.append(spaced_batch)

        # Stitch all batches safely to prevent identical items from colliding at boundaries
        return self._safe_stitch_waves(all_vocab_cards)

    def _generate_convo_cards(self, convo_pairs, lesson_id):
        """
        Builds conversational cards testing stimulus-response pairing context.
        """
        cards = []
        for step_order, assoc_id, (p_id, r_id, p_geo, p_eng, r_geo, r_eng) in convo_pairs:
            convo_distractors = self.content_db.get_convo_distractors(lesson_id, r_id, limit=2)
            cards.append({
                "content_id": f"pair_{assoc_id}",
                "activity": "mc_geo_pair_geo",
                "target": {
                    "prompt_geo": p_geo,
                    "prompt_eng": p_eng,
                    "correct_geo": r_geo,
                    "correct_eng": r_eng
                },
                "distractors": [d[0] for d in convo_distractors]
            })
        return self._space_out_activities(cards)

    def _generate_matrix_cards(self, vocab_list):
        """
        Buffers vocabulary words into sets of 3 to output matching matrix grids.
        """
        matrix_cards = []
        vocab_buffer = []
        
        for step_order, word_row in vocab_list:
            c_id, geo, eng, trans = word_row
            vocab_buffer.append({"id": c_id, "geo": geo, "eng": eng})
            
            if len(vocab_buffer) == 3:
                matrix_cards.append({
                    "content_id": "matrix_block",
                    "activity": "match_matrix_3x3",
                    "targets": list(vocab_buffer)
                })
                vocab_buffer.clear()
                
        # Flush any remaining words (even if less than 3) into a final matrix
        if vocab_buffer:
            matrix_cards.append({
                "content_id": "matrix_block",
                "activity": "match_matrix_3x3",
                "targets": list(vocab_buffer)
            })
            
        return matrix_cards

    def _generate_dialogue_cards(self, dialogues, lesson_id):
        """
        Builds comprehensive reading references, conversational completion games, 
        and implicit vocabulary challenges around dialogues.
        """
        cards = []
        for step_order, assoc_id, dialogue_data in dialogues:
            dialogue_id = dialogue_data[0]
            diag_code = dialogue_data[1]
            
            # Step A: Passive Reading reference slide
            cards.append({
                "content_id": f"diag_{dialogue_id}",
                "activity": "dialogue_passive",
                "target": {"id": dialogue_id, "code": diag_code}
            })
            
            lines = self.content_db.get_dialogue_lines(dialogue_id)
            if len(lines) >= 2:
                # Step B: Roleplay Conversational completion (Hide final dialogue response)
                last_line = lines[-1]
                speaker, geo, trans, eng = last_line
                roleplay_distractors = self.content_db.get_convo_distractors(lesson_id, 0, limit=2)
                
                cards.append({
                    "content_id": f"diag_{dialogue_id}_rp",
                    "activity": "dialogue_roleplay_mc",
                    "target": {
                        "speaker": speaker,
                        "correct_geo": geo,
                        "context_eng": eng
                    },
                    "distractors": [d[0] for d in roleplay_distractors]
                })
                
                # Step C: Dialogue Context translation question
                random_line = random.choice(lines)
                _, context_geo, _, context_eng = random_line
                
                # Grab standard global distractors for meaning context
                fallback_distractors = self.content_db.get_distractors(lesson_id, 0, limit=2)
                cards.append({
                    "content_id": f"diag_{dialogue_id}_comp",
                    "activity": "dialogue_context_mc",
                    "target": {
                        "quote_geo": context_geo,
                        "correct_eng": context_eng
                    },
                    "distractors": [d[0] for d in fallback_distractors]
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
            
            # Count active learning card exposures
            if card.get("activity") not in ["dialogue_passive"]:
                active_step_counter += 1

            # Inject a review card every 3 successful iterations
            if active_step_counter >= 3 and urgent_ids:
                rev_id = urgent_ids.pop(0)
                word_details = self.content_db.get_word_details(rev_id)
                if word_details:
                    _, geo, eng, trans = word_details
                    final_stream.append({
                        "content_id": rev_id,
                        "activity": "type_georgian",
                        "is_review_item": True,
                        "target": {"id": rev_id, "eng": eng, "geo": geo, "trans": trans}
                    })
                active_step_counter = 0

        # Backfill any remaining reviews in case of ultra-short lessons
        while urgent_ids:
            rev_id = urgent_ids.pop(0)
            word_details = self.content_db.get_word_details(rev_id)
            if word_details:
                _, geo, eng, trans = word_details
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
                    # Collision detected! Swap with the first non-colliding card in this incoming batch.
                    found = False
                    for i, alternate in enumerate(wave):
                        if alternate.get("content_id") != stitched_stream[-1].get("content_id"):
                            stitched_stream.append(wave.pop(i))
                            wave.insert(0, card)  # Put colliding card back in front of queue
                            found = True
                            break
                    if not found:
                        stitched_stream.append(card)
                else:
                    stitched_stream.append(card)
        return stitched_stream
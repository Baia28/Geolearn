# test_review_ENGINE.py
from engine.review_engine import ReviewSession

print("⚡ STARTING OPTIONAL PRACTICE HARNESS ⚡")
session = ReviewSession(max_items=4) # Requesting a compact 4-word session (8 exercises total)

print(f"Total exercises generated: {session.total_exercises}")

while True:
    card = session.get_next_exercise()
    if not card:
        print("\n🎉 Practice complete! All words successfully mastered.")
        break
        
    print(f"\n--- Activity: {card['activity']} ---")
    print(f"Target Word: {card['target']['geo']} ({card['target']['eng']})")
    
    ans = input("Press 'c' for correct answer simulate, 'w' for wrong answer simulate: ").strip().lower()
    is_correct = (ans == 'c')
    
    result = session.submit_answer(is_correct)
    print(f"Result Status: {result['status'].upper()} | Completion: {result['progress']*100:.1f}%")
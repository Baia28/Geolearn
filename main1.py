import winsound
import time
from data.alphabet import alphabet

def teach_letter(letter):
    info = alphabet[letter]
    example = info["example"]

    print("\n📘 Georgian Alphabet Lesson")
    print("---------------------------")
    
    # 1. Show letter
    print(f"Letter: {letter}")
    print(f"Pronunciation: {info['latin']}")
    
    # 2. Play letter sound
    print("🔊 Letter sound...")
    #print(info.keys()) #---troubleshooting
    winsound.PlaySound(info["letter_audio"], winsound.SND_FILENAME)
    time.sleep(0.5)

    # 3. Show example
    print(f"\nExample: {example['word']} — {example['meaning']}")

    # 4. Play example sound
    print("🔊 Example pronunciation...")
    winsound.PlaySound(example["audio"], winsound.SND_FILENAME)

    # 5. Show image reference (for now)
    print(f"🖼 Image file: {example['image']}")

    print("\n✅ Lesson complete!\n")

#######################################################################################

#if __name__ == "__main__":
#    teach_letter("ა")

if __name__ == "__main__":
    print(alphabet["ბ"]["latin"] )

    print("----------------------------------------")
    print("Welcome to Georgian Alphabet Trainer 🇬🇪")
    print("Available letters:")

    for letter in alphabet:
        print(letter, end="  ")

    choice = input("\n\nChoose a letter: ").strip()

    if choice in alphabet:
        teach_letter(choice)
    else:
        print("❌ Letter not found yet.")
